package com.ai.socialworld.domain.service

import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.exp

/**
 * 时间衰减服务
 * 统一的时间衰减计算服务
 */
@Singleton
class TimeDecayService @Inject constructor() {
    
    /**
     * 计算时间衰减权重
     * 指数衰减：weight = exp(-hours_since / 72)，半衰期约2.5天
     */
    fun calculateDecayWeight(timestamp: Long, currentTime: Long = System.currentTimeMillis()): Double {
        val hoursDiff = (currentTime - timestamp) / (1000 * 60 * 60)
        return exp(-hoursDiff / 72.0)
    }
    
    /**
     * 计算反思记忆的衰减权重（失败教训衰减更慢）
     * 半衰期7天
     */
    fun calculateReflectionDecayWeight(timestamp: Long, isFailure: Boolean, currentTime: Long = System.currentTimeMillis()): Double {
        val hoursDiff = (currentTime - timestamp) / (1000 * 60 * 60)
        val halfLife = if (isFailure) 168.0 else 72.0 // 7天 vs 2.5天
        return exp(-hoursDiff / halfLife)
    }
    
    /**
     * 旧版兼容方法
     */
    @Deprecated("Use calculateDecayWeight instead")
    fun calculateDecay(importance: Float, timeElapsed: Long): Float {
        val decayFactor = 0.95f
        return importance * Math.pow(decayFactor.toDouble(), timeElapsed.toDouble()).toFloat()
    }
}
