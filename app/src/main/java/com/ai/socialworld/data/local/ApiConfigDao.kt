package com.ai.socialworld.data.local

import androidx.room.*
import com.ai.socialworld.data.model.ApiConfig
import com.ai.socialworld.data.model.ApiType
import com.ai.socialworld.data.model.LogType
import com.ai.socialworld.data.model.SystemLog
import com.ai.socialworld.data.model.WorldSettings
import kotlinx.coroutines.flow.Flow

/**
 * API配置DAO
 */
@Dao
interface ApiConfigDao {
    
    // ==================== API配置 ====================
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(config: ApiConfig)
    
    @Update
    suspend fun update(config: ApiConfig)
    
    @Delete
    suspend fun delete(config: ApiConfig)
    
    @Query("SELECT * FROM api_configs ORDER BY apiType, priority")
    fun getAllApiConfigs(): Flow<List<ApiConfig>>
    
    @Query("SELECT * FROM api_configs WHERE apiType = :apiType ORDER BY priority")
    fun getApiConfigsByType(apiType: ApiType): Flow<List<ApiConfig>>
    
    @Query("SELECT * FROM api_configs WHERE apiType = :apiType AND isEnabled = 1 ORDER BY priority")
    suspend fun getEnabledApiConfigsByType(apiType: ApiType): List<ApiConfig>
    
    @Query("SELECT * FROM api_configs WHERE apiType = :apiType AND isPrimary = 1 LIMIT 1")
    suspend fun getPrimaryApiConfig(apiType: ApiType): ApiConfig?
    
    @Query("UPDATE api_configs SET isPrimary = 0 WHERE apiType = :apiType")
    suspend fun clearPrimaryByType(apiType: ApiType)
    
    @Query("UPDATE api_configs SET isPrimary = 1 WHERE id = :configId")
    suspend fun setPrimary(configId: String)
    
    @Query("DELETE FROM api_configs WHERE id = :configId")
    suspend fun deleteById(configId: String)
    
    // ==================== 世界设置 ====================
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertWorldSettings(settings: WorldSettings)
    
    @Query("SELECT * FROM world_settings LIMIT 1")
    suspend fun getWorldSettings(): WorldSettings?
    
    // ==================== 系统日志 ====================
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertLog(log: SystemLog)
    
    @Query("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT :limit")
    fun getRecentLogs(limit: Int): Flow<List<SystemLog>>
    
    @Query("SELECT * FROM system_logs WHERE characterId = :characterId ORDER BY timestamp DESC")
    fun getLogsByCharacter(characterId: String): Flow<List<SystemLog>>
    
    @Query("SELECT * FROM system_logs WHERE logType = :logType ORDER BY timestamp DESC LIMIT :limit")
    fun getLogsByType(logType: LogType, limit: Int): Flow<List<SystemLog>>
    
    @Query("DELETE FROM system_logs WHERE timestamp < :before")
    suspend fun deleteOldLogs(before: Long)
}
