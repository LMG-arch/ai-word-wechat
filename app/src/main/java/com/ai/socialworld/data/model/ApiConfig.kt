package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * API配置类型
 */
enum class ApiType {
    LANGUAGE,    // 语言模型
    IMAGE,       // 图像模型
    VECTOR,      // 向量模型
    RERANK       // 重排模型
}

/**
 * API配置
 */
@Entity(tableName = "api_configs")
data class ApiConfig(
    @PrimaryKey
    val id: String,
    val name: String,                  // 配置名称
    val apiType: ApiType,             // API类型
    val apiUrl: String,               // API地址
    val apiKey: String,               // API密钥
    val modelName: String,            // 模型名称
    val isPrimary: Boolean = true,    // 是否为主配置
    val priority: Int = 0,            // 优先级 (备用时使用)
    val isEnabled: Boolean = true,    // 是否启用
    val extraParams: String = "{}"    // 额外参数 JSON
)

/**
 * 世界设置
 */
@Entity(tableName = "world_settings")
data class WorldSettings(
    @PrimaryKey
    val id: String = "default",
    val timeMultiplier: Int = 1,      // 时间倍速 (1-30)
    val enableDeath: Boolean = false,  // 是否允许死亡
    val maxAge: Int = 80,            // 最大寿命
    val dailyConsumption: Int = 5,    // 每日消耗
    val initialMoney: Int = 50,       // 初始资金
    val loanAmount: Int = 100,        // 贷款额度
    val loanInterestRate: Float = 0.01f // 日息
)

/**
 * 系统日志
 */
@Entity(tableName = "system_logs")
data class SystemLog(
    @PrimaryKey
    val id: String,
    val timestamp: Long = System.currentTimeMillis(),
    val characterId: String?,         // 相关角色
    val characterName: String?,        // 角色名称
    val logType: LogType,             // 日志类型
    val content: String               // 日志内容
)

/**
 * 日志类型
 */
enum class LogType {
    TASK,       // 任务相关
    SOCIAL,     // 社交相关
    MEMORY,     // 记忆相关
    ECONOMY,    // 经济相关
    SYSTEM      // 系统相关
}
