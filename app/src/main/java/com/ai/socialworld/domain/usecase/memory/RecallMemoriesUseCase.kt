package com.ai.socialworld.domain.usecase.memory

import com.ai.socialworld.data.model.MemoryRecallResult
import com.ai.socialworld.data.model.TimeRange
import com.ai.socialworld.domain.engine.MemoryEngine
import com.ai.socialworld.domain.usecase.BaseUseCase
import javax.inject.Inject

/**
 * 召回记忆用例
 */
class RecallMemoriesUseCase @Inject constructor(
    private val memoryEngine: MemoryEngine
) : BaseUseCase<RecallMemoriesUseCase.Params, List<MemoryRecallResult>>() {

    data class Params(
        val characterId: String,
        val query: String,
        val timeRange: TimeRange? = null,
        val topK: Int = 10
    )

    override suspend fun execute(params: Params): List<MemoryRecallResult> {
        return memoryEngine.recallMemories(
            characterId = params.characterId,
            query = params.query,
            timeRange = params.timeRange,
            topK = params.topK
        )
    }
}
