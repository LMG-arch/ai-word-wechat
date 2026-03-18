package com.ai.socialworld.data.repository

import com.ai.socialworld.data.database.dao.CharacterDao
import com.ai.socialworld.data.model.Character
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Character 仓库接口
 */
interface CharacterRepository {
    fun getAllCharacters(): Flow<List<Character>>
    suspend fun getCharacterById(id: Long): Result<Character?>
    suspend fun getCharacterByName(name: String): Result<Character?>
    suspend fun insertCharacter(character: Character): Result<Long>
    suspend fun updateCharacter(character: Character): Result<Unit>
    suspend fun deleteCharacter(character: Character): Result<Unit>
    suspend fun softDeleteCharacter(id: Long): Result<Unit>
    suspend fun getCharacterCount(): Result<Int>
}

/**
 * Character 仓库实现
 */
@Singleton
class CharacterRepositoryImpl @Inject constructor(
    private val characterDao: CharacterDao
) : CharacterRepository {

    override fun getAllCharacters(): Flow<List<Character>> =
        characterDao.getAllCharacters()

    override suspend fun getCharacterById(id: Long): Result<Character?> =
        runCatching { characterDao.getCharacterById(id) }

    override suspend fun getCharacterByName(name: String): Result<Character?> =
        runCatching { characterDao.getCharacterByName(name) }

    override suspend fun insertCharacter(character: Character): Result<Long> =
        runCatching { characterDao.insertCharacter(character) }

    override suspend fun updateCharacter(character: Character): Result<Unit> =
        runCatching { characterDao.updateCharacter(character) }

    override suspend fun deleteCharacter(character: Character): Result<Unit> =
        runCatching { characterDao.deleteCharacter(character) }

    override suspend fun softDeleteCharacter(id: Long): Result<Unit> =
        runCatching { characterDao.softDeleteCharacter(id) }

    override suspend fun getCharacterCount(): Result<Int> =
        runCatching { characterDao.getCharacterCount() }
}
