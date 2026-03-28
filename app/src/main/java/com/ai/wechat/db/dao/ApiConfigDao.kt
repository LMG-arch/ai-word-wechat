package com.ai.wechat.db.dao

import androidx.room.*
import com.ai.wechat.data.model.ApiConfig
import com.ai.wechat.data.model.ApiType
import kotlinx.coroutines.flow.Flow

/**
 * API 配置数据访问对象
 */
@Dao
interface ApiConfigDao {

    @Query("SELECT * FROM api_configs WHERE isEnabled = 1 ORDER BY priority")
    fun getAllEnabledConfigs(): Flow<List<ApiConfig>>

    @Query("SELECT * FROM api_configs WHERE type = :type AND isEnabled = 1 ORDER BY priority")
    fun getConfigsByType(type: ApiType): Flow<List<ApiConfig>>

    @Query("SELECT * FROM api_configs WHERE id = :id")
    suspend fun getConfigById(id: String): ApiConfig?

    @Query("SELECT * FROM api_configs WHERE type = :type ORDER BY priority LIMIT 1")
    suspend fun getPrimaryConfigByType(type: ApiType): ApiConfig?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertConfig(config: ApiConfig)

    @Update
    suspend fun updateConfig(config: ApiConfig)

    @Delete
    suspend fun deleteConfig(config: ApiConfig)

    @Query("UPDATE api_configs SET isEnabled = :enabled WHERE id = :id")
    suspend fun toggleConfig(id: String, enabled: Boolean)

    @Query("SELECT * FROM api_configs WHERE type = :type ORDER BY priority")
    suspend fun getAllConfigsByType(type: ApiType): List<ApiConfig>
}
