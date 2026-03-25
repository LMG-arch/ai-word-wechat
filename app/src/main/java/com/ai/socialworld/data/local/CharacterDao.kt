package com.ai.socialworld.data.local

import androidx.room.*
import com.ai.socialworld.data.model.Character
import kotlinx.coroutines.flow.Flow

/**
 * 角色DAO
 */
@Dao
interface CharacterDao {
    
    @Query("SELECT * FROM characters WHERE isDeleted = 0 ORDER BY name ASC")
    fun getAllCharacters(): Flow<List<Character>>
    
    @Query("SELECT * FROM characters WHERE isDeleted = 0 ORDER BY name ASC")
    suspend fun getAllCharactersSync(): List<Character>
    
    @Query("SELECT * FROM characters WHERE id = :id")
    suspend fun getCharacterById(id: Long): Character?
    
    @Query("SELECT * FROM characters WHERE name = :name AND isDeleted = 0 LIMIT 1")
    suspend fun getCharacterByName(name: String): Character?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCharacter(character: Character): Long
    
    @Update
    suspend fun updateCharacter(character: Character)
    
    @Delete
    suspend fun deleteCharacter(character: Character)
    
    @Query("UPDATE characters SET isDeleted = 1 WHERE id = :id")
    suspend fun softDeleteCharacter(id: Long)
    
    @Query("SELECT COUNT(*) FROM characters WHERE isDeleted = 0")
    suspend fun getCharacterCount(): Int
    
    @Query("UPDATE characters SET money = money + :amount WHERE id = :id")
    suspend fun updateMoney(id: Long, amount: Int)
    
    @Query("SELECT * FROM characters WHERE age >= :minAge AND age <= :maxAge AND isDeleted = 0")
    suspend fun getCharactersByAgeRange(minAge: Int, maxAge: Int): List<Character>
    
    @Query("SELECT * FROM characters WHERE occupation LIKE '%' || :keyword || '%' AND isDeleted = 0")
    suspend fun getCharactersByOccupation(keyword: String): List<Character>
    
    @Query("UPDATE characters SET avatarUrl = :avatarUrl WHERE id = :id")
    suspend fun updateAvatar(id: Long, avatarUrl: String)
    
    @Query("UPDATE characters SET signature = :signature WHERE id = :id")
    suspend fun updateSignature(id: Long, signature: String)
    
    @Query("UPDATE characters SET age = age + 1 WHERE id = :id")
    suspend fun incrementAge(id: Long)
}
