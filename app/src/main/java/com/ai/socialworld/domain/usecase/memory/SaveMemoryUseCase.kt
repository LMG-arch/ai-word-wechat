package com.ai.socialworld.domain.usecase.memory

import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.domain.repository.MemoryRepository
import com.ai.socialworld.domain.usecase.BaseUseCase
import javax.inject.Inject

class SaveMemoryUseCase @Inject constructor(
    private val memoryRepository: MemoryRepository
) : BaseUseCase<Memory, Result<Unit>>() {

    override suspend fun execute(params: Memory): Result<Unit> {
        return memoryRepository.saveMemory(params)
    }
}
