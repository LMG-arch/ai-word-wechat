package com.ai.socialworld.util

import kotlin.math.sqrt
import kotlin.random.Random

/**
 * 数学工具类
 */
object MathUtils {
    
    /**
     * 计算余弦相似度
     */
    fun cosineSimilarity(vectorA: List<Float>, vectorB: List<Float>): Float {
        if (vectorA.size != vectorB.size || vectorA.isEmpty()) return 0f
        
        var dotProduct = 0f
        var normA = 0f
        var normB = 0f
        
        for (i in vectorA.indices) {
            dotProduct += vectorA[i] * vectorB[i]
            normA += vectorA[i] * vectorA[i]
            normB += vectorB[i] * vectorB[i]
        }
        
        val denominator = sqrt(normA.toDouble()) * sqrt(normB.toDouble())
        return if (denominator > 0) (dotProduct / denominator).toFloat() else 0f
    }
    
    /**
     * 计算欧几里得距离
     */
    fun euclideanDistance(vectorA: List<Float>, vectorB: List<Float>): Float {
        if (vectorA.size != vectorB.size || vectorA.isEmpty()) return Float.MAX_VALUE
        
        var sum = 0f
        for (i in vectorA.indices) {
            val diff = vectorA[i] - vectorB[i]
            sum += diff * diff
        }
        
        return sqrt(sum.toDouble()).toFloat()
    }
    
    /**
     * 指数衰减函数
     * @param hoursSince 经过的小时数
     * @param halfLife 半衰期（小时）
     * @return 衰减后的权重 (0-1)
     */
    fun exponentialDecay(hoursSince: Double, halfLife: Double): Float {
        return kotlin.math.exp(-hoursSince / halfLife).toFloat()
    }
    
    /**
     * 线性插值
     */
    fun lerp(start: Float, end: Float, t: Float): Float {
        return start + (end - start) * t.coerceIn(0f, 1f)
    }
    
    /**
     * 平滑插值
     */
    fun smoothStep(edge0: Float, edge1: Float, x: Float): Float {
        val t = ((x - edge0) / (edge1 - edge0)).coerceIn(0f, 1f)
        return t * t * (3 - 2 * t)
    }
    
    /**
     * 计算两点之间的距离（2D）
     */
    fun distance2D(x1: Double, y1: Double, x2: Double, y2: Double): Double {
        val dx = x2 - x1
        val dy = y2 - y1
        return sqrt(dx * dx + dy * dy)
    }
    
    /**
     * 随机范围
     */
    fun randomInRange(min: Int, max: Int): Int {
        return Random.nextInt(min, max + 1)
    }
    
    fun randomInRange(min: Float, max: Float): Float {
        return Random.nextFloat() * (max - min) + min
    }
    
    /**
     * 高斯分布随机数
     */
    fun gaussianRandom(mean: Float = 0f, stdDev: Float = 1f): Float {
        return (Random.nextGaussian() * stdDev + mean).toFloat()
    }
    
    /**
     * Softmax函数
     */
    fun softmax(values: List<Float>): List<Float> {
        val max = values.maxOrNull() ?: 0f
        val expValues = values.map { kotlin.math.exp((it - max).toDouble()).toFloat() }
        val sum = expValues.sum()
        return expValues.map { it / sum }
    }
    
    /**
     * 归一化
     */
    fun normalize(values: List<Float>): List<Float> {
        val sum = values.sum()
        return if (sum > 0) values.map { it / sum } else values
    }
    
    /**
     * 限制在范围内
     */
    fun <T : Comparable<T>> clamp(value: T, min: T, max: T): T {
        return value.coerceIn(min, max)
    }
}
