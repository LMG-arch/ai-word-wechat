package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.Character
import kotlinx.coroutines.flow.Flow

/**
 * Character 仓库接口
 */
interface CharacterRepository {
    fun getAllCharacters(): Flow<List<Character>>
    suspend fun getAllCharactersSync(): List<Character>
    suspend fun getCharacterById(id: Long): Character?
    suspend fun getCharacterByName(name: String): Character?
    suspend fun insertCharacter(character: Character): Long
    suspend fun updateCharacter(character: Character)
    suspend fun deleteCharacter(character: Character)
    suspend fun softDeleteCharacter(id: Long)
    suspend fun getCharacterCount(): Int
    suspend fun updateCharacterMoney(id: Long, amount: Int)
}
