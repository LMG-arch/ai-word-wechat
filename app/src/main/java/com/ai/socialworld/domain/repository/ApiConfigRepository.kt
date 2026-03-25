package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.ApiConfig
import com.ai.socialworld.data.model.ApiType
import com.ai.socialworld.data.model.LogType
import com.ai.socialworld.data.model.SystemLog
import com.ai.socialworld.data.model.WorldSettings
import kotlinx.coroutines.flow.Flow

/**
 * API配置仓库接口
 */
interface ApiConfigRepository {
    
    /**
     * 获取所有API配置
     */
    fun getAllApiConfigs(): Flow<List<ApiConfig>>
    
    /**
     * 获取指定类型的API配置
     */
    fun getApiConfigsByType(apiType: ApiType): Flow<List<ApiConfig>>
    
    /**
     * 获取启用的API配置
     */
    suspend fun getEnabledApiConfigs(apiType: ApiType): List<ApiConfig>
    
    /**
     * 获取主API配置
     */
    suspend fun getPrimaryApiConfig(apiType: ApiType): ApiConfig?
    
    /**
     * 保存API配置
     */
    suspend fun saveApiConfig(config: ApiConfig)
    
    /**
     * 删除API配置
     */
    suspend fun deleteApiConfig(config: ApiConfig)
    
    /**
     * 设置主配置
     */
    suspend fun setPrimaryConfig(apiType: ApiType, configId: String)
    
    /**
     * 获取世界设置
     */
    suspend fun getWorldSettings(): WorldSettings?
    
    /**
     * 保存世界设置
     */
    suspend fun saveWorldSettings(settings: WorldSettings)
    
    /**
     * 添加系统日志
     */
    suspend fun addLog(characterId: String?, characterName: String?, logType: LogType, content: String)
    
    /**
     * 获取最近日志
     */
    fun getRecentLogs(limit: Int): Flow<List<SystemLog>>
}
