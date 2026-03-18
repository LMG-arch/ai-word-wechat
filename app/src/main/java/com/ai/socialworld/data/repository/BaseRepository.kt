package com.ai.socialworld.data.repository

interface BaseRepository {
    suspend fun <T> execute(operation: suspend () -> Result<T>): Result<T> {
        return try {
            operation()
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
