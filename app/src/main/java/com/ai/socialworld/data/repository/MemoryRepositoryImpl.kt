package com.ai.socialworld.data.repository

import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.domain.repository.MemoryRepository

class MemoryRepositoryImpl : MemoryRepository {
    private val memories = mutableMapOf<String, Memory>()

    override suspend fun saveMemory(memory: Memory): Result<Unit> {
        return try {
            memories[memory.id] = memory
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getMemoryById(id: String): Result<Memory> {
        return memories[id]?.let { Result.success(it) }
            ?: Result.failure(NoSuchElementException("Memory not found: $id"))
    }

    override suspend fun getMemoriesByCharacterId(characterId: String): Result<List<Memory>> {
        return Result.success(
            memories.values.filter { it.characterId == characterId }
        )
    }

    override suspend fun deleteMemory(id: String): Result<Unit> {
        return if (memories.remove(id) != null) {
            Result.success(Unit)
        } else {
            Result.failure(NoSuchElementException("Memory not found: $id"))
        }
    }
}
