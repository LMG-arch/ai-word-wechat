package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.data.model.Neo4jRelationship
import com.ai.socialworld.data.repository.MemoryRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 记忆服务实现
 */
@Singleton
class MemoryServiceImpl @Inject constructor(
    private val memoryRepository: MemoryRepository,
    private val timeDecayService: TimeDecayService
) : MemoryService {

    override suspend fun createMemory(memory: Memory): Result<Memory> = withContext(Dispatchers.IO) {
        memoryRepository.createMemory(memory)
    }

    override suspend fun getMemoryById(id: String): Result<Memory?> = withContext(Dispatchers.IO) {
        memoryRepository.getMemoryById(id)
    }

    override suspend fun updateMemory(memory: Memory): Result<Memory> = withContext(Dispatchers.IO) {
        memoryRepository.updateMemory(memory)
    }

    override suspend fun deleteMemory(id: String): Result<Unit> = withContext(Dispatchers.IO) {
        memoryRepository.deleteMemory(id)
    }

    override suspend fun linkToCharacter(characterId: Long, memoryId: String, relationship: Neo4jRelationship): Result<Unit> =
        withContext(Dispatchers.IO) {
            memoryRepository.linkToCharacter(characterId, memoryId, relationship)
        }

    override suspend fun accessMemory(id: String): Result<Memory> = withContext(Dispatchers.IO) {
        getMemoryById(id).mapCatching { memory ->
            memory?.let {
                val updated = it.copy(
                    accessCount = it.accessCount + 1,
                    lastAccessedAt = Instant.now()
                )
                updateMemory(updated).getOrThrow()
            } ?: throw IllegalStateException("Memory not found: $id")
        }
    }
}
