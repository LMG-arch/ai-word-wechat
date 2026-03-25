package com.ai.socialworld.data.repository

import com.ai.socialworld.data.local.*
import com.ai.socialworld.data.model.*
import com.ai.socialworld.domain.repository.MemoryRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 记忆仓库实现
 */
@Singleton
class MemoryRepositoryImpl @Inject constructor(
    private val memoryDao: MemoryDao,
    private val reflectionDao: ReflectionDao
) : MemoryRepository {
    
    // ==================== 记忆相关 ====================
    
    override suspend fun insertMemory(memory: Memory): Long {
        return memoryDao.insert(memory)
    }
    
    override fun getMemoriesByCharacter(characterId: String): Flow<List<Memory>> {
        return memoryDao.getMemoriesByCharacter(characterId)
    }
    
    override suspend fun getMemoriesByCharacterSync(characterId: String): List<Memory> {
        return memoryDao.getMemoriesByCharacterSync(characterId)
    }
    
    override fun getMemoriesByType(characterId: String, type: MemoryType): Flow<List<Memory>> {
        return memoryDao.getMemoriesByType(characterId, type)
    }
    
    override suspend fun getMemoriesByTypeSync(characterId: String, type: MemoryType): List<Memory> {
        return memoryDao.getMemoriesByTypeSync(characterId, type)
    }
    
    override suspend fun getMemoriesForRetrieval(
        characterId: String,
        limit: Int,
        types: List<MemoryType>?,
        since: Long?
    ): List<Memory> {
        return memoryDao.getMemoriesForRetrieval(characterId, limit, types, since)
    }
    
    override suspend fun getMemoryById(memoryId: String): Memory? {
        return memoryDao.getMemoryById(memoryId)
    }
    
    override suspend fun deleteMemoryById(memoryId: String) {
        memoryDao.deleteById(memoryId)
    }
    
    override suspend fun updateMemoryImportance(memoryId: String, importance: Float) {
        memoryDao.updateImportance(memoryId, importance)
    }
    
    override suspend fun searchMemoriesByContent(
        characterId: String,
        keyword: String,
        limit: Int
    ): List<Memory> {
        return memoryDao.searchByContent(characterId, keyword, limit)
    }
    
    // ==================== 反思相关 ====================
    
    override suspend fun insertReflection(reflection: Reflection): Long {
        return reflectionDao.insert(reflection)
    }
    
    override fun getReflectionsByCharacter(characterId: String): Flow<List<Reflection>> {
        return reflectionDao.getReflectionsByCharacter(characterId)
    }
    
    override suspend fun getReflectionsByTask(taskId: String): List<Reflection> {
        return reflectionDao.getReflectionsByTask(taskId)
    }
    
    override suspend fun getReflectionById(reflectionId: String): Reflection? {
        return reflectionDao.getById(reflectionId)
    }
    
    override suspend fun getRecentReflections(characterId: String, limit: Int): List<Reflection> {
        return reflectionDao.getRecentReflections(characterId, limit)
    }
}
