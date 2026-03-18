package com.ai.socialworld.domain.service

class TimeDecayService {
    fun calculateDecay(importance: Float, timeElapsed: Long): Float {
        val decayFactor = 0.95f
        return importance * Math.pow(decayFactor.toDouble(), timeElapsed.toDouble()).toFloat()
    }
}
