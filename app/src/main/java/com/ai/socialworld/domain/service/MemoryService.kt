package com.ai.socialworld.domain.service

interface MemoryService {
    suspend fun processMemory(content: String, importance: Float): String
}
