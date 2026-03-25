package com.ai.socialworld.data.repository

import com.ai.socialworld.data.local.SkillDao
import com.ai.socialworld.data.model.Skill
import com.ai.socialworld.data.model.SkillHistory
import com.ai.socialworld.data.model.SkillType
import com.ai.socialworld.domain.repository.SkillRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 技能仓库实现
 */
@Singleton
class SkillRepositoryImpl @Inject constructor(
    private val skillDao: SkillDao
) : SkillRepository {
    
    override suspend fun insertSkill(skill: Skill) {
        skillDao.insert(skill)
    }
    
    override suspend fun updateSkill(skill: Skill) {
        skillDao.update(skill)
    }
    
    override fun getSkillsByCharacter(characterId: String): Flow<List<Skill>> {
        return skillDao.getSkillsByCharacter(characterId)
    }
    
    override suspend fun getSkillsByCharacterSync(characterId: String): List<Skill> {
        return skillDao.getSkillsByCharacterSync(characterId)
    }
    
    override suspend fun getSkillSync(characterId: String, skillType: SkillType): Skill? {
        return skillDao.getSkill(characterId, skillType)
    }
    
    override fun getSkillHistory(characterId: String): Flow<List<SkillHistory>> {
        return skillDao.getSkillHistory(characterId)
    }
    
    override suspend fun insertSkillHistory(history: SkillHistory) {
        skillDao.insertSkillHistory(history)
    }
    
    override suspend fun getSkillTrend(
        characterId: String,
        skillType: SkillType,
        limit: Int
    ): List<SkillHistory> {
        return skillDao.getSkillTrend(characterId, skillType, limit)
    }
}
