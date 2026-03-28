package com.ai.wechat.data.memory.impl

import com.ai.wechat.data.memory.*
import com.ai.wechat.db.dao.MemoryCacheDao
import com.ai.wechat.network.AiService
import com.ai.wechat.network.EmbedData
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.neo4j.driver.*
import java.time.Instant
import java.time.temporal.ChronoUnit
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.exp

/**
 * Graphiti 记忆引擎实现
 * 基于 Neo4j 图数据库实现时间感知记忆存储
 */
@Singleton
class GraphitiMemoryEngine @Inject constructor(
    private val neo4jDriver: Driver,
    private val memoryCacheDao: MemoryCacheDao,
    private val aiService: AiService,
    private val gson: Gson
) : MemoryEngine {

    companion object {
        private const val TIME_DECAY_HALF_LIFE = 72.0 // 小时
        private const val REFLECTION_HALF_LIFE = 168.0 // 小时（7 天）
    }

    override suspend fun storeMemory(
        characterId: String,
        content: String,
        type: MemoryType,
        importance: Float,
        relatedEntities: List<String>,
        metadata: Map<String, Any>
    ): Memory = withContext(Dispatchers.IO) {
        val now = Instant.now()
        val memoryId = UUID.randomUUID().toString()
        
        // 生成向量嵌入
        val embedding = try {
            aiService.embed(content).getOrNull()
        } catch (e: Exception) {
            null
        }

        // 存储到 Neo4j
        neo4jDriver.session { session ->
            session.executeWrite { tx ->
                val embeddingStr = embedding?.joinToString(",") { it.toString() }
                
                tx.run(
                    """
                    CREATE (m:Memory {
                        id: \$id,
                        characterId: \$characterId,
                        content: \$content,
                        type: \$type,
                        importance: \$importance,
                        timestamp: datetime(\$timestamp),
                        valid_from: datetime(\$validFrom),
                        valid_to: null,
                        emotion: \$emotion,
                        relatedEntities: \$relatedEntities,
                        embedding: \$embedding,
                        metadata: \$metadata
                    })
                    """.trimIndent(),
                    Parameters.map(
                        "id", memoryId,
                        "characterId", characterId,
                        "content", content,
                        "type", type.name,
                        "importance", importance.toDouble(),
                        "timestamp", now.toString(),
                        "validFrom", now.toString(),
                        "emotion", metadata["emotion"] as? String,
                        "relatedEntities", relatedEntities,
                        "embedding", embeddingStr,
                        "metadata", gson.toJson(metadata)
                    )
                )
            }
        }

        // 缓存到本地
        val memory = Memory(
            id = memoryId,
            characterId = characterId,
            content = content,
            type = type,
            importance = importance,
            emotion = metadata["emotion"] as? String,
            timestamp = now.toEpochMilli(),
            validFrom = now,
            validTo = null,
            relatedEntities = relatedEntities,
            embedding = embedding,
            metadata = metadata
        )

        cacheMemory(memory)
        memory
    }

    override suspend fun recallMemories(
        characterId: String,
        query: String,
        timeRange: TimeRange?,
        topK: Int
    ): List<Memory> = withContext(Dispatchers.IO) {
        // 1. 生成查询向量
        val queryEmbedding = aiService.embed(query).getOrNull()
            ?: return@withContext emptyList()

        // 2. 向量检索 Top 50
        val candidates = searchVector(characterId, queryEmbedding, 50)

        // 3. 时间范围过滤
        val filtered = if (timeRange != null) {
            candidates.filter { memory ->
                memory.timestamp >= timeRange.startTime.toEpochMilli() &&
                memory.timestamp <= timeRange.endTime.toEpochMilli()
            }
        } else {
            candidates
        }

        // 4. 时间衰减加权
        val timeWeighted = filtered.map { memory ->
            val hoursDiff = ChronoUnit.HOURS.between(memory.validFrom, Instant.now())
            val isReflection = memory.type == MemoryType.REFLECTION
            val halfLife = if (isReflection) REFLECTION_HALF_LIFE else TIME_DECAY_HALF_LIFE
            val timeWeight = exp(-hoursDiff / halfLife)
            val combinedScore = memory.importance * timeWeight
            memory to combinedScore
        }.sortedByDescending { it.second }

        // 5. 重排模型精排
        val topCandidates = timeWeighted.take(20).map { it.first.content }
        val rerankedResults = aiService.rerank(query, topCandidates, topK).getOrNull()
            ?: return@withContext timeWeighted.take(topK).map { it.first }

        // 6. 返回重排后的记忆
        rerankedResults.mapNotNull { result ->
            timeWeighted.find { it.first.content == result.text }?.first
        }
    }

    override suspend fun searchVector(
        characterId: String,
        queryEmbedding: List<Float>,
        topK: Int
    ): List<Memory> = withContext(Dispatchers.IO) {
        // 从本地缓存检索（带向量相似度计算）
        val allMemories = memoryCacheDao.getMemoriesByCharacter(characterId)
            .firstOrNull() ?: emptyList()

        allMemories
            .filter { it.embedding != null }
            .map { memory ->
                val memoryEmbedding = parseEmbedding(memory.embedding)
                val similarity = cosineSimilarity(queryEmbedding, memoryEmbedding)
                memory to similarity
            }
            .sortedByDescending { it.second }
            .take(topK)
            .map { parseMemory(it.first) }
    }

    override suspend fun storeRelationship(
        fromId: String,
        toId: String,
        type: RelationshipType,
        properties: Map<String, Any>,
        validFrom: Instant,
        validTo: Instant?
    ) = withContext(Dispatchers.IO) {
        neo4jDriver.session { session ->
            session.executeWrite { tx ->
                // 先使旧关系失效
                tx.run(
                    """
                    MATCH (a:Character {id: \$fromId})-[r:${type.name}]->(b:Character {id: \$toId})
                    WHERE r.valid_to IS NULL
                    SET r.valid_to = datetime(\$invalidTime)
                    """.trimIndent(),
                    Parameters.map("fromId", fromId, "toId", toId, "invalidTime", validFrom.toString())
                )

                // 创建新关系
                val cypher = """
                    MATCH (a:Character {id: \$fromId}), (b:Character {id: \$toId})
                    CREATE (a)-[r:${type.name} {
                        valid_from: datetime(\$validFrom),
                        valid_to: \$validTo,
                        ${properties.keys.joinToString(", ") { "$it: \$$it" }}
                    }]->(b)
                    """.trimIndent()

                val params = mutableMapOf<String, Any>(
                    "fromId" to fromId,
                    "toId" to toId,
                    "validFrom" to validFrom.toString(),
                    "validTo" to (validTo?.toString() ?: "null")
                )
                properties.forEach { (k, v) -> params[k] = v }

                tx.run(cypher, Parameters.map(*params.flatMap { arrayOf(it.key, it.value) }.toTypedArray()))
            }
        }
    }

    override suspend fun getCurrentRelationship(
        fromId: String,
        toId: String
    ): RelationshipState? = withContext(Dispatchers.IO) {
        neo4jDriver.session { session ->
            session.executeRead { tx ->
                val result = tx.run(
                    """
                    MATCH (a:Character {id: \$fromId})-[r:FRIEND_WITH]->(b:Character {id: \$toId})
                    WHERE r.valid_to IS NULL
                    RETURN r, b.name as targetName
                    """.trimIndent(),
                    Parameters.map("fromId", fromId, "toId", toId)
                )

                if (result.hasNext()) {
                    val record = result.next()
                    val rel = record.get("r").asRelationship()
                    RelationshipState(
                        targetId = toId,
                        targetName = record.get("targetName").asString(),
                        type = RelationshipType.FRIEND_WITH,
                        intimacy = rel["intimacy"]?.asDouble() ?: 0.0,
                        validFrom = Instant.parse(rel["valid_from"]?.asString()),
                        validTo = null
                    )
                } else {
                    null
                }
            }
        }
    }

    override suspend fun getStateAtTime(
        characterId: String,
        timestamp: Instant
    ): CharacterState? = withContext(Dispatchers.IO) {
        neo4jDriver.session { session ->
            session.executeRead { tx ->
                // 查询角色在指定时间点的状态
                val result = tx.run(
                    """
                    MATCH (c:Character {id: \$characterId})
                    OPTIONAL MATCH (c)-[r:FRIEND_WITH]->(friend)
                    WHERE r.valid_from <= datetime(\$timestamp)
                      AND (r.valid_to IS NULL OR r.valid_to > datetime(\$timestamp))
                    RETURN c, collect({
                        targetId: friend.id,
                        targetName: friend.name,
                        type: 'FRIEND_WITH',
                        intimacy: r.intimacy,
                        validFrom: r.valid_from,
                        validTo: r.valid_to
                    }) as relationships
                    """.trimIndent(),
                    Parameters.map("characterId", characterId, "timestamp", timestamp.toString())
                )

                if (result.hasNext()) {
                    val record = result.next()
                    val character = record.get("c").asNode()
                    val relationships = record.get("relationships").asList { it.asMap() }
                        .map { rel ->
                            RelationshipState(
                                targetId = rel["targetId"] as String,
                                targetName = rel["targetName"] as String,
                                type = RelationshipType.FRIEND_WITH,
                                intimacy = (rel["intimacy"] as Number).toDouble(),
                                validFrom = Instant.parse(rel["validFrom"].toString()),
                                validTo = rel["validTo"]?.toString()?.let { Instant.parse(it) }
                            )
                        }

                    CharacterState(
                        id = characterId,
                        name = character["name"]?.asString() ?: "",
                        age = (character["age"]?.asInt() ?: 0),
                        money = (character["money"]?.asDouble() ?: 0.0),
                        location = character["location"]?.asString(),
                        companyId = character["companyId"]?.asString(),
                        relationships = relationships,
                        timestamp = timestamp
                    )
                } else {
                    null
                }
            }
        }
    }

    override suspend fun getStaleRelationships(days: Int): List<RelationshipState> =
        withContext(Dispatchers.IO) {
            neo4jDriver.session { session ->
                session.executeRead { tx ->
                    val result = tx.run(
                        """
                        MATCH (a:Character)-[r:FRIEND_WITH]->(b:Character)
                        WHERE r.valid_to IS NULL
                          AND datetime(r.valid_from) < datetime() - duration({days: \$days})
                        RETURN a.id as fromId, b.id as toId, b.name as targetName, r.intimacy as intimacy, r.valid_from as validFrom
                        """.trimIndent(),
                        Parameters.map("days", days)
                    )

                    result.list { record ->
                        RelationshipState(
                            targetId = record.get("toId").asString(),
                            targetName = record.get("targetName").asString(),
                            type = RelationshipType.FRIEND_WITH,
                            intimacy = record.get("intimacy").asDouble(),
                            validFrom = Instant.parse(record.get("validFrom").asString()),
                            validTo = null
                        )
                    }
                }
            }
        }

    override suspend fun invalidateRelationship(
        fromId: String,
        toId: String,
        invalidTime: Instant
    ) = withContext(Dispatchers.IO) {
        neo4jDriver.session { session ->
            session.executeWrite { tx ->
                tx.run(
                    """
                    MATCH (a:Character {id: \$fromId})-[r:FRIEND_WITH]->(b:Character {id: \$toId})
                    WHERE r.valid_to IS NULL
                    SET r.valid_to = datetime(\$invalidTime)
                    """.trimIndent(),
                    Parameters.map("fromId", fromId, "toId", toId, "invalidTime", invalidTime.toString())
                )
            }
        }
    }

    override suspend fun getRelationships(characterId: String): List<RelationshipState> =
        withContext(Dispatchers.IO) {
            neo4jDriver.session { session ->
                session.executeRead { tx ->
                    val result = tx.run(
                        """
                        MATCH (a:Character {id: \$characterId})-[r:FRIEND_WITH]->(b:Character)
                        WHERE r.valid_to IS NULL
                        RETURN b.id as targetId, b.name as targetName, r.intimacy as intimacy, r.valid_from as validFrom
                        """.trimIndent(),
                        Parameters.map("characterId", characterId)
                    )

                    result.list { record ->
                        RelationshipState(
                            targetId = record.get("targetId").asString(),
                            targetName = record.get("targetName").asString(),
                            type = RelationshipType.FRIEND_WITH,
                            intimacy = record.get("intimacy").asDouble(),
                            validFrom = Instant.parse(record.get("validFrom").asString()),
                            validTo = null
                        )
                    }
                }
            }
        }

    override suspend fun storeReflection(
        characterId: String,
        taskId: String,
        content: String,
        lessons: List<String>,
        skillDeltas: Map<String, Float>
    ): Memory = withContext(Dispatchers.IO) {
        storeMemory(
            characterId = characterId,
            content = content,
            type = MemoryType.REFLECTION,
            importance = 0.9f,
            relatedEntities = listOf(taskId),
            metadata = mapOf(
                "lessons" to lessons,
                "skillDeltas" to skillDeltas
            )
        )
    }

    override suspend fun getMemoriesByType(
        characterId: String,
        type: MemoryType,
        limit: Int
    ): List<Memory> = withContext(Dispatchers.IO) {
        memoryCacheDao.getMemoriesByType(characterId, type)
            .firstOrNull()
            ?.take(limit)
            ?.map { parseMemory(it) } ?: emptyList()
    }

    override suspend fun deleteMemory(memoryId: String) = withContext(Dispatchers.IO) {
        neo4jDriver.session { session ->
            session.executeWrite { tx ->
                tx.run(
                    "MATCH (m:Memory {id: \$id}) DETACH DELETE m",
                    Parameters.map("id", memoryId)
                )
            }
        }
        // 同时删除本地缓存
        memoryCacheDao.getMemoryById(memoryId)?.let { memory ->
            memoryCacheDao.deleteMemory(memory)
        }
    }

    override suspend fun cleanupExpiredMemories() = withContext(Dispatchers.IO) {
        val expiryTime = Instant.now().minus(30, ChronoUnit.DAYS)
        neo4jDriver.session { session ->
            session.executeWrite { tx ->
                tx.run(
                    """
                    MATCH (m:Memory)
                    WHERE m.valid_to IS NOT NULL AND datetime(m.valid_to) < datetime(\$expiryTime)
                    DETACH DELETE m
                    """.trimIndent(),
                    Parameters.map("expiryTime", expiryTime.toString())
                )
            }
        }
    }

    // 私有辅助方法

    private suspend fun cacheMemory(memory: Memory) {
        val cache = com.ai.wechat.data.model.MemoryCache(
            id = memory.id,
            characterId = memory.characterId,
            content = memory.content,
            type = memory.type,
            importance = memory.importance,
            emotion = memory.emotion,
            timestamp = memory.timestamp,
            validFrom = memory.validFrom.toEpochMilli(),
            validTo = memory.validTo?.toEpochMilli(),
            relatedEntities = gson.toJson(memory.relatedEntities),
            embedding = memory.embedding?.joinToString(",") { it.toString() },
            metadata = gson.toJson(memory.metadata)
        )
        memoryCacheDao.insertMemory(cache)
    }

    private fun parseEmbedding(embeddingStr: String?): List<Float> {
        if (embeddingStr.isNullOrBlank()) return emptyList()
        return embeddingStr.split(",").map { it.toFloat() }
    }

    private fun parseMemory(cache: com.ai.wechat.data.model.MemoryCache): Memory {
        return Memory(
            id = cache.id,
            characterId = cache.characterId,
            content = cache.content,
            type = cache.type,
            importance = cache.importance,
            emotion = cache.emotion,
            timestamp = cache.timestamp,
            validFrom = Instant.ofEpochMilli(cache.validFrom),
            validTo = cache.validTo?.let { Instant.ofEpochMilli(it) },
            relatedEntities = gson.fromJson(cache.relatedEntities, object : TypeToken<List<String>>() {}.type),
            embedding = parseEmbedding(cache.embedding),
            metadata = cache.metadata?.let { gson.fromJson(it, object : TypeToken<Map<String, Any>>() {}.type) } ?: emptyMap()
        )
    }

    private fun cosineSimilarity(a: List<Float>, b: List<Float>): Double {
        if (a.size != b.size || a.isEmpty()) return 0.0
        var dotProduct = 0.0
        var normA = 0.0
        var normB = 0.0
        for (i in a.indices) {
            dotProduct += a[i] * b[i]
            normA += a[i] * a[i]
            normB += b[i] * b[i]
        }
        return if (normA == 0.0 || normB == 0.0) 0.0 else dotProduct / (Math.sqrt(normA) * Math.sqrt(normB))
    }
}
