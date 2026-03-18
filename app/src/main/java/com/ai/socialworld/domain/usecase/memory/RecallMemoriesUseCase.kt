package com.ai.socialworld.domain.usecase.memory

import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.domain.usecase.BaseUseCase
import com.ai.socialworld.domain.repository.MemoryRepository
import javax.inject.Inject

class RecallMemoriesUseCase @Inject constructor(
    private val memoryRepository: MemoryRepository
) : BaseUseCase<String, Result<List<Memory>>>() {

    override suspend fun execute(params: String): Result<List<Memory>> {
        return memoryRepository.getMemoriesByCharacterId(params)
    }
}
