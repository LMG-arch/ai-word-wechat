package com.ai.socialworld.data.database.dao

import androidx.room.*
import com.ai.socialworld.data.model.Character
import com.ai.socialworld.data.model.Gender
import com.ai.socialworld.data.model.GrowthStage
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

    @Query("SELECT * FROM characters WHERE name = :name LIMIT 1")
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
    
    @Query("SELECT * FROM characters WHERE gender = :gender AND isDeleted = 0")
    fun getCharactersByGender(gender: Gender): Flow<List<Character>>
    
    @Query("SELECT * FROM characters WHERE growthStage = :stage AND isDeleted = 0")
    fun getCharactersByGrowthStage(stage: GrowthStage): Flow<List<Character>>
    
    @Query("SELECT * FROM characters WHERE isAlive = 1 AND isDeleted = 0")
    fun getLivingCharacters(): Flow<List<Character>>
    
    @Query("SELECT * FROM characters WHERE money <= 0 AND isAlive = 1 AND isDeleted = 0")
    fun getBankruptCharacters(): Flow<List<Character>>
    
    @Query("UPDATE characters SET money = money + :amount WHERE id = :id")
    suspend fun updateMoney(id: Long, amount: Int)
    
    @Query("UPDATE characters SET age = :age, growthStage = :stage WHERE id = :id")
    suspend fun updateAge(id: Long, age: Int, stage: GrowthStage)
    
    @Query("UPDATE characters SET avatarUrl = :url, lastAvatarUpdate = :time, avatarUpdateCount = avatarUpdateCount + 1 WHERE id = :id")
    suspend fun updateAvatar(id: Long, url: String, time: Long)
    
    @Query("UPDATE characters SET signature = :signature, lastSignatureUpdate = :time, signatureUpdateCount = signatureUpdateCount + 1 WHERE id = :id")
    suspend fun updateSignature(id: Long, signature: String, time: Long)
    
    @Query("UPDATE characters SET avatarUpdateCount = 0, signatureUpdateCount = 0")
    suspend fun resetWeeklyUpdateCount()
}
