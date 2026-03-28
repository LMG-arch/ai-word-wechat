package com.ai.wechat.service

import com.ai.wechat.data.memory.MemoryEngine
import com.ai.wechat.data.memory.MemoryType
import com.ai.wechat.data.model.*
import com.ai.wechat.db.dao.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 经济系统
 * 负责资金管理、贷款、破产处理
 */
@Singleton
class EconomyService @Inject constructor(
    private val characterDao: CharacterDao,
    private val companyDao: CompanyDao,
    private val memoryEngine: MemoryEngine
) {

    companion object {
        const val INITIAL_MONEY = 50.0
        const val DAILY_EXPENSE = 5.0
        const val LOAN_AMOUNT = 100.0
        const val LOAN_INTEREST_RATE = 0.01 // 日息 1%
        const val BANKRUPTCY_DAYS = 3
        const val COMPANY_FOUNDING_COST = 200.0
    }

    /**
     * 转账
     */
    suspend fun transferMoney(
        from: String,
        to: String,
        amount: Double
    ): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val now = System.currentTimeMillis()

            // 处理系统转账（系统发放奖励）
            if (from == "SYSTEM") {
                val character = characterDao.getCharacterById(to)
                    ?: return@withContext Result.failure(Exception("角色不存在"))
                characterDao.updateMoney(to, character.money + amount, now)
                return@withContext Result.success(Unit)
            }

            // 角色间转账
            val fromCharacter = characterDao.getCharacterById(from)
                ?: return@withContext Result.failure(Exception("付款方不存在"))
            val toCharacter = characterDao.getCharacterById(to)
                ?: return@withContext Result.failure(Exception("收款方不存在"))

            if (fromCharacter.money < amount) {
                return@withContext Result.failure(Exception("余额不足"))
            }

            characterDao.updateMoney(from, fromCharacter.money - amount, now)
            characterDao.updateMoney(to, toCharacter.money + amount, now)

            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 公司转账
     */
    suspend fun transferToCompany(
        from: String,
        companyId: String,
        amount: Double
    ): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val company = companyDao.getCompanyById(companyId)
                ?: return@withContext Result.failure(Exception("公司不存在"))

            val character = characterDao.getCharacterById(from)
                ?: return@withContext Result.failure(Exception("角色不存在"))

            if (character.money < amount) {
                return@withContext Result.failure(Exception("余额不足"))
            }

            characterDao.updateMoney(from, character.money - amount, System.currentTimeMillis())
            companyDao.updateMoney(companyId, company.money + amount, System.currentTimeMillis())

            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 公司发放工资
     */
    suspend fun paySalary(
        companyId: String,
        memberId: String,
        amount: Double
    ): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val company = companyDao.getCompanyById(companyId)
                ?: return@withContext Result.failure(Exception("公司不存在"))

            if (company.money < amount) {
                return@withContext Result.failure(Exception("公司余额不足"))
            }

            characterDao.updateMoney(memberId, characterDao.getCharacterById(memberId)!!.money + amount, System.currentTimeMillis())
            companyDao.updateMoney(companyId, company.money - amount, System.currentTimeMillis())

            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 每日消耗检测
     */
    suspend fun checkDailyExpense(characterId: String) = withContext(Dispatchers.IO) {
        val character = characterDao.getCharacterById(characterId) ?: return@withContext

        val newMoney = character.money - DAILY_EXPENSE
        characterDao.updateMoney(characterId, newMoney, System.currentTimeMillis())

        if (newMoney <= 0) {
            memoryEngine.storeMemory(
                characterId = characterId,
                content = "${character.name}资金归零，无法支付每日开销",
                type = MemoryType.EVENT,
                importance = 0.7f
            )
        }
    }

    /**
     * 贷款检测
     */
    suspend fun checkLoan(characterId: String) = withContext(Dispatchers.IO) {
        val character = characterDao.getCharacterById(characterId) ?: return@withContext

        if (character.money <= 0) {
            // 连续 3 天资金为 0 触发贷款
            // 这里简化处理，实际应记录天数
            characterDao.updateMoney(characterId, LOAN_AMOUNT, System.currentTimeMillis())

            memoryEngine.storeMemory(
                characterId = characterId,
                content = "${character.name}因无力维持生计，向世界银行申请了${LOAN_AMOUNT}贷款",
                type = MemoryType.EVENT,
                importance = 0.8f,
                metadata = mapOf("eventType" to "loan", "amount" to LOAN_AMOUNT)
            )
        }
    }

    /**
     * 创建公司
     */
    suspend fun createCompany(
        founderId: String,
        companyName: String,
        coFounderId: String?
    ): Result<Company> = withContext(Dispatchers.IO) {
        try {
            val founder = characterDao.getCharacterById(founderId)
                ?: return@withContext Result.failure(Exception("创始人不存在"))

            if (founder.age < 18) {
                return@withContext Result.failure(Exception("年龄未满 18 岁，不能创建公司"))
            }

            if (founder.money < COMPANY_FOUNDING_COST) {
                return@withContext Result.failure(Exception("启动资金不足${COMPANY_FOUNDING_COST}"))
            }

            val companyId = UUID.randomUUID().toString()
            val now = System.currentTimeMillis()

            val company = Company(
                id = companyId,
                name = companyName,
                founderId = founderId,
                money = 0.0,
                createdAt = now,
                updatedAt = now
            )

            // 扣除创始人资金
            characterDao.updateMoney(founderId, founder.money - COMPANY_FOUNDING_COST, now)

            // 存储公司
            companyDao.insertCompany(company)

            // 添加创始人
            companyDao.insertMember(CompanyMember(
                companyId = companyId,
                characterId = founderId,
                role = MemberRole.FOUNDER,
                joinedAt = now,
                contribution = COMPANY_FOUNDING_COST
            ))

            // 添加联合创始人
            if (coFounderId != null) {
                companyDao.insertMember(CompanyMember(
                    companyId = companyId,
                    characterId = coFounderId,
                    role = MemberRole.CO_FOUNDER,
                    joinedAt = now
                ))
            }

            memoryEngine.storeMemory(
                characterId = founderId,
                content = "${founder.name}创建了公司${companyName}",
                type = MemoryType.EVENT,
                importance = 0.9f
            )

            Result.success(company)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
