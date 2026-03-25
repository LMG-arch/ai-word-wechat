package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.Character
import com.ai.socialworld.data.model.WorldSettings
import com.ai.socialworld.domain.repository.ApiConfigRepository
import com.ai.socialworld.domain.repository.CharacterRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 经济系统服务
 * 管理角色资金、日常消耗、贷款等
 */
@Singleton
class EconomyService @Inject constructor(
    private val characterRepository: CharacterRepository,
    private val apiConfigRepository: ApiConfigRepository,
    private val languageModelService: LanguageModelService
) {
    
    // 默认经济参数
    companion object {
        const val INITIAL_MONEY = 50          // 初始资金
        const val DAILY_CONSUMPTION = 5       // 每日消耗
        const val LOAN_AMOUNT = 100           // 贷款额度
        const val LOAN_INTEREST_RATE = 0.01f  // 日息1%
        const val LOAN_TRIGGER_DAYS = 3       // 贫困触发天数
        const val MAX_OVERDUE_DAYS = 7        // 逾期触发天数
    }
    
    /**
     * 执行每日资金消耗
     */
    suspend fun performDailyConsumption(): Int = withContext(Dispatchers.IO) {
        val settings = apiConfigRepository.getWorldSettings()
        val consumption = settings?.dailyConsumption ?: DAILY_CONSUMPTION
        
        val characters = characterRepository.getAllCharactersSync()
        var processedCount = 0
        
        characters.forEach { character ->
            // 扣除日常消耗
            val newMoney = (character.money - consumption).coerceAtLeast(-100)
            characterRepository.updateCharacterMoney(character.id, -consumption)
            
            // 记录日志
            apiConfigRepository.addLog(
                characterId = character.id.toString(),
                characterName = character.name,
                logType = com.ai.socialworld.domain.repository.LogType.ECONOMY,
                content = "每日消耗: -$consumption 资金, 当前: $newMoney"
            )
            
            processedCount++
        }
        
        processedCount
    }
    
    /**
     * 检查并处理贫困状态
     */
    suspend fun checkPovertyStatus(): List<PovertyAlert> = withContext(Dispatchers.IO) {
        val alerts = mutableListOf<PovertyAlert>()
        val characters = characterRepository.getAllCharactersSync()
        
        characters.forEach { character ->
            if (character.money <= 0) {
                // 检查贫困天数
                val povertyDays = calculatePovertyDays(character)
                
                when {
                    povertyDays >= LOAN_TRIGGER_DAYS && character.money < 0 -> {
                        // 触发自动贷款
                        val loanAmount = (apiConfigRepository.getWorldSettings()?.loanAmount ?: LOAN_AMOUNT)
                        triggerAutoLoan(character, loanAmount)
                        
                        alerts.add(PovertyAlert.AutoLoan(
                            characterId = character.id.toString(),
                            characterName = character.name,
                            amount = loanAmount
                        ))
                    }
                    character.money < 0 -> {
                        // 贫困状态警告
                        alerts.add(PovertyAlert.Warning(
                            characterId = character.id.toString(),
                            characterName = character.name,
                            daysInPoverty = povertyDays,
                            currentMoney = character.money
                        ))
                    }
                }
            }
        }
        
        alerts
    }
    
    /**
     * 触发自动贷款
     */
    private suspend fun triggerAutoLoan(character: Character, amount: Int) {
        // 增加资金
        characterRepository.updateCharacterMoney(character.id, amount)
        
        // 记录贷款（简化：直接加钱，不记录债务）
        // 实际项目中应该有专门的债务表
        
        // 记录日志
        apiConfigRepository.addLog(
            characterId = character.id.toString(),
            characterName = character.name,
            logType = com.ai.socialworld.domain.repository.LogType.ECONOMY,
            content = "自动贷款: +$amount 资金"
        )
    }
    
    /**
     * 计算贫困天数（简化实现）
     */
    private fun calculatePovertyDays(character: Character): Int {
        // TODO: 实际应该记录贫困开始时间
        // 这里简化处理
        return if (character.money < 0) {
            (-character.money / 10).coerceIn(1, 10)
        } else {
            0
        }
    }
    
    /**
     * 转账（角色间）
     */
    suspend fun transferMoney(
        fromId: Long,
        toId: Long,
        amount: Int
    ): TransferResult = withContext(Dispatchers.IO) {
        val fromCharacter = characterRepository.getCharacterById(fromId)
        val toCharacter = characterRepository.getCharacterById(toId)
        
        if (fromCharacter == null || toCharacter == null) {
            return@withContext TransferResult.Error("角色不存在")
        }
        
        if (fromCharacter.money < amount) {
            return@withContext TransferResult.Error("资金不足")
        }
        
        if (amount <= 0) {
            return@withContext TransferResult.Error("转账金额必须大于0")
        }
        
        // 执行转账
        characterRepository.updateCharacterMoney(fromId, -amount)
        characterRepository.updateCharacterMoney(toId, amount)
        
        // 记录日志
        apiConfigRepository.addLog(
            characterId = fromId.toString(),
            characterName = fromCharacter.name,
            logType = com.ai.socialworld.domain.repository.LogType.ECONOMY,
            content = "转账给${toCharacter.name}: -$amount"
        )
        
        apiConfigRepository.addLog(
            characterId = toId.toString(),
            characterName = toCharacter.name,
            logType = com.ai.socialworld.domain.repository.LogType.ECONOMY,
            content = "收到${fromCharacter.name}转账: +$amount"
        )
        
        TransferResult.Success(
            fromBalance = fromCharacter.money - amount,
            toBalance = toCharacter.money + amount
        )
    }
    
    /**
     * 发放任务奖励
     */
    suspend fun grantTaskReward(
        characterId: Long,
        amount: Int,
        reason: String
    ): Boolean = withContext(Dispatchers.IO) {
        val character = characterRepository.getCharacterById(characterId)
            ?: return@withContext false
        
        characterRepository.updateCharacterMoney(characterId, amount)
        
        // 记录日志
        apiConfigRepository.addLog(
            characterId = characterId.toString(),
            characterName = character.name,
            logType = com.ai.socialworld.domain.repository.LogType.ECONOMY,
            content = "$reason: +$amount 资金"
        )
        
        true
    }
    
    /**
     * 购买物品（消耗资金）
     */
    suspend fun purchase(
        characterId: Long,
        amount: Int,
        item: String
    ): PurchaseResult = withContext(Dispatchers.IO) {
        val character = characterRepository.getCharacterById(characterId)
            ?: return@withContext PurchaseResult.Error("角色不存在")
        
        if (character.money < amount) {
            return@withContext PurchaseResult.InsufficientFunds(
                current = character.money,
                required = amount
            )
        }
        
        characterRepository.updateCharacterMoney(characterId, -amount)
        
        // 记录日志
        apiConfigRepository.addLog(
            characterId = characterId.toString(),
            characterName = character.name,
            logType = com.ai.socialworld.domain.repository.LogType.ECONOMY,
            content = "购买$item: -$amount 资金"
        )
        
        PurchaseResult.Success(
            item = item,
            newBalance = character.money - amount
        )
    }
    
    /**
     * 获取角色经济状态
     */
    suspend fun getEconomicStatus(characterId: Long): EconomicStatus = withContext(Dispatchers.IO) {
        val character = characterRepository.getCharacterById(characterId)
            ?: return@withContext EconomicStatus.Unknown
        
        val wealthLevel = when {
            character.money >= 500 -> WealthLevel.RICH
            character.money >= 200 -> WealthLevel.WELL_OFF
            character.money >= 100 -> WealthLevel.COMFORTABLE
            character.money >= 50 -> WealthLevel.AVERAGE
            character.money >= 20 -> WealthLevel.POOR
            character.money > 0 -> WealthLevel.STRUGGLING
            else -> WealthLevel.DESTITUTE
        }
        
        EconomicStatus(
            characterId = characterId,
            characterName = character.name,
            money = character.money,
            wealthLevel = wealthLevel,
            dailyConsumption = apiConfigRepository.getWorldSettings()?.dailyConsumption ?: DAILY_CONSUMPTION
        )
    }
    
    /**
     * 生成贫困对话提示
     */
    suspend fun generatePovertyDialoguePrompt(characterId: Long): String? = withContext(Dispatchers.IO) {
        val character = characterRepository.getCharacterById(characterId)
            ?: return@withContext null
        
        if (character.money >= 20) {
            return@withContext null
        }
        
        when {
            character.money < 0 -> "我现在身无分文，还欠着债，生活太艰难了..."
            character.money < 10 -> "我的钱快花光了，不知道该怎么办..."
            character.money < 20 -> "最近手头有点紧，得想办法赚点钱..."
            else -> null
        }
    }
}

// ==================== 数据类和枚举 ====================

sealed class TransferResult {
    data class Success(
        val fromBalance: Int,
        val toBalance: Int
    ) : TransferResult()
    
    data class Error(val message: String) : TransferResult()
}

sealed class PurchaseResult {
    data class Success(
        val item: String,
        val newBalance: Int
    ) : PurchaseResult()
    
    data class InsufficientFunds(
        val current: Int,
        val required: Int
    ) : PurchaseResult()
    
    data class Error(val message: String) : PurchaseResult()
}

sealed class PovertyAlert {
    data class Warning(
        val characterId: String,
        val characterName: String,
        val daysInPoverty: Int,
        val currentMoney: Int
    ) : PovertyAlert()
    
    data class AutoLoan(
        val characterId: String,
        val characterName: String,
        val amount: Int
    ) : PovertyAlert()
}

enum class WealthLevel {
    RICH,        // 富裕 (500+)
    WELL_OFF,    // 小康 (200-499)
    COMFORTABLE, // 舒适 (100-199)
    AVERAGE,     // 一般 (50-99)
    POOR,        // 贫困 (20-49)
    STRUGGLING,  // 挣扎 (1-19)
    DESTITUTE    // 一贫如洗 (0或负)
}

data class EconomicStatus(
    val characterId: Long,
    val characterName: String,
    val money: Int,
    val wealthLevel: WealthLevel,
    val dailyConsumption: Int
) {
    val daysUntilBankrupt: Int
        get() = if (dailyConsumption > 0) {
            (money / dailyConsumption).coerceAtLeast(0)
        } else {
            Int.MAX_VALUE
        }
    
    val isBankrupt: Boolean
        get() = money <= 0
}
