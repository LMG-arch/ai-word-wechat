package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.*
import kotlinx.coroutines.flow.Flow

/**
 * 记忆仓库接口
 */
interface MemoryRepository {
    fun getMemoriesByCharacter(characterId: String): Flow<List<Memory>>
    fun getMemoriesByType(characterId: String, type: MemoryType): Flow<List<Memory>>
    suspend fun getRecentReflections(characterId: String, limit: Int = 5): List<Memory>
    suspend fun getMemoryById(memoryId: String): Memory?
    suspend fun storeMemory(memory: Memory)
    suspend fun storeMemories(memories: List<Memory>)
    suspend fun deleteMemory(memory: Memory)
    suspend fun getMemoriesInTimeRange(characterId: String, from: Long, to: Long): List<Memory>
    suspend fun getRelevantReflections(characterId: String, taskType: String, limit: Int = 5): List<Memory>
}

/**
 * 关系仓库接口
 */
interface RelationshipRepository {
    fun getActiveRelationships(characterId: String): Flow<List<Relationship>>
    suspend fun getRelationship(fromId: String, toId: String): Relationship?
    suspend fun createRelationship(relationship: Relationship)
    suspend fun updateRelationship(relationship: Relationship)
    suspend fun endRelationship(relationshipId: String)
    suspend fun getCloseFriends(characterId: String, minIntimacy: Int = 60): List<Relationship>
    suspend fun recordRelationshipChange(change: RelationshipChange)
    fun getRelationshipChanges(relationshipId: String): Flow<List<RelationshipChange>>
}

/**
 * 技能仓库接口
 */
interface SkillRepository {
    fun getSkillsByCharacter(characterId: String): Flow<List<Skill>>
    suspend fun getSkill(characterId: String, skillType: SkillType): Skill?
    suspend fun updateSkill(skill: Skill)
    fun getSkillHistory(characterId: String): Flow<List<SkillHistory>>
    suspend fun recordSkillChange(history: SkillHistory)
    suspend fun getAverageSkill(skillType: SkillType): Float?
}

/**
 * 反思仓库接口
 */
interface ReflectionRepository {
    fun getReflectionsByCharacter(characterId: String): Flow<List<Reflection>>
    suspend fun getRecentReflections(characterId: String, limit: Int = 5): List<Reflection>
    suspend fun getReflectionById(reflectionId: String): Reflection?
    suspend fun storeReflection(reflection: Reflection)
    suspend fun getReflectionByTaskId(taskId: String): Reflection?
}

/**
 * 公司仓库接口
 */
interface CompanyRepository {
    fun getAllCompanies(): Flow<List<Company>>
    suspend fun getCompanyById(companyId: String): Company?
    suspend fun createCompany(company: Company)
    suspend fun updateCompany(company: Company)
    fun getCompanyMembers(companyId: String): Flow<List<CompanyMember>>
    suspend fun addCompanyMember(member: CompanyMember)
    fun getCompanyKnowledge(companyId: String): Flow<List<CompanyKnowledge>>
    suspend fun addCompanyKnowledge(knowledge: CompanyKnowledge)
    suspend fun incrementKnowledgeReference(knowledgeId: String)
}

/**
 * 日程仓库接口
 */
interface ScheduleRepository {
    suspend fun getScheduleByDate(characterId: String, date: String): Schedule?
    suspend fun saveSchedule(schedule: Schedule)
    fun getAllSchedulesByCharacter(characterId: String): Flow<List<Schedule>>
    fun getLocationHistory(characterId: String): Flow<List<Location>>
    suspend fun recordLocation(location: Location)
    suspend fun leaveLocation(locationId: String)
}
