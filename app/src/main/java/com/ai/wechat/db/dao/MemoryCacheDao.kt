package com.ai.wechat.db.dao

import androidx.room.*
import com.ai.wechat.data.model.MemoryCache
import com.ai.wechat.data.model.MemoryType
import kotlinx.coroutines.flow.Flow

/**
 * 记忆缓存数据访问对象
 */
@Dao
interface MemoryCacheDao {

    @Query("SELECT * FROM memory_cache WHERE characterId = :characterId ORDER BY timestamp DESC")
    fun getMemoriesByCharacter(characterId: String): Flow<List<MemoryCache>>

    @Query("SELECT * FROM memory_cache WHERE characterId = :characterId AND type = :type ORDER BY timestamp DESC")
    fun getMemoriesByType(characterId: String, type: MemoryType): Flow<List<MemoryCache>>

    @Query("SELECT * FROM memory_cache WHERE id = :id")
    suspend fun getMemoryById(id: String): MemoryCache?

    @Query("SELECT * FROM memory_cache WHERE characterId = :characterId AND timestamp BETWEEN :startTime AND :endTime ORDER BY timestamp DESC")
    suspend fun getMemoriesByTimeRange(characterId: String, startTime: Long, endTime: Long): List<MemoryCache>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMemory(memory: MemoryCache)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMemories(memories: List<MemoryCache>)

    @Update
    suspend fun updateMemory(memory: MemoryCache)

    @Delete
    suspend fun deleteMemory(memory: MemoryCache)

    @Query("DELETE FROM memory_cache WHERE characterId = :characterId")
    suspend fun deleteAllMemories(characterId: String)

    @Query("DELETE FROM memory_cache WHERE cachedAt < :expireTime")
    suspend fun deleteExpiredMemories(expireTime: Long)
}
