package com.ai.socialworld.domain.usecase.memory

import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.data.model.MemoryType
import com.ai.socialworld.domain.engine.MemoryEngine
import com.ai.socialworld.domain.usecase.BaseUseCase
import javax.inject.Inject

/**
 * 保存记忆用例
 */
class SaveMemoryUseCase @Inject constructor(
    private val memoryEngine: MemoryEngine
) : BaseUseCase<SaveMemoryUseCase.Params, Result<String>>() {

    data class Params(
        val characterId: String,
        val content: String,
        val type: MemoryType = MemoryType.CONVERSATION,
        val importance: Float = 0.5f,
        val relatedEntities: List<String> = emptyList()
    )

    override suspend fun execute(params: Params): Result<String> {
        return memoryEngine.storeMemory(
            characterId = params.characterId,
            content = params.content,
            type = params.type,
            importance = params.importance,
            relatedEntities = params.relatedEntities
        )
    }
}
