package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.Character

interface CharacterRepository {
    suspend fun createCharacter(character: Character)
    suspend fun getCharacterById(id: String): Character?
    suspend fun getAllCharacters(): List<Character>
    suspend fun updateCharacter(character: Character)
    suspend fun deleteCharacter(id: String)
}
