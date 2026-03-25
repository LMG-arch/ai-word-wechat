package com.ai.socialworld.data.database.dao

import androidx.room.*
import com.ai.socialworld.data.database.entity.CompanyEntity
import com.ai.socialworld.data.database.entity.CompanyMemberEntity
import kotlinx.coroutines.flow.Flow

/**
 * 公司数据访问对象
 */
@Dao
interface CompanyDao {
    @Query("SELECT * FROM companies WHERE isDeleted = 0")
    fun getAllCompanies(): Flow<List<CompanyEntity>>
    
    @Query("SELECT * FROM companies WHERE id = :id")
    suspend fun getCompanyById(id: String): CompanyEntity?
    
    @Query("SELECT * FROM companies WHERE founderId = :founderId AND isDeleted = 0")
    fun getCompaniesByFounder(founderId: String): Flow<List<CompanyEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCompany(company: CompanyEntity)
    
    @Update
    suspend fun updateCompany(company: CompanyEntity)
    
    @Delete
    suspend fun deleteCompany(company: CompanyEntity)
    
    @Query("UPDATE companies SET isDeleted = 1 WHERE id = :id")
    suspend fun softDeleteCompany(id: String)
    
    @Query("UPDATE companies SET money = money + :amount WHERE id = :id")
    suspend fun updateCompanyMoney(id: String, amount: Int)
    
    // 公司成员相关
    @Query("SELECT * FROM company_members WHERE companyId = :companyId")
    fun getCompanyMembers(companyId: String): Flow<List<CompanyMemberEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCompanyMember(member: CompanyMemberEntity)
    
    @Delete
    suspend fun deleteCompanyMember(member: CompanyMemberEntity)
    
    @Query("UPDATE company_members SET contribution = contribution + :amount WHERE companyId = :companyId AND characterId = :characterId")
    suspend fun updateMemberContribution(companyId: String, characterId: String, amount: Int)
}
