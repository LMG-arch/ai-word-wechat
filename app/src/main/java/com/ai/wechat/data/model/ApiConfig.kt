package com.ai.wechat.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * API 配置实体
 * 支持多服务商配置和备用机制
 */
@Entity(tableName = "api_configs")
data class ApiConfig(
    @PrimaryKey
    val id: String,
    val name: String,
    val type: ApiType,
    val provider: String,
    val apiUrl: String,
    val apiKey: String,
    val modelName: String,
    val isEnabled: Boolean = true,
    val priority: Int = 0,
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
)

/**
 * API 类型
 */
enum class ApiType {
    LLM,        // 语言模型
    IMAGE,      // 图像模型
    VECTOR,     // 向量模型
    RERANK      // 重排模型
}

/**
 * API 服务商
 */
enum class ApiProvider(val displayName: String) {
    OPENAI("OpenAI"),
    AZURE("Azure"),
    BAIDU("百度文心"),
    ALIYUN("阿里云"),
    TENCENT("腾讯混元"),
    STABILITY("Stability AI"),
    MIDJOURNEY("Midjourney"),
    LOCAL("本地部署")
}
