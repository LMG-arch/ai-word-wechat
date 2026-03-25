package com.ai.socialworld.data.local

import androidx.room.*
import com.ai.socialworld.data.model.Reflection
import kotlinx.coroutines.flow.Flow

/**
 * 反思DAO
 */
@Dao
interface ReflectionDao {
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(reflection: Reflection): Long
    
    @Update
    suspend fun update(reflection: Reflection)
    
    @Delete
    suspend fun delete(reflection: Reflection)
    
    @Query("SELECT * FROM reflections WHERE characterId = :characterId ORDER BY timestamp DESC")
    fun getReflectionsByCharacter(characterId: String): Flow<List<Reflection>>
    
    @Query("SELECT * FROM reflections WHERE characterId = :characterId ORDER BY timestamp DESC")
    suspend fun getReflectionsByCharacterSync(characterId: String): List<Reflection>
    
    @Query("SELECT * FROM reflections WHERE taskId = :taskId ORDER BY timestamp DESC")
    suspend fun getReflectionsByTask(taskId: String): List<Reflection>
    
    @Query("SELECT * FROM reflections WHERE id = :reflectionId")
    suspend fun getById(reflectionId: String): Reflection?
    
    @Query("SELECT * FROM reflections WHERE characterId = :characterId ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getRecentReflections(characterId: String, limit: Int): List<Reflection>
    
    @Query("SELECT * FROM reflections WHERE characterId = :characterId AND success = :success ORDER BY timestamp DESC")
    suspend fun getReflectionsByResult(characterId: String, success: Boolean): List<Reflection>
    
    @Query("SELECT * FROM reflections WHERE characterId = :characterId AND importance >= :minImportance ORDER BY timestamp DESC")
    suspend fun getImportantReflections(characterId: String, minImportance: Float = 0.8f): List<Reflection>
    
    @Query("SELECT COUNT(*) FROM reflections WHERE characterId = :characterId")
    suspend fun getReflectionCount(characterId: String): Int
    
    @Query("DELETE FROM reflections WHERE id = :reflectionId")
    suspend fun deleteById(reflectionId: String)
    
    @Query("DELETE FROM reflections WHERE characterId = :characterId")
    suspend fun deleteAllByCharacter(characterId: String)
}
