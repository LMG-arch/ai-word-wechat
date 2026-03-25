package com.ai.socialworld.data.repository

import com.ai.socialworld.data.local.ApiConfigDao
import com.ai.socialworld.data.model.ApiConfig
import com.ai.socialworld.data.model.ApiType
import com.ai.socialworld.data.model.LogType
import com.ai.socialworld.data.model.SystemLog
import com.ai.socialworld.data.model.WorldSettings
import com.ai.socialworld.domain.repository.ApiConfigRepository
import kotlinx.coroutines.flow.Flow
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * API配置仓库实现
 */
@Singleton
class ApiConfigRepositoryImpl @Inject constructor(
    private val apiConfigDao: ApiConfigDao
) : ApiConfigRepository {
    
    override fun getAllApiConfigs(): Flow<List<ApiConfig>> {
        return apiConfigDao.getAllApiConfigs()
    }
    
    override fun getApiConfigsByType(apiType: ApiType): Flow<List<ApiConfig>> {
        return apiConfigDao.getApiConfigsByType(apiType)
    }
    
    override suspend fun getEnabledApiConfigs(apiType: ApiType): List<ApiConfig> {
        return apiConfigDao.getEnabledApiConfigsByType(apiType)
    }
    
    override suspend fun getPrimaryApiConfig(apiType: ApiType): ApiConfig? {
        return apiConfigDao.getPrimaryApiConfig(apiType)
    }
    
    override suspend fun saveApiConfig(config: ApiConfig) {
        apiConfigDao.insert(config)
    }
    
    override suspend fun deleteApiConfig(config: ApiConfig) {
        apiConfigDao.delete(config)
    }
    
    override suspend fun setPrimaryConfig(apiType: ApiType, configId: String) {
        // 先取消该类型的所有主配置
        apiConfigDao.clearPrimaryByType(apiType)
        // 设置新的主配置
        apiConfigDao.setPrimary(configId)
    }
    
    override suspend fun getWorldSettings(): WorldSettings? {
        return apiConfigDao.getWorldSettings()
    }
    
    override suspend fun saveWorldSettings(settings: WorldSettings) {
        apiConfigDao.insertWorldSettings(settings)
    }
    
    override suspend fun addLog(
        characterId: String?,
        characterName: String?,
        logType: LogType,
        content: String
    ) {
        val log = SystemLog(
            id = UUID.randomUUID().toString(),
            timestamp = System.currentTimeMillis(),
            characterId = characterId,
            characterName = characterName,
            logType = logType,
            content = content
        )
        apiConfigDao.insertLog(log)
    }
    
    override fun getRecentLogs(limit: Int): Flow<List<SystemLog>> {
        return apiConfigDao.getRecentLogs(limit)
    }
}
