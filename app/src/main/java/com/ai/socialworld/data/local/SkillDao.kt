package com.ai.socialworld.data.local

import androidx.room.*
import com.ai.socialworld.data.model.Skill
import com.ai.socialworld.data.model.SkillHistory
import com.ai.socialworld.data.model.SkillType
import kotlinx.coroutines.flow.Flow

/**
 * 技能DAO
 */
@Dao
interface SkillDao {
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(skill: Skill)
    
    @Update
    suspend fun update(skill: Skill)
    
    @Delete
    suspend fun delete(skill: Skill)
    
    @Query("SELECT * FROM skills WHERE characterId = :characterId")
    fun getSkillsByCharacter(characterId: String): Flow<List<Skill>>
    
    @Query("SELECT * FROM skills WHERE characterId = :characterId")
    suspend fun getSkillsByCharacterSync(characterId: String): List<Skill>
    
    @Query("SELECT * FROM skills WHERE characterId = :characterId AND skillType = :skillType")
    suspend fun getSkill(characterId: String, skillType: SkillType): Skill?
    
    @Query("DELETE FROM skills WHERE characterId = :characterId AND skillType = :skillType")
    suspend fun deleteSkill(characterId: String, skillType: SkillType)
    
    // ==================== 技能历史 ====================
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSkillHistory(history: SkillHistory)
    
    @Query("SELECT * FROM skill_history WHERE characterId = :characterId ORDER BY changedAt DESC")
    fun getSkillHistory(characterId: String): Flow<List<SkillHistory>>
    
    @Query("""
        SELECT * FROM skill_history 
        WHERE characterId = :characterId 
        AND skillType = :skillType 
        ORDER BY changedAt DESC 
        LIMIT :limit
    """)
    suspend fun getSkillTrend(
        characterId: String,
        skillType: SkillType,
        limit: Int
    ): List<SkillHistory>
    
    @Query("SELECT COUNT(*) FROM skills WHERE characterId = :characterId")
    suspend fun getSkillCount(characterId: String): Int
}
