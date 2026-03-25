package com.ai.socialworld.data.repository

import com.ai.socialworld.data.local.*
import com.ai.socialworld.data.model.*
import com.ai.socialworld.domain.repository.*
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 记忆仓库实现
 */
@Singleton
class MemoryRepositoryImpl @Inject constructor(
    private val memoryDao: MemoryDao
) : MemoryRepository {
    
    override fun getMemoriesByCharacter(characterId: String): Flow<List<Memory>> {
        return memoryDao.getMemoriesByCharacter(characterId)
    }
    
    override fun getMemoriesByType(characterId: String, type: MemoryType): Flow<List<Memory>> {
        return memoryDao.getMemoriesByType(characterId, type)
    }
    
    override suspend fun getRecentReflections(characterId: String, limit: Int): List<Memory> {
        return memoryDao.getRecentReflections(characterId, limit)
    }
    
    override suspend fun getMemoryById(memoryId: String): Memory? {
        return memoryDao.getMemoryById(memoryId)
    }
    
    override suspend fun storeMemory(memory: Memory) {
        memoryDao.insertMemory(memory)
    }
    
    override suspend fun storeMemories(memories: List<Memory>) {
        memoryDao.insertMemories(memories)
    }
    
    override suspend fun deleteMemory(memory: Memory) {
        memoryDao.deleteMemory(memory)
    }
    
    override suspend fun getMemoriesInTimeRange(characterId: String, from: Long, to: Long): List<Memory> {
        return memoryDao.getMemoriesInTimeRange(characterId, from, to)
    }
    
    override suspend fun getRelevantReflections(characterId: String, taskType: String, limit: Int): List<Memory> {
        return memoryDao.getRelevantReflections(characterId, taskType, limit)
    }
}

/**
 * 关系仓库实现
 */
@Singleton
class RelationshipRepositoryImpl @Inject constructor(
    private val relationshipDao: RelationshipDao
) : RelationshipRepository {
    
    override fun getActiveRelationships(characterId: String): Flow<List<Relationship>> {
        return relationshipDao.getActiveRelationships(characterId)
    }
    
    override suspend fun getRelationship(fromId: String, toId: String): Relationship? {
        return relationshipDao.getRelationship(fromId, toId)
    }
    
    override suspend fun createRelationship(relationship: Relationship) {
        relationshipDao.insertRelationship(relationship)
    }
    
    override suspend fun updateRelationship(relationship: Relationship) {
        relationshipDao.updateRelationship(relationship)
    }
    
    override suspend fun endRelationship(relationshipId: String) {
        relationshipDao.endRelationship(relationshipId, System.currentTimeMillis())
    }
    
    override suspend fun getCloseFriends(characterId: String, minIntimacy: Int): List<Relationship> {
        return relationshipDao.getCloseFriends(characterId, minIntimacy)
    }
    
    override suspend fun recordRelationshipChange(change: RelationshipChange) {
        relationshipDao.insertRelationshipChange(change)
    }
    
    override fun getRelationshipChanges(relationshipId: String): Flow<List<RelationshipChange>> {
        return relationshipDao.getRelationshipChanges(relationshipId)
    }
}

/**
 * 技能仓库实现
 */
@Singleton
class SkillRepositoryImpl @Inject constructor(
    private val skillDao: SkillDao
) : SkillRepository {
    
    override fun getSkillsByCharacter(characterId: String): Flow<List<Skill>> {
        return skillDao.getSkillsByCharacter(characterId)
    }
    
    override suspend fun getSkill(characterId: String, skillType: SkillType): Skill? {
        return skillDao.getSkill(characterId, skillType)
    }
    
    override suspend fun updateSkill(skill: Skill) {
        skillDao.insertSkill(skill)
    }
    
    override fun getSkillHistory(characterId: String): Flow<List<SkillHistory>> {
        return skillDao.getSkillHistory(characterId)
    }
    
    override suspend fun recordSkillChange(history: SkillHistory) {
        skillDao.insertSkillHistory(history)
    }
    
    override suspend fun getAverageSkill(skillType: SkillType): Float? {
        return skillDao.getAverageSkill(skillType)
    }
}

/**
 * 反思仓库实现
 */
@Singleton
class ReflectionRepositoryImpl @Inject constructor(
    private val reflectionDao: ReflectionDao
) : ReflectionRepository {
    
    override fun getReflectionsByCharacter(characterId: String): Flow<List<Reflection>> {
        return reflectionDao.getReflectionsByCharacter(characterId)
    }
    
    override suspend fun getRecentReflections(characterId: String, limit: Int): List<Reflection> {
        return reflectionDao.getRecentReflections(characterId, limit)
    }
    
    override suspend fun getReflectionById(reflectionId: String): Reflection? {
        return reflectionDao.getReflectionById(reflectionId)
    }
    
    override suspend fun storeReflection(reflection: Reflection) {
        reflectionDao.insertReflection(reflection)
    }
    
    override suspend fun getReflectionByTaskId(taskId: String): Reflection? {
        return reflectionDao.getReflectionByTaskId(taskId)
    }
}

/**
 * 公司仓库实现
 */
@Singleton
class CompanyRepositoryImpl @Inject constructor(
    private val companyDao: CompanyDao
) : CompanyRepository {
    
    override fun getAllCompanies(): Flow<List<Company>> {
        return companyDao.getAllCompanies()
    }
    
    override suspend fun getCompanyById(companyId: String): Company? {
        return companyDao.getCompanyById(companyId)
    }
    
    override suspend fun createCompany(company: Company) {
        companyDao.insertCompany(company)
    }
    
    override suspend fun updateCompany(company: Company) {
        companyDao.updateCompany(company)
    }
    
    override fun getCompanyMembers(companyId: String): Flow<List<CompanyMember>> {
        return companyDao.getCompanyMembers(companyId)
    }
    
    override suspend fun addCompanyMember(member: CompanyMember) {
        companyDao.insertCompanyMember(member)
    }
    
    override fun getCompanyKnowledge(companyId: String): Flow<List<CompanyKnowledge>> {
        return companyDao.getCompanyKnowledge(companyId)
    }
    
    override suspend fun addCompanyKnowledge(knowledge: CompanyKnowledge) {
        companyDao.insertCompanyKnowledge(knowledge)
    }
    
    override suspend fun incrementKnowledgeReference(knowledgeId: String) {
        companyDao.incrementKnowledgeReference(knowledgeId)
    }
}

/**
 * 日程仓库实现
 */
@Singleton
class ScheduleRepositoryImpl @Inject constructor(
    private val scheduleDao: ScheduleDao
) : ScheduleRepository {
    
    override suspend fun getScheduleByDate(characterId: String, date: String): Schedule? {
        return scheduleDao.getScheduleByDate(characterId, date)
    }
    
    override suspend fun saveSchedule(schedule: Schedule) {
        scheduleDao.insertSchedule(schedule)
    }
    
    override fun getAllSchedulesByCharacter(characterId: String): Flow<List<Schedule>> {
        return scheduleDao.getAllSchedulesByCharacter(characterId)
    }
    
    override fun getLocationHistory(characterId: String): Flow<List<Location>> {
        return scheduleDao.getLocationHistory(characterId)
    }
    
    override suspend fun recordLocation(location: Location) {
        scheduleDao.insertLocation(location)
    }
    
    override suspend fun leaveLocation(locationId: String) {
        scheduleDao.leaveLocation(locationId, System.currentTimeMillis())
    }
}
