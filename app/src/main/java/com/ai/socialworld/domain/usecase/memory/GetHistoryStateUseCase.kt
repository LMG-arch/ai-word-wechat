package com.ai.socialworld.domain.usecase.memory

import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.domain.usecase.BaseUseCase
import com.ai.socialworld.domain.repository.MemoryRepository
import javax.inject.Inject

data class HistoryStateParams(
    val characterId: String,
    val maxTimestamp: Long? = null
)

data class HistoryState(
    val memories: List<Memory>,
    val totalMemories: Int,
    val latestTimestamp: Long?
)

class GetHistoryStateUseCase @Inject constructor(
    private val memoryRepository: MemoryRepository
) : BaseUseCase<HistoryStateParams, Result<HistoryState>>() {

    override suspend fun execute(params: HistoryStateParams): Result<HistoryState> {
        return try {
            val memoriesResult = memoryRepository.getMemoriesByCharacterId(params.characterId)
            
            memoriesResult.fold(
                onSuccess = { memories ->
                    val filteredMemories = if (params.maxTimestamp != null) {
                        memories.filter { it.timestamp <= params.maxTimestamp }
                    } else {
                        memories
                    }
                    
                    val latestTimestamp = filteredMemories.maxOfOrNull { it.timestamp }
                    
                    Result.success(
                        HistoryState(
                            memories = filteredMemories,
                            totalMemories = filteredMemories.size,
                            latestTimestamp = latestTimestamp
                        )
                    )
                },
                onFailure = { error ->
                    Result.failure(error)
                }
            )
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
