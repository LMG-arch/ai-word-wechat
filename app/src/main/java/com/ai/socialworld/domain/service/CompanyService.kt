package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.*
import com.ai.socialworld.domain.repository.ApiConfigRepository
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.domain.repository.RelationshipRepository
import com.ai.socialworld.data.repository.CompanyRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 公司管理服务
 * 处理公司创建、成员管理、知识库等
 */
@Singleton
class CompanyService @Inject constructor(
    private val companyRepository: CompanyRepository,
    private val characterRepository: CharacterRepository,
    private val relationshipRepository: RelationshipRepository,
    private val apiConfigRepository: ApiConfigRepository,
    private val reflectionEngine: ReflectionEngine
) {
    
    companion object {
        const val MIN_AGE_TO_CREATE_COMPANY = 18
        const val MIN_MONEY_TO_CREATE_COMPANY = 200
        const val MIN_INTIMACY_FOR_CO_FOUNDER = 60  // 联合创始人亲密度要求
    }
    
    /**
     * 创建公司
     */
    suspend fun createCompany(
        name: String,
        founderId: String,
        coFounderId: String
    ): CompanyResult = withContext(Dispatchers.IO) {
        
        // 1. 检查创始人条件
        val founder = characterRepository.getCharacterById(founderId.toLong())
        if (founder == null) {
            return@withContext CompanyResult.Error("创始人不存在")
        }
        
        if (founder.age < MIN_AGE_TO_CREATE_COMPANY) {
            return@withContext CompanyResult.Error("创始人年龄不足18岁")
        }
        
        if (founder.money < MIN_MONEY_TO_CREATE_COMPANY) {
            return@withContext CompanyResult.Error("创始人资金不足200")
        }
        
        // 2. 检查联合创始人
        val coFounder = characterRepository.getCharacterById(coFounderId.toLong())
        if (coFounder == null) {
            return@withContext CompanyResult.Error("联合创始人不存在")
        }
        
        // 3. 检查亲密度
        val canCreate = relationshipRepository.getRelationshipBetween(founderId, coFounderId)
        if (canCreate == null || canCreate.intimacy < MIN_INTIMACY_FOR_CO_FOUNDER) {
            return@withContext CompanyResult.Error("亲密度不足60，无法创建公司")
        }
        
        // 4. 扣除资金
        characterRepository.updateCharacterMoney(founderId.toLong(), -MIN_MONEY_TO_CREATE_COMPANY)
        
        // 5. 创建公司
        val companyId = UUID.randomUUID().toString()
        val company = Company(
            id = companyId,
            name = name,
            founderId = founderId,
            money = MIN_MONEY_TO_CREATE_COMPANY, // 启动资金转入公司账户
            createdAt = System.currentTimeMillis()
        )
        
        companyRepository.insertCompany(company)
        
        // 6. 添加创始人作为法人
        val founderMember = CompanyMember(
            companyId = companyId,
            characterId = founderId,
            role = CompanyRole.FOUNDER.name,
            joinedAt = System.currentTimeMillis(),
            contribution = 0
        )
        companyRepository.insertMember(founderMember)
        
        // 7. 添加联合创始人
        val coFounderMember = CompanyMember(
            companyId = companyId,
            characterId = coFounderId,
            role = CompanyRole.CO_FOUNDER.name,
            joinedAt = System.currentTimeMillis(),
            contribution = 0
        )
        companyRepository.insertMember(coFounderMember)
        
        // 8. 记录日志
        apiConfigRepository.addLog(
            characterId = founderId,
            characterName = founder.name,
            logType = com.ai.socialworld.domain.repository.LogType.TASK,
            content = "创建公司: $name，联合创始人: ${coFounder.name}"
        )
        
        apiConfigRepository.addLog(
            characterId = coFounderId,
            characterName = coFounder.name,
            logType = com.ai.socialworld.domain.repository.LogType.TASK,
            content = "加入公司: $name，作为联合创始人"
        )
        
        CompanyResult.Success(
            company = company,
            message = "公司创建成功！启动资金: $MIN_MONEY_TO_CREATE_COMPANY"
        )
    }
    
    /**
     * 邀请成员加入公司
     */
    suspend fun inviteMember(
        companyId: String,
        inviterId: String,
        inviteeId: String
    ): CompanyResult = withContext(Dispatchers.IO) {
        
        val company = companyRepository.getCompanyById(companyId)
        if (company == null) {
            return@withContext CompanyResult.Error("公司不存在")
        }
        
        // 检查邀请者权限
        val members = companyRepository.getCompanyMembersSync(companyId)
        val inviter = members.find { it.characterId == inviterId }
        if (inviter == null || inviter.role != CompanyRole.FOUNDER.name) {
            return@withContext CompanyResult.Error("只有法人才能邀请成员")
        }
        
        // 检查是否已是成员
        if (members.any { it.characterId == inviteeId }) {
            return@withContext CompanyResult.Error("该角色已是公司成员")
        }
        
        // 添加成员
        val newMember = CompanyMember(
            companyId = companyId,
            characterId = inviteeId,
            role = CompanyRole.MEMBER.name,
            joinedAt = System.currentTimeMillis(),
            contribution = 0
        )
        companyRepository.insertMember(newMember)
        
        // 推送公司知识库高频反思
        pushKnowledgeToNewMember(companyId, inviteeId)
        
        // 记录日志
        val invitee = characterRepository.getCharacterById(inviteeId.toLong())
        apiConfigRepository.addLog(
            characterId = inviteeId,
            characterName = invitee?.name,
            logType = com.ai.socialworld.domain.repository.LogType.TASK,
            content = "加入公司: ${company.name}"
        )
        
        CompanyResult.Success(message = "邀请成功")
    }
    
    /**
     * 推送公司知识库给新成员
     */
    private suspend fun pushKnowledgeToNewMember(companyId: String, memberId: String) {
        val topKnowledge = companyRepository.getTopKnowledge(companyId, limit = 5)
        
        // TODO: 将知识库内容推送给新成员
        // 可以作为消息或通知
    }
    
    /**
     * 分配奖金
     */
    suspend fun distributeBonus(
        companyId: String,
        totalAmount: Int,
        distribution: Map<String, Int> // characterId -> amount
    ): CompanyResult = withContext(Dispatchers.IO) {
        
        val company = companyRepository.getCompanyById(companyId)
        if (company == null) {
            return@withContext CompanyResult.Error("公司不存在")
        }
        
        if (company.money < totalAmount) {
            return@withContext CompanyResult.Error("公司资金不足")
        }
        
        // 扣除公司资金
        companyRepository.updateCompanyMoney(companyId, -totalAmount)
        
        // 分配给成员
        distribution.forEach { (characterId, amount) ->
            characterRepository.updateCharacterMoney(characterId.toLong(), amount)
            
            // 更新贡献度
            companyRepository.updateContribution(companyId, characterId, amount)
        }
        
        // 记录日志
        apiConfigRepository.addLog(
            characterId = null,
            characterName = null,
            logType = com.ai.socialworld.domain.repository.LogType.ECONOMY,
            content = "公司${company.name}发放奖金: $totalAmount"
        )
        
        CompanyResult.Success(message = "奖金分配成功")
    }
    
    /**
     * 添加反思到公司知识库
     */
    suspend fun addReflectionToKnowledgeBase(
        companyId: String,
        reflection: Reflection
    ): Boolean = withContext(Dispatchers.IO) {
        
        val knowledge = CompanyKnowledge(
            id = UUID.randomUUID().toString(),
            companyId = companyId,
            reflectionId = reflection.id,
            title = "任务反思: ${reflection.taskId}",
            summary = reflection.lessonsLearned.take(3).joinToString("; "),
            tags = "[\"${reflection.taskId}\"]",
            referenceCount = 0,
            createdAt = System.currentTimeMillis()
        )
        
        companyRepository.insertKnowledge(knowledge)
        
        // 如果重要性高，通知所有成员
        if (reflection.importance >= 0.8f) {
            val members = companyRepository.getCompanyMembersSync(companyId)
            members.forEach { member ->
                apiConfigRepository.addLog(
                    characterId = member.characterId,
                    characterName = null,
                    logType = com.ai.socialworld.domain.repository.LogType.MEMORY,
                    content = "公司知识库更新: ${knowledge.title}"
                )
            }
        }
        
        true
    }
    
    /**
     * 获取公司成员列表（按贡献度排序）
     */
    suspend fun getMembersByContribution(companyId: String): List<CompanyMemberWithCharacter> = withContext(Dispatchers.IO) {
        val members = companyRepository.getCompanyMembersSync(companyId)
        
        members.map { member ->
            val character = characterRepository.getCharacterById(member.characterId.toLong())
            CompanyMemberWithCharacter(
                member = member,
                character = character
            )
        }.sortedByDescending { it.member.contribution }
    }
    
    /**
     * 获取公司统计
     */
    suspend fun getCompanyStats(companyId: String): CompanyStats? = withContext(Dispatchers.IO) {
        val company = companyRepository.getCompanyById(companyId) ?: return@withContext null
        val members = companyRepository.getCompanyMembersSync(companyId)
        
        CompanyStats(
            companyId = companyId,
            companyName = company.name,
            totalMembers = members.size,
            totalMoney = company.money,
            totalContribution = members.sumOf { it.contribution },
            averageContribution = if (members.isNotEmpty()) members.map { it.contribution }.average().toInt() else 0
        )
    }
    
    /**
     * 移除成员
     */
    suspend fun removeMember(
        companyId: String,
        memberId: String,
        removerId: String
    ): CompanyResult = withContext(Dispatchers.IO) {
        
        val company = companyRepository.getCompanyById(companyId)
        if (company == null) {
            return@withContext CompanyResult.Error("公司不存在")
        }
        
        // 检查权限
        val members = companyRepository.getCompanyMembersSync(companyId)
        val remover = members.find { it.characterId == removerId }
        if (remover == null || remover.role != CompanyRole.FOUNDER.name) {
            return@withContext CompanyResult.Error("只有法人才能移除成员")
        }
        
        // 不能移除法人
        if (memberId == company.founderId) {
            return@withContext CompanyResult.Error("不能移除法人")
        }
        
        // 移除
        companyRepository.removeMember(companyId, memberId)
        
        // 记录日志
        val member = characterRepository.getCharacterById(memberId.toLong())
        apiConfigRepository.addLog(
            characterId = memberId,
            characterName = member?.name,
            logType = com.ai.socialworld.domain.repository.LogType.TASK,
            content = "已离开公司: ${company.name}"
        )
        
        CompanyResult.Success(message = "成员已移除")
    }
}

// ==================== 数据类和枚举 ====================

enum class CompanyRole {
    FOUNDER,      // 法人（创始人）
    CO_FOUNDER,   // 联合创始人
    MEMBER        // 普通成员
}

sealed class CompanyResult {
    data class Success(
        val company: Company? = null,
        val message: String
    ) : CompanyResult()
    
    data class Error(val message: String) : CompanyResult()
}

data class CompanyMemberWithCharacter(
    val member: CompanyMember,
    val character: Character?
)

data class CompanyStats(
    val companyId: String,
    val companyName: String,
    val totalMembers: Int,
    val totalMoney: Int,
    val totalContribution: Int,
    val averageContribution: Int
)
