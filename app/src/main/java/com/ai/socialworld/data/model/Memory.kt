package com.ai.socialworld.data.model

data class Memory(
    val id: Long,
    val characterId: Long,
    val content: String,
    val type: MemoryType,
    val createdAt: Long
)

enum class MemoryType {
    SHORT_TERM,
    LONG_TERM,
    EPISODIC,
    SEMANTIC
}
