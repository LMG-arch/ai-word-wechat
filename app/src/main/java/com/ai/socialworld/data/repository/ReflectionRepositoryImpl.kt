package com.ai.socialworld.data.repository

import com.ai.socialworld.data.local.ReflectionDao
import com.ai.socialworld.data.model.Reflection
import com.ai.socialworld.domain.repository.ReflectionRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 反思仓库实现
 */
@Singleton
class ReflectionRepositoryImpl @Inject constructor(
    private val reflectionDao: ReflectionDao
) : ReflectionRepository {
    
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
