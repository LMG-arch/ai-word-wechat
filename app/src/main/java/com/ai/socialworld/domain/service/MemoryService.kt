package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.data.model.Neo4jRelationship

/**
 * 记忆服务接口
 */
interface MemoryService {
    suspend fun createMemory(memory: Memory): Result<Memory>
    suspend fun getMemoryById(id: String): Result<Memory?>
    suspend fun updateMemory(memory: Memory): Result<Memory>
    suspend fun deleteMemory(id: String): Result<Unit>
    suspend fun linkToCharacter(characterId: Long, memoryId: String, relationship: Neo4jRelationship): Result<Unit>
    suspend fun accessMemory(id: String): Result<Memory>
}
