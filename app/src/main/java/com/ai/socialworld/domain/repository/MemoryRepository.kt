package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.data.model.MemoryType
import com.ai.socialworld.data.model.Reflection
import kotlinx.coroutines.flow.Flow

/**
 * 记忆仓库接口
 */
interface MemoryRepository {
    
    /**
     * 插入记忆
     */
    suspend fun insertMemory(memory: Memory): Long
    
    /**
     * 获取角色的所有记忆（Flow）
     */
    fun getMemoriesByCharacter(characterId: String): Flow<List<Memory>>
    
    /**
     * 获取角色的所有记忆（同步）
     */
    suspend fun getMemoriesByCharacterSync(characterId: String): List<Memory>
    
    /**
     * 获取指定类型的记忆（Flow）
     */
    fun getMemoriesByType(characterId: String, type: MemoryType): Flow<List<Memory>>
    
    /**
     * 获取指定类型的记忆（同步）
     */
    suspend fun getMemoriesByTypeSync(characterId: String, type: MemoryType): List<Memory>
    
    /**
     * 获取用于检索的记忆（带向量的）
     */
    suspend fun getMemoriesForRetrieval(
        characterId: String,
        limit: Int = 50,
        types: List<MemoryType>? = null,
        since: Long? = null
    ): List<Memory>
    
    /**
     * 根据ID获取记忆
     */
    suspend fun getMemoryById(memoryId: String): Memory?
    
    /**
     * 根据ID删除记忆
     */
    suspend fun deleteMemoryById(memoryId: String)
    
    /**
     * 更新记忆重要性
     */
    suspend fun updateMemoryImportance(memoryId: String, importance: Float)
    
    /**
     * 搜索记忆（基于内容）
     */
    suspend fun searchMemoriesByContent(
        characterId: String,
        keyword: String,
        limit: Int = 10
    ): List<Memory>
    
    // ==================== 反思相关 ====================
    
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
