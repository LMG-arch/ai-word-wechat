package com.ai.wechat.db.dao

import androidx.room.*
import com.ai.wechat.data.model.Character
import kotlinx.coroutines.flow.Flow

/**
 * 角色数据访问对象
 */
@Dao
interface CharacterDao {

    @Query("SELECT * FROM characters WHERE isAlive = 1 ORDER BY name")
    fun getAllCharacters(): Flow<List<Character>>

    @Query("SELECT * FROM characters WHERE id = :id")
    suspend fun getCharacterById(id: String): Character?

    @Query("SELECT * FROM characters WHERE id = :id")
    fun getCharacterByIdFlow(id: String): Flow<Character?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCharacter(character: Character)

    @Update
    suspend fun updateCharacter(character: Character)

    @Delete
    suspend fun deleteCharacter(character: Character)

    @Query("UPDATE characters SET money = :money, updatedAt = :updatedAt WHERE id = :id")
    suspend fun updateMoney(id: String, money: Double, updatedAt: Long)

    @Query("UPDATE characters SET age = :age, updatedAt = :updatedAt WHERE id = :id")
    suspend fun updateAge(id: String, age: Int, updatedAt: Long)

    @Query("UPDATE characters SET avatarUrl = :avatarUrl, lastAvatarChangeTime = :changeTime WHERE id = :id")
    suspend fun updateAvatar(id: String, avatarUrl: String?, changeTime: Long)

    @Query("UPDATE characters SET signature = :signature, lastSignatureChangeTime = :changeTime WHERE id = :id")
    suspend fun updateSignature(id: String, signature: String?, changeTime: Long)

    @Query("UPDATE characters SET isAlive = 0, deathTime = :deathTime WHERE id = :id")
    suspend fun markAsDead(id: String, deathTime: Long)

    @Query("SELECT * FROM characters WHERE companyId = :companyId")
    suspend fun getCharactersByCompanyId(companyId: String): List<Character>

    @Query("SELECT * FROM characters WHERE age >= :minAge AND age <= :maxAge")
    suspend fun getCharactersByAgeRange(minAge: Int, maxAge: Int): List<Character>
}
