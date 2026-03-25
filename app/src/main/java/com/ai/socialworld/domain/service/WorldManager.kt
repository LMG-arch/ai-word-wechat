package com.ai.socialworld.domain.service

import com.ai.socialworld.util.Constants
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 世界管理器
 * 统一管理所有定时任务和核心服务
 */
@Singleton
class WorldManager @Inject constructor(
    private val worldTimeManager: WorldTimeManager,
    private val economyService: EconomyService,
    private val relationshipEngine: RelationshipEngine,
    private val scheduleEngine: ScheduleEngine,
    private val taskGeneratorService: TaskGeneratorService,
    private val characterAutonomyService: CharacterAutonomyService,
    private val mapService: MapService,
    private val logService: LogService,
    private val characterRepository: com.ai.socialworld.domain.repository.CharacterRepository
) {
    
    private val _isRunning = MutableStateFlow(false)
    val isRunning: StateFlow<Boolean> = _isRunning
    
    private var worldJob: Job? = null
    private var lastDailyTaskTime = 0L
    
    /**
     * 启动世界
     */
    fun startWorld() {
        if (_isRunning.value) return
        
        _isRunning.value = true
        worldTimeManager.startWorld()
        
        // 启动主循环
        worldJob = CoroutineScope(Dispatchers.Default).launch {
            while (_isRunning.value) {
                // 每秒检查一次
                checkAndRunTasks()
                delay(1000)
            }
        }
        
        CoroutineScope(Dispatchers.IO).launch {
            logService.logSystem("世界已启动")
        }
    }
    
    /**
     * 暂停世界
     */
    fun pauseWorld() {
        _isRunning.value = false
        worldTimeManager.pauseWorld()
        worldJob?.cancel()
        worldJob = null
        
        CoroutineScope(Dispatchers.IO).launch {
            logService.logSystem("世界已暂停")
        }
    }
    
    /**
     * 检查并运行定时任务
     */
    private suspend fun checkAndRunTasks() {
        val worldTime = worldTimeManager.worldTime.value
        val timeMultiplier = worldTimeManager.timeMultiplier.value
        
        // 检查是否需要执行每日任务
        // 简化：使用现实时间，每天执行一次
        val realTime = System.currentTimeMillis()
        val realDay = realTime / Constants.WorldTime.DAY_IN_MILLIS
        val lastDay = lastDailyTaskTime / Constants.WorldTime.DAY_IN_MILLIS
        
        if (realDay > lastDay) {
            runDailyTasks()
            lastDailyTaskTime = realTime
        }
    }
    
    /**
     * 执行每日任务
     */
    private suspend fun runDailyTasks() = withContext(Dispatchers.IO) {
        logService.logSystem("===== 开始执行每日任务 =====")
        
        try {
            // 1. 每日资金消耗
            val consumptionCount = economyService.performDailyConsumption()
            logService.logSystem("每日消耗完成: $consumptionCount 个角色")
            
            // 2. 检查贫困状态
            val povertyAlerts = economyService.checkPovertyStatus()
            logService.logSystem("贫困检查完成: ${povertyAlerts.size} 个警报")
            
            // 3. 亲密度衰减
            val decayCount = relationshipEngine.performDailyDecay()
            logService.logSystem("亲密度衰减完成: $decayCount 对关系")
            
            // 4. 生成日程
            val scheduleCount = scheduleEngine.generateAllDailySchedules()
            logService.logSystem("日程生成完成: $scheduleCount 个角色")
            
            // 5. 生成每日任务
            val tasks = taskGeneratorService.generateDailyTasks()
            logService.logSystem("任务生成完成: ${tasks.size} 个任务")
            
            // 6. 更新角色位置
            val characters = characterRepository.getAllCharactersSync()
            characters.forEach { character ->
                mapService.updateLocationBySchedule(character.id.toString())
            }
            logService.logSystem("位置更新完成: ${characters.size} 个角色")
            
            // 7. 检查角色自主更新
            characters.forEach { character ->
                characterAutonomyService.checkAndUpdateAutonomy(character.id.toString())
            }
            
            logService.logSystem("===== 每日任务完成 =====")
            
        } catch (e: Exception) {
            logService.logSystem("每日任务执行出错: ${e.message}")
        }
    }
    
    /**
     * 手动触发每日任务
     */
    suspend fun triggerDailyTasks() {
        runDailyTasks()
    }
    
    /**
     * 获取世界状态
     */
    suspend fun getWorldStatus(): WorldStatusSummary = withContext(Dispatchers.IO) {
        val characters = characterRepository.getAllCharactersSync()
        val worldStatus = worldTimeManager.getWorldStatus()
        val mapStats = mapService.getMapStats()
        
        WorldStatusSummary(
            isRunning = _isRunning.value,
            worldTime = worldStatus.worldTime,
            formattedTime = worldStatus.formattedTime,
            timeMultiplier = worldStatus.timeMultiplier,
            totalCharacters = characters.size,
            totalMoney = characters.sumOf { it.money },
            averageAge = if (characters.isNotEmpty()) characters.map { it.age }.average().toInt() else 0,
            activeCharacters = mapStats.activeCharacters,
            activeEncounters = mapStats.activeEncounters
        )
    }
    
    /**
     * 设置时间倍速
     */
    fun setTimeMultiplier(multiplier: Int) {
        worldTimeManager.setTimeMultiplier(multiplier)
    }
    
    /**
     * 获取时间倍速
     */
    fun getTimeMultiplier(): Int {
        return worldTimeManager.timeMultiplier.value
    }
}

/**
 * 世界状态摘要
 */
data class WorldStatusSummary(
    val isRunning: Boolean,
    val worldTime: Long,
    val formattedTime: String,
    val timeMultiplier: Int,
    val totalCharacters: Int,
    val totalMoney: Int,
    val averageAge: Int,
    val activeCharacters: Int,
    val activeEncounters: Int
)
