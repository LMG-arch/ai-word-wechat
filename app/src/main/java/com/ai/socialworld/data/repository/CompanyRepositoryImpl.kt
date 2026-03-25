package com.ai.socialworld.data.repository

import com.ai.socialworld.data.local.CompanyDao
import com.ai.socialworld.data.model.Company
import com.ai.socialworld.data.model.CompanyKnowledge
import com.ai.socialworld.data.model.CompanyMember
import com.ai.socialworld.domain.repository.CompanyRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 公司仓库实现
 */
@Singleton
class CompanyRepositoryImpl @Inject constructor(
    private val companyDao: CompanyDao
) : CompanyRepository {
    
    // ==================== 公司相关 ====================
    
    override suspend fun insertCompany(company: Company): Long {
        return companyDao.insert(company)
    }
    
    override suspend fun updateCompany(company: Company) {
        companyDao.update(company)
    }
    
    override suspend fun deleteCompany(company: Company) {
        companyDao.delete(company)
    }
    
    override suspend fun getCompanyById(companyId: String): Company? {
        return companyDao.getCompanyById(companyId)
    }
    
    override fun getAllCompanies(): Flow<List<Company>> {
        return companyDao.getAllCompanies()
    }
    
    override suspend fun getCompaniesByFounder(founderId: String): List<Company> {
        return companyDao.getCompaniesByFounder(founderId)
    }
    
    override suspend fun updateCompanyMoney(companyId: String, amount: Int) {
        companyDao.updateMoney(companyId, amount)
    }
    
    // ==================== 成员相关 ====================
    
    override suspend fun insertMember(member: CompanyMember) {
        companyDao.insertMember(member)
    }
    
    override suspend fun removeMember(companyId: String, characterId: String) {
        companyDao.removeMember(companyId, characterId)
    }
    
    override suspend fun getCompanyMembersSync(companyId: String): List<CompanyMember> {
        return companyDao.getCompanyMembersSync(companyId)
    }
    
    override fun getCompanyMembers(companyId: String): Flow<List<CompanyMember>> {
        return companyDao.getCompanyMembers(companyId)
    }
    
    override suspend fun updateContribution(companyId: String, characterId: String, amount: Int) {
        companyDao.updateContribution(companyId, characterId, amount)
    }
    
    // ==================== 知识库相关 ====================
    
    override suspend fun insertKnowledge(knowledge: CompanyKnowledge) {
        companyDao.insertKnowledge(knowledge)
    }
    
    override fun getCompanyKnowledge(companyId: String): Flow<List<CompanyKnowledge>> {
        return companyDao.getCompanyKnowledge(companyId)
    }
    
    override suspend fun getTopKnowledge(companyId: String, limit: Int): List<CompanyKnowledge> {
        return companyDao.getTopKnowledge(companyId, limit)
    }
    
    override suspend fun incrementKnowledgeReference(knowledgeId: String) {
        companyDao.incrementReference(knowledgeId)
    }
}
