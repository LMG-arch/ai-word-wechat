package com.ai.wechat.db.dao

import androidx.room.*
import com.ai.wechat.data.model.Company
import com.ai.wechat.data.model.CompanyMember
import kotlinx.coroutines.flow.Flow

/**
 * 公司数据访问对象
 */
@Dao
interface CompanyDao {

    @Query("SELECT * FROM companies ORDER BY createdAt DESC")
    fun getAllCompanies(): Flow<List<Company>>

    @Query("SELECT * FROM companies WHERE id = :id")
    suspend fun getCompanyById(id: String): Company?

    @Query("SELECT * FROM companies WHERE id = :id")
    fun getCompanyByIdFlow(id: String): Flow<Company?>

    @Query("SELECT * FROM companies WHERE founderId = :founderId")
    suspend fun getCompanyByFounder(founderId: String): Company?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCompany(company: Company)

    @Update
    suspend fun updateCompany(company: Company)

    @Delete
    suspend fun deleteCompany(company: Company)

    @Query("UPDATE companies SET money = :money, updatedAt = :updatedAt WHERE id = :id")
    suspend fun updateMoney(id: String, money: Double, updatedAt: Long)

    // Company Members
    @Query("SELECT * FROM company_members WHERE companyId = :companyId ORDER BY joinedAt")
    fun getMembersByCompanyId(companyId: String): Flow<List<CompanyMember>>

    @Query("SELECT * FROM company_members WHERE characterId = :characterId")
    suspend fun getMemberByCharacterId(characterId: String): CompanyMember?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMember(member: CompanyMember)

    @Update
    suspend fun updateMember(member: CompanyMember)

    @Delete
    suspend fun deleteMember(member: CompanyMember)

    @Query("SELECT COUNT(*) FROM company_members WHERE companyId = :companyId")
    suspend fun getMemberCount(companyId: String): Int
}
