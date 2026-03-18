package com.ai.socialworld.data.database.dao

import androidx.room.*
import com.ai.socialworld.data.model.Character
import kotlinx.coroutines.flow.Flow

@Dao
interface CharacterDao {

    @Insert
    suspend fun insert(character: Character)

    @Update
    suspend fun update(character: Character)

    @Delete
    suspend fun delete(character: Character)

    @Query("SELECT * FROM characters WHERE id = :id")
    suspend fun getById(id: String): Character?

    @Query("SELECT * FROM characters")
    fun getAll(): Flow<List<Character>>

    @Query("SELECT * FROM characters WHERE age >= :minAge AND age <= :maxAge")
    fun getByAgeRange(minAge: Int, maxAge: Int): Flow<List<Character>>
}

}
