package com.ai.socialworld.domain.engine

import com.ai.socialworld.data.model.Character
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 经济系统引擎
 * 处理资金、贷款、破产等
 */
@Singleton
class EconomyEngine @Inject constructor() {
    
    private val _loanRecords = MutableStateFlow<List<LoanRecord>>(emptyList())
    val loanRecords: StateFlow<List<LoanRecord>> = _loanRecords
    
    companion object {
        const val INITIAL_MONEY = 50
        const val DAILY_CONSUMPTION = 5
        const val LOAN_AMOUNT = 100
        const val LOAN_INTEREST_RATE = 0.01 // 日息1%
        const val LOAN_OVERDUE_DAYS = 7
        const val BANKRUPTCY_THRESHOLD_DAYS = 3
    }
    
    /**
     * 检查是否可以贷款
     */
    fun canApplyLoan(character: Character, zeroMoneyDays: Int): Boolean {
        return character.money <= 0 && zeroMoneyDays >= BANKRUPTCY_THRESHOLD_DAYS
    }
    
    /**
     * 申请贷款
     */
    fun applyLoan(characterId: String): LoanRecord {
        val loan = LoanRecord(
            characterId = characterId,
            amount = LOAN_AMOUNT,
            interestRate = LOAN_INTEREST_RATE,
            borrowedAt = System.currentTimeMillis()
        )
        _loanRecords.value = _loanRecords.value + loan
        return loan
    }
    
    /**
     * 计算贷款利息
     */
    fun calculateInterest(loan: LoanRecord): Double {
        val days = (System.currentTimeMillis() - loan.borrowedAt) / (1000 * 60 * 60 * 24)
        return loan.amount * loan.interestRate * days
    }
    
    /**
     * 检查是否逾期
     */
    fun isOverdue(loan: LoanRecord): Boolean {
        val days = (System.currentTimeMillis() - loan.borrowedAt) / (1000 * 60 * 60 * 24)
        return days > LOAN_OVERDUE_DAYS && !loan.isRepaid
    }
    
    /**
     * 获取贫困状态描述
     */
    fun getPovertyStatusDescription(money: Int): String {
        return when {
            money > 50 -> "富裕"
            money > 20 -> "小康"
            money > 0 -> "拮据"
            money > -50 -> "贫困"
            else -> "破产"
        }
    }
    
    /**
     * 检查角色是否破产
     */
    fun isBankrupt(character: Character): Boolean {
        return character.money < -50
    }
}

/**
 * 贷款记录
 */
data class LoanRecord(
    val id: String = "loan_${System.currentTimeMillis()}",
    val characterId: String,
    val amount: Int,
    val interestRate: Double,
    val borrowedAt: Long,
    var isRepaid: Boolean = false,
    var repaidAt: Long? = null
)
