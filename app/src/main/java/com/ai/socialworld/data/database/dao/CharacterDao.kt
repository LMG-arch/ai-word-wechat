package com.ai.socialworld.data.database.dao

import androidx.room.*
import com.ai.socialworld.data.model.Character
import kotlinx.coroutines.flow.Flow

/**
 * Character 数据访问对象
 */
@Dao
interface CharacterDao {
    @Query("SELECT * FROM characters WHERE isDeleted = 0")
    fun getAllCharacters(): Flow<List<Character>>

    @Query("SELECT * FROM characters WHERE id = :id")
    suspend fun getCharacterById(id: Long): Character?

    @Query("SELECT * FROM characters WHERE name LIKE :name LIMIT 1")
    suspend fun getCharacterByName(name: String): Character?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCharacter(character: Character): Long

    @Update
    suspend fun updateCharacter(character: Character)

    @Delete
    suspend fun deleteCharacter(character: Character)

    @Query("UPDATE characters SET isDeleted = 1 WHERE id = :id")
    suspend fun softDeleteCharacter(id: Long)

    @Query("SELECT COUNT(*) FROM characters")
    suspend fun getCharacterCount(): Int
}
