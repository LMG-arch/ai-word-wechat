package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.Memory

interface MemoryRepository {
    suspend fun saveMemory(memory: Memory): Result<Unit>
    suspend fun getMemoryById(id: String): Result<Memory>
    suspend fun getMemoriesByCharacterId(characterId: String): Result<List<Memory>>
    suspend fun deleteMemory(id: String): Result<Unit>
}
