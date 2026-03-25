package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.GrowthStage
import com.ai.socialworld.data.model.WorldSettings
import com.ai.socialworld.domain.repository.ApiConfigRepository
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.domain.repository.ScheduleRepository
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 世界时间管理器
 * 管理世界时间流逝和定时任务
 */
@Singleton
class WorldTimeManager @Inject constructor(
    private val characterRepository: CharacterRepository,
    private val scheduleRepository: ScheduleRepository,
    private val apiConfigRepository: ApiConfigRepository,
    private val economyService: EconomyService,
    private val relationshipEngine: RelationshipEngine,
    private val scheduleEngine: ScheduleEngine,
    private val reflectionEngine: ReflectionEngine
) {
    
    // 世界时间状态
    private val _worldTime = MutableStateFlow(System.currentTimeMillis())
    val worldTime: StateFlow<Long> = _worldTime
    
    // 时间倍速
    private val _timeMultiplier = MutableStateFlow(1)
    val timeMultiplier: StateFlow<Int> = _timeMultiplier
    
    // 是否运行中
    private val _isRunning = MutableStateFlow(false)
    val isRunning: StateFlow<Boolean> = _isRunning
    
    // 定时任务Job
    private var timeJob: Job? = null
    private var dailyJob: Job? = null
    
    // 上次执行每日任务的时间
    private var lastDailyTaskTime: Long = 0
    
    companion object {
        const val MIN_MULTIPLIER = 1
        const val MAX_MULTIPLIER = 30
        const val DAY_IN_MILLIS = 24 * 60 * 60 * 1000L
        
        // 成长阶段年龄边界
        val GROWTH_STAGES = mapOf(
            GrowthStage.CHILD to 0..12,
            GrowthStage.TEENAGER to 13..17,
            GrowthStage.YOUNG_ADULT to 18..40,
            GrowthStage.MIDDLE_AGED to 41..60,
            GrowthStage.ELDERLY to 61..100
        )
    }
    
    /**
     * 启动世界时间
     */
    fun startWorld() {
        if (_isRunning.value) return
        
        _isRunning.value = true
        
        // 启动时间流逝Job
        timeJob = CoroutineScope(Dispatchers.Default).launch {
            while (_isRunning.value) {
                // 每秒更新一次世界时间
                val multiplier = _timeMultiplier.value
                val timeToAdd = 1000L * multiplier // 每秒增加multiplier秒
                
                _worldTime.value += timeToAdd
                
                // 检查是否需要执行每日任务
                checkAndExecuteDailyTasks()
                
                delay(1000) // 现实1秒
            }
        }
        
        // 记录日志
        CoroutineScope(Dispatchers.IO).launch {
            apiConfigRepository.addLog(
                characterId = null,
                characterName = null,
                logType = com.ai.socialworld.domain.repository.LogType.SYSTEM,
                content = "世界启动，时间倍速: ${_timeMultiplier.value}x"
            )
        }
    }
    
    /**
     * 暂停世界时间
     */
    fun pauseWorld() {
        _isRunning.value = false
        timeJob?.cancel()
        timeJob = null
        
        CoroutineScope(Dispatchers.IO).launch {
            apiConfigRepository.addLog(
                characterId = null,
                characterName = null,
                logType = com.ai.socialworld.domain.repository.LogType.SYSTEM,
                content = "世界暂停"
            )
        }
    }
    
    /**
     * 设置时间倍速
     */
    fun setTimeMultiplier(multiplier: Int) {
        val newMultiplier = multiplier.coerceIn(MIN_MULTIPLIER, MAX_MULTIPLIER)
        _timeMultiplier.value = newMultiplier
        
        // 保存到设置
        CoroutineScope(Dispatchers.IO).launch {
            val settings = apiConfigRepository.getWorldSettings()
            if (settings != null) {
                apiConfigRepository.saveWorldSettings(settings.copy(timeMultiplier = newMultiplier))
            }
        }
    }
    
    /**
     * 检查并执行每日任务
     */
    private suspend fun checkAndExecuteDailyTasks() {
        val currentTime = _worldTime.value
        val currentDay = currentTime / DAY_IN_MILLIS
        val lastDay = lastDailyTaskTime / DAY_IN_MILLIS
        
        // 如果是新的一天（世界时间）
        if (currentDay > lastDay && currentTime - lastDailyTaskTime >= DAY_IN_MILLIS / _timeMultiplier.value) {
            executeDailyTasks()
            lastDailyTaskTime = currentTime
        }
    }
    
    /**
     * 执行每日任务
     */
    private suspend fun executeDailyTasks() = withContext(Dispatchers.IO) {
        apiConfigRepository.addLog(
            characterId = null,
            characterName = null,
            logType = com.ai.socialworld.domain.repository.LogType.SYSTEM,
            content = "===== 新的一天开始 ====="
        )
        
        // 1. 每日资金消耗
        val consumptionCount = economyService.performDailyConsumption()
        apiConfigRepository.addLog(
            characterId = null,
            characterName = null,
            logType = com.ai.socialworld.domain.repository.LogType.ECONOMY,
            content = "每日消耗已执行，影响 $consumptionCount 个角色"
        )
        
        // 2. 检查贫困状态
        val povertyAlerts = economyService.checkPovertyStatus()
        povertyAlerts.forEach { alert ->
            when (alert) {
                is PovertyAlert.AutoLoan -> {
                    apiConfigRepository.addLog(
                        characterId = alert.characterId,
                        characterName = alert.characterName,
                        logType = com.ai.socialworld.domain.repository.LogType.ECONOMY,
                        content = "自动贷款: ${alert.amount}"
                    )
                }
                is PovertyAlert.Warning -> {
                    apiConfigRepository.addLog(
                        characterId = alert.characterId,
                        characterName = alert.characterName,
                        logType = com.ai.socialworld.domain.repository.LogType.ECONOMY,
                        content = "贫困警告: ${alert.daysInPoverty}天"
                    )
                }
            }
        }
        
        // 3. 亲密度衰减
        val decayCount = relationshipEngine.performDailyDecay()
        apiConfigRepository.addLog(
            characterId = null,
            characterName = null,
            logType = com.ai.socialworld.domain.repository.LogType.SOCIAL,
            content = "亲密度衰减已执行，影响 $decayCount 对关系"
        )
        
        // 4. 生成次日日程
        val scheduleCount = scheduleEngine.generateAllDailySchedules()
        apiConfigRepository.addLog(
            characterId = null,
            characterName = null,
            logType = com.ai.socialworld.domain.repository.LogType.SYSTEM,
            content = "日程生成完成，影响 $scheduleCount 个角色"
        )
        
        // 5. 年龄增长（根据时间倍速计算）
        val characters = characterRepository.getAllCharactersSync()
        characters.forEach { character ->
            // 每30倍速现实天 = 角色+1月
            // 简化：每30天检查一次年龄增长
            if (_timeMultiplier.value >= 30) {
                // 高倍速下每天增加年龄
                val ageIncrement = _timeMultiplier.value / 30
                val newAge = character.age + ageIncrement
                
                // 检查成长阶段变化
                val oldStage = getGrowthStage(character.age)
                val newStage = getGrowthStage(newAge)
                
                if (oldStage != newStage) {
                    apiConfigRepository.addLog(
                        characterId = character.id.toString(),
                        characterName = character.name,
                        logType = com.ai.socialworld.domain.repository.LogType.SYSTEM,
                        content = "成长阶段变化: $oldStage -> $newStage"
                    )
                    
                    // TODO: 触发头像更新
                }
                
                characterRepository.updateCharacter(character.copy(age = newAge))
            }
        }
        
        apiConfigRepository.addLog(
            characterId = null,
            characterName = null,
            logType = com.ai.socialworld.domain.repository.LogType.SYSTEM,
            content = "===== 每日任务完成 ====="
        )
    }
    
    /**
     * 获取成长阶段
     */
    fun getGrowthStage(age: Int): GrowthStage {
        return GROWTH_STAGES.entries.find { (_, range) ->
            age in range
        }?.key ?: GrowthStage.YOUNG_ADULT
    }
    
    /**
     * 获取格式化的世界时间
     */
    fun getFormattedWorldTime(): String {
        val time = _worldTime.value
        val calendar = java.util.Calendar.getInstance()
        calendar.timeInMillis = time
        
        val year = calendar.get(java.util.Calendar.YEAR)
        val month = calendar.get(java.util.Calendar.MONTH) + 1
        val day = calendar.get(java.util.Calendar.DAY_OF_MONTH)
        val hour = calendar.get(java.util.Calendar.HOUR_OF_DAY)
        val minute = calendar.get(java.util.Calendar.MINUTE)
        
        return String.format("%04d-%02d-%02d %02d:%02d", year, month, day, hour, minute)
    }
    
    /**
     * 获取世界状态摘要
     */
    suspend fun getWorldStatus(): WorldStatus = withContext(Dispatchers.IO) {
        val characters = characterRepository.getAllCharactersSync()
        val settings = apiConfigRepository.getWorldSettings()
        
        WorldStatus(
            worldTime = _worldTime.value,
            formattedTime = getFormattedWorldTime(),
            timeMultiplier = _timeMultiplier.value,
            isRunning = _isRunning.value,
            totalCharacters = characters.size,
            totalMoney = characters.sumOf { it.money },
            averageAge = if (characters.isNotEmpty()) characters.map { it.age }.average().toInt() else 0
        )
    }
    
    /**
     * 手动触发每日任务（调试用）
     */
    suspend fun triggerDailyTasksManually() {
        executeDailyTasks()
    }
    
    /**
     * 重置世界时间到当前
     */
    fun resetWorldTime() {
        _worldTime.value = System.currentTimeMillis()
    }
    
    /**
     * 设置世界时间
     */
    fun setWorldTime(timestamp: Long) {
        _worldTime.value = timestamp
    }
}

// ==================== 数据类 ====================

data class WorldStatus(
    val worldTime: Long,
    val formattedTime: String,
    val timeMultiplier: Int,
    val isRunning: Boolean,
    val totalCharacters: Int,
    val totalMoney: Int,
    val averageAge: Int
)
