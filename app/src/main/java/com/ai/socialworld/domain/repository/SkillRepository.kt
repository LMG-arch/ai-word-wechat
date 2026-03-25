package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.Skill
import com.ai.socialworld.data.model.SkillHistory
import com.ai.socialworld.data.model.SkillType
import kotlinx.coroutines.flow.Flow

/**
 * 技能仓库接口
 */
interface SkillRepository {
    
    /**
     * 插入技能
     */
    suspend fun insertSkill(skill: Skill)
    
    /**
     * 更新技能
     */
    suspend fun updateSkill(skill: Skill)
    
    /**
     * 获取角色的所有技能
     */
    fun getSkillsByCharacter(characterId: String): Flow<List<Skill>>
    
    /**
     * 获取角色的所有技能（同步）
     */
    suspend fun getSkillsByCharacterSync(characterId: String): List<Skill>
    
    /**
     * 获取指定类型的技能
     */
    suspend fun getSkillSync(characterId: String, skillType: SkillType): Skill?
    
    /**
     * 获取技能历史
     */
    fun getSkillHistory(characterId: String): Flow<List<SkillHistory>>
    
    /**
     * 插入技能历史
     */
    suspend fun insertSkillHistory(history: SkillHistory)
    
    /**
     * 获取技能变化趋势
     */
    suspend fun getSkillTrend(
        characterId: String,
        skillType: SkillType,
        limit: Int = 10
    ): List<SkillHistory>
}
