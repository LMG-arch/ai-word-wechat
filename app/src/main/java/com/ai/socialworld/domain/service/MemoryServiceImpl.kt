package com.ai.socialworld.domain.service

import javax.inject.Inject

class MemoryServiceImpl @Inject constructor(
    private val timeDecayService: TimeDecayService
) : MemoryService {
    override suspend fun processMemory(content: String, importance: Float): String {
        val decay = timeDecayService.calculateDecay(importance, System.currentTimeMillis())
        return "Processed: $content with decay $decay"
    }
}
