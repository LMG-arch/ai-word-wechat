package com.ai.socialworld.data.model

data class Memory(
    val id: String,
    val characterId: String,
    val content: String,
    val timestamp: Long,
    val importance: Float = 0.5f,
    val decayFactor: Float = 0.95f
)
