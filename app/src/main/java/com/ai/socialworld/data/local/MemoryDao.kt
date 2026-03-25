package com.ai.socialworld.data.local

import androidx.room.*
import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.data.model.MemoryType
import kotlinx.coroutines.flow.Flow

/**
 * 记忆DAO
 */
@Dao
interface MemoryDao {
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(memory: Memory): Long
    
    @Update
    suspend fun update(memory: Memory)
    
    @Delete
    suspend fun delete(memory: Memory)
    
    @Query("SELECT * FROM memories WHERE characterId = :characterId ORDER BY timestamp DESC")
    fun getMemoriesByCharacter(characterId: String): Flow<List<Memory>>
    
    @Query("SELECT * FROM memories WHERE characterId = :characterId ORDER BY timestamp DESC")
    suspend fun getMemoriesByCharacterSync(characterId: String): List<Memory>
    
    @Query("SELECT * FROM memories WHERE characterId = :characterId AND type = :type ORDER BY timestamp DESC")
    fun getMemoriesByType(characterId: String, type: MemoryType): Flow<List<Memory>>
    
    @Query("SELECT * FROM memories WHERE characterId = :characterId AND type = :type ORDER BY timestamp DESC")
    suspend fun getMemoriesByTypeSync(characterId: String, type: MemoryType): List<Memory>
    
    @Query("""
        SELECT * FROM memories 
        WHERE characterId = :characterId 
        AND embedding IS NOT NULL 
        AND (:types IS NULL OR type IN (:types))
        AND (:since IS NULL OR timestamp >= :since)
        ORDER BY timestamp DESC 
        LIMIT :limit
    """)
    suspend fun getMemoriesForRetrieval(
        characterId: String,
        limit: Int,
        types: List<MemoryType>?,
        since: Long?
    ): List<Memory>
    
    @Query("SELECT * FROM memories WHERE id = :memoryId")
    suspend fun getMemoryById(memoryId: String): Memory?
    
    @Query("DELETE FROM memories WHERE id = :memoryId")
    suspend fun deleteById(memoryId: String)
    
    @Query("UPDATE memories SET importance = :importance WHERE id = :memoryId")
    suspend fun updateImportance(memoryId: String, importance: Float)
    
    @Query("""
        SELECT * FROM memories 
        WHERE characterId = :characterId 
        AND content LIKE '%' || :keyword || '%'
        ORDER BY timestamp DESC 
        LIMIT :limit
    """)
    suspend fun searchByContent(
        characterId: String,
        keyword: String,
        limit: Int
    ): List<Memory>
    
    @Query("SELECT * FROM memories WHERE characterId = :characterId AND importance >= :minImportance ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getImportantMemories(
        characterId: String,
        minImportance: Float = 0.7f,
        limit: Int = 10
    ): List<Memory>
    
    @Query("SELECT COUNT(*) FROM memories WHERE characterId = :characterId")
    suspend fun getMemoryCount(characterId: String): Int
    
    @Query("DELETE FROM memories WHERE characterId = :characterId")
    suspend fun deleteAllByCharacter(characterId: String)
}
