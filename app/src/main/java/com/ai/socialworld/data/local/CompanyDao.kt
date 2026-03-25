package com.ai.socialworld.data.local

import androidx.room.*
import com.ai.socialworld.data.model.Company
import com.ai.socialworld.data.model.CompanyMember
import com.ai.socialworld.data.model.CompanyKnowledge
import kotlinx.coroutines.flow.Flow

/**
 * 公司DAO
 */
@Dao
interface CompanyDao {
    
    // ==================== 公司相关 ====================
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(company: Company): Long
    
    @Update
    suspend fun update(company: Company)
    
    @Delete
    suspend fun delete(company: Company)
    
    @Query("SELECT * FROM companies WHERE id = :companyId")
    suspend fun getCompanyById(companyId: String): Company?
    
    @Query("SELECT * FROM companies ORDER BY createdAt DESC")
    fun getAllCompanies(): Flow<List<Company>>
    
    @Query("SELECT * FROM companies WHERE founderId = :founderId")
    suspend fun getCompaniesByFounder(founderId: String): List<Company>
    
    @Query("UPDATE companies SET money = money + :amount WHERE id = :companyId")
    suspend fun updateMoney(companyId: String, amount: Int)
    
    // ==================== 公司成员 ====================
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMember(member: CompanyMember)
    
    @Delete
    suspend fun deleteMember(member: CompanyMember)
    
    @Query("SELECT * FROM company_members WHERE companyId = :companyId")
    suspend fun getCompanyMembersSync(companyId: String): List<CompanyMember>
    
    @Query("SELECT * FROM company_members WHERE companyId = :companyId")
    fun getCompanyMembers(companyId: String): Flow<List<CompanyMember>>
    
    @Query("SELECT * FROM company_members WHERE characterId = :characterId")
    suspend fun getMemberCompanies(characterId: String): List<CompanyMember>
    
    @Query("DELETE FROM company_members WHERE companyId = :companyId AND characterId = :characterId")
    suspend fun removeMember(companyId: String, characterId: String)
    
    @Query("UPDATE company_members SET contribution = contribution + :amount WHERE companyId = :companyId AND characterId = :characterId")
    suspend fun updateContribution(companyId: String, characterId: String, amount: Int)
    
    // ==================== 公司知识库 ====================
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertKnowledge(knowledge: CompanyKnowledge)
    
    @Query("SELECT * FROM company_knowledge WHERE companyId = :companyId ORDER BY createdAt DESC")
    fun getCompanyKnowledge(companyId: String): Flow<List<CompanyKnowledge>>
    
    @Query("SELECT * FROM company_knowledge WHERE companyId = :companyId ORDER BY referenceCount DESC LIMIT :limit")
    suspend fun getTopKnowledge(companyId: String, limit: Int): List<CompanyKnowledge>
    
    @Query("UPDATE company_knowledge SET referenceCount = referenceCount + 1 WHERE id = :knowledgeId")
    suspend fun incrementReference(knowledgeId: String)
}
