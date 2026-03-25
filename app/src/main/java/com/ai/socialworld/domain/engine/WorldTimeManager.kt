package com.ai.socialworld.domain.engine

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneId
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 世界时间管理器
 * 支持时间倍速（1-30倍）
 */
@Singleton
class WorldTimeManager @Inject constructor() {
    
    private val _timeSpeed = MutableStateFlow(1) // 1-30倍速
    val timeSpeed: StateFlow<Int> = _timeSpeed
    
    private val _worldTime = MutableStateFlow(Instant.now())
    val worldTime: StateFlow<Instant> = _worldTime
    
    private var timeUpdateJob: Job? = null
    private val scope = CoroutineScope(kotlinx.coroutines.Dispatchers.Default)
    
    init {
        startTimeLoop()
    }
    
    /**
     * 设置时间倍速
     */
    fun setTimeSpeed(speed: Int) {
        _timeSpeed.value = speed.coerceIn(1, 30)
    }
    
    /**
     * 获取当前世界时间
     */
    fun getCurrentWorldTime(): Instant = _worldTime.value
    
    /**
     * 获取世界时间（LocalDateTime）
     */
    fun getCurrentWorldLocalTime(): LocalDateTime {
        return LocalDateTime.ofInstant(_worldTime.value, ZoneId.systemDefault())
    }
    
    /**
     * 启动时间循环
     */
    private fun startTimeLoop() {
        timeUpdateJob?.cancel()
        timeUpdateJob = scope.launch {
            while (true) {
                val speed = _timeSpeed.value
                // 每秒更新一次世界时间
                // 速度越快，时间流逝越快
                val elapsedMillis = 1000L * speed // 每秒实际流逝多少毫秒的世界时间
                _worldTime.value = _worldTime.value.plusMillis(elapsedMillis)
                delay(1000) // 每秒更新一次
            }
        }
    }
    
    /**
     * 计算年龄增长
     * 在30倍速下，现实1天 = 角色增长1个月
     */
    fun calculateAgeGrowth(realDays: Int, timeSpeed: Int): Int {
        // 现实天数 * 时间倍速 / 30 = 角色增长的月数
        // 角色增长的月数 / 12 = 增长的年数（向下取整）
        val months = (realDays * timeSpeed) / 30
        return months / 12
    }
    
    /**
     * 格式化世界时间显示
     */
    fun formatWorldTime(): String {
        val time = getCurrentWorldLocalTime()
        return "${time.year}年${time.monthValue}月${time.dayOfMonth}日 ${time.hour}:${time.minute.toString().padStart(2, '0')}"
    }
    
    /**
     * 获取时间速度描述
     */
    fun getTimeSpeedDescription(): String {
        return when (_timeSpeed.value) {
            1 -> "现实时间"
            in 2..10 -> "快速 (${_timeSpeed.value}x)"
            in 11..20 -> "超快 (${_timeSpeed.value}x)"
            else -> "极速 (${_timeSpeed.value}x)"
        }
    }
}
