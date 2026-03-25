package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.Company
import com.ai.socialworld.data.model.CompanyMember
import com.ai.socialworld.data.model.CompanyKnowledge
import kotlinx.coroutines.flow.Flow

/**
 * 公司仓库接口
 */
interface CompanyRepository {
    
    // ==================== 公司相关 ====================
    
    suspend fun insertCompany(company: Company): Long
    suspend fun updateCompany(company: Company)
    suspend fun deleteCompany(company: Company)
    suspend fun getCompanyById(companyId: String): Company?
    fun getAllCompanies(): Flow<List<Company>>
    suspend fun getCompaniesByFounder(founderId: String): List<Company>
    suspend fun updateCompanyMoney(companyId: String, amount: Int)
    
    // ==================== 成员相关 ====================
    
    suspend fun insertMember(member: CompanyMember)
    suspend fun removeMember(companyId: String, characterId: String)
    suspend fun getCompanyMembersSync(companyId: String): List<CompanyMember>
    fun getCompanyMembers(companyId: String): Flow<List<CompanyMember>>
    suspend fun updateContribution(companyId: String, characterId: String, amount: Int)
    
    // ==================== 知识库相关 ====================
    
    suspend fun insertKnowledge(knowledge: CompanyKnowledge)
    fun getCompanyKnowledge(companyId: String): Flow<List<CompanyKnowledge>>
    suspend fun getTopKnowledge(companyId: String, limit: Int): List<CompanyKnowledge>
    suspend fun incrementKnowledgeReference(knowledgeId: String)
}
