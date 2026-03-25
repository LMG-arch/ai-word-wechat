package com.ai.socialworld.domain.usecase.memory

import com.ai.socialworld.domain.engine.CharacterState
import com.ai.socialworld.domain.engine.MemoryEngine
import com.ai.socialworld.domain.usecase.BaseUseCase
import java.time.Instant
import javax.inject.Inject

/**
 * 获取历史状态用例
 */
class GetHistoryStateUseCase @Inject constructor(
    private val memoryEngine: MemoryEngine
) : BaseUseCase<GetHistoryStateUseCase.Params, CharacterState?>() {

    data class Params(
        val characterId: String,
        val timestamp: Instant
    )

    override suspend fun execute(params: Params): CharacterState? {
        return memoryEngine.getStateAtTime(
            characterId = params.characterId,
            timestamp = params.timestamp
        )
    }
}
