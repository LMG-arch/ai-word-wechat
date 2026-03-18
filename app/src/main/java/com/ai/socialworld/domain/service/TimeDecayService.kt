package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.Memory
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.exp

/**
 * 时间衰减服务
 * 基于艾宾浩斯遗忘曲线实现记忆衰减
 */
@Singleton
class TimeDecayService @Inject constructor() {

    companion object {
        private const val DEFAULT_DECAY_RATE = 0.5
        private const val INITIAL_RETENTION = 1.0
    }

    /**
     * 计算记忆保留度
     * 使用指数衰减模型：R(t) = R0 * e^(-λt)
     * @param timeElapsed 经过的时间（小时）
     * @param decayRate 衰减率
     * @return 保留度 (0.0-1.0)
     */
    fun calculateRetention(timeElapsed: Double, decayRate: Double = DEFAULT_DECAY_RATE): Double {
        return INITIAL_RETENTION * exp(-decayRate * timeElapsed)
    }

    /**
     * 计算记忆强度
     * 综合考虑初始重要性、访问次数和时间衰减
     */
    fun calculateMemoryStrength(memory: Memory): Float {
        val timeElapsed = getTimeElapsedInHours(memory.businessCreatedAt)
        val retention = calculateRetention(timeElapsed)
        val accessBonus = calculateAccessBonus(memory.accessCount)
        
        return (memory.importance * retention * (1 + accessBonus)).toFloat()
    }

    /**
     * 计算访问奖励系数
     */
    private fun calculateAccessBonus(accessCount: Int): Double {
        return 1 - exp(-0.1 * accessCount)
    }

    /**
     * 计算经过的小时数
     */
    private fun getTimeElapsedInHours(startTime: java.time.Instant): Double {
        val duration = java.time.Duration.between(startTime, Instant.now())
        return duration.toHours().toDouble()
    }

    /**
     * 判断记忆是否需要强化
     * 当记忆强度低于阈值时返回 true
     */
    fun needsReinforcement(memory: Memory, threshold: Float = 0.3f): Boolean {
        return calculateMemoryStrength(memory) < threshold
    }

    /**
     * 计算最佳复习时间
     * 基于间隔重复理论
     */
    fun calculateOptimalReviewTime(memory: Memory): java.time.Instant {
        val strength = calculateMemoryStrength(memory)
        val hoursUntilReview = when {
            strength > 0.8 -> 24 * 7    // 1 周
            strength > 0.6 -> 24 * 3    // 3 天
            strength > 0.4 -> 24        // 1 天
            else -> 12                  // 12 小时
        }
        return Instant.now().plusSeconds(hoursUntilReview * 3600)
    }
}
