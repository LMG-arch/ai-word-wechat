package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.Reflection
import kotlinx.coroutines.flow.Flow

/**
 * 反思仓库接口
 */
interface ReflectionRepository {
    
    /**
     * 插入反思
     */
    suspend fun insertReflection(reflection: Reflection): Long
    
    /**
     * 获取角色的反思列表
     */
    fun getReflectionsByCharacter(characterId: String): Flow<List<Reflection>>
    
    /**
     * 获取任务相关的反思
     */
    suspend fun getReflectionsByTask(taskId: String): List<Reflection>
    
    /**
     * 根据ID获取反思
     */
    suspend fun getReflectionById(reflectionId: String): Reflection?
    
    /**
     * 获取最近N条反思
     */
    suspend fun getRecentReflections(characterId: String, limit: Int = 5): List<Reflection>
}
