﻿﻿﻿package com.ai.socialworld.domain.usecase

import kotlinx.coroutines.flow.Flow

abstract class BaseUseCase<in Params, out T> {
    abstract suspend fun execute(params: Params): T
}

abstract class BaseFlowUseCase<in Params, out T> {
    abstract fun execute(params: Params): Flow<T>
}

class None
