package com.ai.socialworld.data.repository

import com.ai.socialworld.data.local.CharacterDao
import com.ai.socialworld.data.model.Character
import com.ai.socialworld.domain.repository.CharacterRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Character 仓库实现
 */
@Singleton
class CharacterRepositoryImpl @Inject constructor(
    private val characterDao: CharacterDao
) : CharacterRepository {

    override fun getAllCharacters(): Flow<List<Character>> =
        characterDao.getAllCharacters()

    override suspend fun getAllCharactersSync(): List<Character> =
        characterDao.getAllCharactersSync()

    override suspend fun getCharacterById(id: Long): Character? =
        characterDao.getCharacterById(id)

    override suspend fun getCharacterByName(name: String): Character? =
        characterDao.getCharacterByName(name)

    override suspend fun insertCharacter(character: Character): Long =
        characterDao.insertCharacter(character)

    override suspend fun updateCharacter(character: Character) =
        characterDao.updateCharacter(character)

    override suspend fun deleteCharacter(character: Character) =
        characterDao.deleteCharacter(character)

    override suspend fun softDeleteCharacter(id: Long) =
        characterDao.softDeleteCharacter(id)

    override suspend fun getCharacterCount(): Int =
        characterDao.getCharacterCount()
    
    override suspend fun updateCharacterMoney(id: Long, amount: Int) =
        characterDao.updateMoney(id, amount)
}
