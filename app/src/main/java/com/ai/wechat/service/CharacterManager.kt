package com.ai.wechat.service

import com.ai.wechat.data.memory.MemoryEngine
import com.ai.wechat.data.memory.RelationshipType
import com.ai.wechat.data.model.*
import com.ai.wechat.db.dao.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.time.Instant
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 角色管理器
 * 负责角色的创建、生命周期管理、自主更新
 */
@Singleton
class CharacterManager @Inject constructor(
    private val characterDao: CharacterDao,
    private val memoryEngine: MemoryEngine,
    private val aiWeChatService: AiWeChatService,
    private val companyDao: CompanyDao
) {

    /**
     * 创建角色
     */
    suspend fun createCharacter(request: CreateCharacterRequest): Result<Character> =
        withContext(Dispatchers.IO) {
            try {
                val characterId = UUID.randomUUID().toString()
                val now = System.currentTimeMillis()

                // 生成头像
                val initialCharacter = Character(
                    id = characterId,
                    name = request.name,
                    age = request.age,
                    gender = request.gender,
                    occupation = request.occupation,
                    personality = request.personality,
                    avatarUrl = null,
                    signature = null,
                    money = 50.0,
                    currentLocationId = null,
                    companyId = null,
                    createdAt = now,
                    updatedAt = now
                )

                // 调用 AI 生成头像
                val avatarResult = aiWeChatService.generateAvatar(initialCharacter)
                val avatarUrl = avatarResult.getOrNull()

                val character = initialCharacter.copy(
                    avatarUrl = avatarUrl,
                    updatedAt = now
                )

                // 存储角色
                characterDao.insertCharacter(character)

                // 存储创建记忆
                memoryEngine.storeMemory(
                    characterId = characterId,
                    content = "角色${character.name}被创建，年龄${character.age}岁，职业是${character.occupation}",
                    type = MemoryType.EVENT,
                    importance = 1.0f,
                    relatedEntities = emptyList(),
                    metadata = mapOf("eventType" to "creation")
                )

                Result.success(character)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }

    /**
     * 年龄增长检测（每日定时任务）
     */
    suspend fun checkAgeGrowth(timeSpeed: Int = 1) = withContext(Dispatchers.IO) {
        val characters = characterDao.getAllCharacters().firstOrNull() ?: return@withContext

        characters.forEach { character ->
            if (!character.isAlive) return@forEach

            // 根据时间倍速计算年龄增长
            // 30 倍速下，现实 1 天=角色增长 1 个月
            val monthsToAdd = timeSpeed / 30.0
            if (monthsToAdd >= 1.0) {
                val newAge = character.age + monthsToAdd.toInt()
                if (newAge > character.age) {
                    characterDao.updateAge(character.id, newAge, System.currentTimeMillis())

                    // 检查年龄段跨越，强制更新头像
                    if (character.getAgeStage() != getAgeStage(newAge)) {
                        maybeUpdateAvatar(character.id)
                    }

                    // 记录年龄增长事件
                    memoryEngine.storeMemory(
                        characterId = character.id,
                        content = "${character.name}年龄增长到${newAge}岁",
                        type = MemoryType.EVENT,
                        importance = 0.5f
                    )
                }
            }
        }
    }

    /**
     * 自主头像更新
     */
    suspend fun maybeUpdateAvatar(characterId: String) = withContext(Dispatchers.IO) {
        val character = characterDao.getCharacterById(characterId) ?: return@withContext

        val now = System.currentTimeMillis()
        val oneWeekMillis = 7 * 24 * 60 * 60 * 1000L

        // 检查更换频率（每周最多 2 次，但年龄段跨越除外）
        if (now - character.lastAvatarChangeTime < oneWeekMillis / 2) {
            return@withContext // 距离上次更换不到一周
        }

        // 根据心情、重大事件决定是否更换
        val shouldUpdate = character.mood != "normal" ||
                character.companyId != null // 有工作等

        if (shouldUpdate) {
            val avatarResult = aiWeChatService.generateAvatar(character)
            avatarResult.onSuccess { newAvatarUrl ->
                characterDao.updateAvatar(characterId, newAvatarUrl, now)
            }
        }
    }

    /**
     * 自主签名更新
     */
    suspend fun maybeUpdateSignature(characterId: String) = withContext(Dispatchers.IO) {
        val character = characterDao.getCharacterById(characterId) ?: return@withContext

        val now = System.currentTimeMillis()
        val oneWeekMillis = 7 * 24 * 60 * 60 * 1000L

        // 检查更换频率（每周最多 2 次）
        if (now - character.lastSignatureChangeTime < oneWeekMillis / 2) {
            return@withContext
        }

        // 根据状态生成新签名
        val prompt = """
        为以下角色生成一个个性签名（20 字以内）：
        姓名：${character.name}
        年龄：${character.age}岁
        职业：${character.occupation}
        性格：${character.personality}
        当前心情：${character.mood}
        资金：${character.money}
        
        签名风格应符合人设，反映当前状态。
        """.trimIndent()

        aiWeChatService.generateText(prompt).onSuccess { signature ->
            characterDao.updateSignature(characterId, signature, now)
        }
    }

    /**
     * 破产检测
     */
    suspend fun checkBankruptcy(characterId: String) = withContext(Dispatchers.IO) {
        val character = characterDao.getCharacterById(characterId) ?: return@withContext

        if (character.money <= 0) {
            // 进入贫困状态
            memoryEngine.storeMemory(
                characterId = characterId,
                content = "${character.name}资金归零，陷入贫困",
                type = MemoryType.EVENT,
                importance = 0.8f,
                metadata = mapOf("eventType" to "bankruptcy")
            )
        }
    }

    /**
     * 死亡检测
     */
    suspend fun checkDeath(characterId: String, enableDeathMechanism: Boolean = false) =
        withContext(Dispatchers.IO) {
            if (!enableDeathMechanism) return@withContext

            val character = characterDao.getCharacterById(characterId) ?: return@withContext

            // 自然死亡检测（寿命上限 80-100 岁）
            val maxAge = (80..100).random()
            if (character.age >= maxAge) {
                characterDao.markAsDead(characterId, System.currentTimeMillis())
                
                memoryEngine.storeMemory(
                    characterId = characterId,
                    content = "${character.name}因年老去世，享年${character.age}岁",
                    type = MemoryType.EVENT,
                    importance = 1.0f,
                    metadata = mapOf("eventType" to "death", "cause" to "natural")
                )
            }
        }

    /**
     * 获取所有角色
     */
    fun getAllCharacters(): Flow<List<Character>> = characterDao.getAllCharacters()

    /**
     * 获取角色详情
     */
    suspend fun getCharacter(id: String): Character? = characterDao.getCharacterById(id)

    /**
     * 更新角色资金
     */
    suspend fun updateMoney(characterId: String, amount: Double) {
        val character = characterDao.getCharacterById(characterId) ?: return
        characterDao.updateMoney(characterId, character.money + amount, System.currentTimeMillis())
    }

    private fun getAgeStage(age: Int): AgeStage {
        return AgeStage.values().find { age in it.minAge..it.maxAge } ?: AgeStage.YOUTH
    }
}

/**
 * 创建角色请求
 */
data class CreateCharacterRequest(
    val name: String,
    val age: Int,
    val gender: String,
    val occupation: String,
    val personality: String
)
