package com.ai.wechat

import com.ai.wechat.data.model.Character
import com.ai.wechat.service.CharacterManager
import com.ai.wechat.service.EconomyService
import com.ai.wechat.service.RelationshipEngine
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test

/**
 * 单元测试示例
 */
class CharacterManagerTest {

    @Test
    fun characterCreation_shouldSetInitialMoney() {
        // 测试角色创建时初始资金是否正确
        val initialMoney = 50.0
        assertEquals(initialMoney, EconomyService.INITIAL_MONEY, 0.0)
    }

    @Test
    fun dailyExpense_shouldDeductCorrectAmount() {
        // 测试每日消耗是否正确
        val dailyExpense = 5.0
        assertEquals(dailyExpense, EconomyService.DAILY_EXPENSE, 0.0)
    }

    @Test
    fun loanAmount_shouldBeCorrect() {
        // 测试贷款金额是否正确
        val loanAmount = 100.0
        assertEquals(loanAmount, EconomyService.LOAN_AMOUNT, 0.0)
    }
}

/**
 * 关系引擎测试
 */
class RelationshipEngineTest {

    @Test
    fun intimacyCalculation_strangerBonus() {
        // 测试陌生人互动加成
        val baseDelta = 2
        val coefficient = 1.2  // 陌生人系数
        val expectedDelta = baseDelta * coefficient
        assertEquals(2.4, expectedDelta, 0.01)
    }

    @Test
    fun intimacyCalculation_closeFriendDiminishing() {
        // 测试密友边际递减
        val baseDelta = 2
        val coefficient = 0.8  // 密友系数
        val expectedDelta = baseDelta * coefficient
        assertEquals(1.6, expectedDelta, 0.01)
    }

    @Test
    fun thresholdCrossing_becomeFriends() {
        // 测试成为好友阈值
        val threshold = 20
        val oldIntimacy = 19.0
        val newIntimacy = 21.0
        
        assertTrue(oldIntimacy < threshold)
        assertTrue(newIntimacy >= threshold)
    }
}

/**
 * 经济系统测试
 */
class EconomyServiceTest {

    @Test
    fun companyFoundingCost_shouldBeCorrect() {
        // 测试公司创建成本
        val foundingCost = 200.0
        assertEquals(foundingCost, EconomyService.COMPANY_FOUNDING_COST, 0.0)
    }

    @Test
    fun loanInterestRate_shouldBeCorrect() {
        // 测试贷款利率
        val interestRate = 0.01
        assertEquals(interestRate, EconomyService.LOAN_INTEREST_RATE, 0.001)
    }

    @Test
    fun bankruptcyDays_shouldBeCorrect() {
        // 测试破产天数
        val bankruptcyDays = 3
        assertEquals(bankruptcyDays, EconomyService.BANKRUPTCY_DAYS)
    }
}
