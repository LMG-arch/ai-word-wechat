package com.ai.wechat.network

import com.ai.wechat.data.model.ApiConfig
import com.ai.wechat.data.model.ApiType
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 网络配置管理器
 * 管理 API 密钥和配置
 */
@Singleton
class NetworkConfig @Inject constructor() {
    
    private val configCache = mutableMapOf<ApiType, List<ApiConfig>>()
    
    suspend fun updateConfigs(configs: List<ApiConfig>) {
        configs.groupBy { it.type }.forEach { (type, configList) ->
            configCache[type] = configList
        }
    }
    
    fun getConfigs(type: ApiType): List<ApiConfig> {
        return configCache[type] ?: emptyList()
    }
    
    fun getPrimaryConfig(type: ApiType): ApiConfig? {
        return getConfigs(type).firstOrNull { it.isEnabled }
    }
}

/**
 * AI 服务调用封装
 * 支持备用机制和自动重试
 */
@Singleton
class AiService @Inject constructor(
    private val apiService: AiApiService,
    private val networkConfig: NetworkConfig
) {

    /**
     * 聊天调用（带备用机制）
     */
    suspend fun chat(
        type: ApiType,
        request: ChatRequest
    ): Result<ChatResponse> = withContext(Dispatchers.IO) {
        val configs = networkConfig.getConfigs(type)
        if (configs.isEmpty()) {
            return@withContext Result.failure(Exception("未配置 API"))
        }

        var lastError: Exception? = null
        var retryCount = 0
        val maxRetries = 3

        for (config in configs) {
            if (retryCount >= maxRetries) break
            
            try {
                val response = apiService.chat(
                    url = config.apiUrl,
                    authorization = "Bearer ${config.apiKey}",
                    request = request.copy(model = config.modelName)
                )

                if (response.isSuccessful && response.body()?.error == null) {
                    return@withContext Result.success(response.body()!!)
                } else {
                    lastError = Exception(response.errorBody()?.string() ?: "请求失败")
                    retryCount++
                }
            } catch (e: Exception) {
                lastError = e
                retryCount++
            }
        }

        Result.failure(lastError ?: Exception("所有 API 调用失败"))
    }

    /**
     * 图像生成调用
     */
    suspend fun generateImage(
        request: ImageRequest
    ): Result<ImageResponse> = withContext(Dispatchers.IO) {
        val configs = networkConfig.getConfigs(ApiType.IMAGE)
        if (configs.isEmpty()) {
            return@withContext Result.failure(Exception("未配置图像 API"))
        }

        val config = configs.first { it.isEnabled }
        try {
            val response = apiService.generateImage(
                url = config.apiUrl,
                authorization = "Bearer ${config.apiKey}",
                request = request
            )

            if (response.isSuccessful && response.body()?.error == null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "生成失败"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 向量嵌入调用
     */
    suspend fun embed(
        text: String
    ): Result<List<Float>> = withContext(Dispatchers.IO) {
        val configs = networkConfig.getConfigs(ApiType.VECTOR)
        if (configs.isEmpty()) {
            return@withContext Result.failure(Exception("未配置向量 API"))
        }

        val config = configs.first { it.isEnabled }
        try {
            val response = apiService.embed(
                url = config.apiUrl,
                authorization = "Bearer ${config.apiKey}",
                request = EmbedRequest(model = config.modelName, input = listOf(text))
            )

            if (response.isSuccessful && response.body()?.error == null) {
                val embedding = response.body()?.data?.firstOrNull()?.embedding
                if (embedding != null) {
                    Result.success(embedding)
                } else {
                    Result.failure(Exception("嵌入结果为空"))
                }
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "嵌入失败"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 重排序调用
     */
    suspend fun rerank(
        query: String,
        documents: List<String>,
        topK: Int = 10
    ): Result<List<RerankResult>> = withContext(Dispatchers.IO) {
        val configs = networkConfig.getConfigs(ApiType.RERANK)
        if (configs.isEmpty()) {
            // 如果没有配置重排模型，直接返回原始顺序
            return@withContext Result.success(
                documents.mapIndexed { index, text ->
                    RerankResult(index = index, score = 1.0 - index * 0.1, text = text)
                }.sortedByDescending { it.score }.take(topK)
            )
        }

        val config = configs.first { it.isEnabled }
        try {
            val response = apiService.rerank(
                url = config.apiUrl,
                authorization = "Bearer ${config.apiKey}",
                request = RerankRequest(query = query, documents = documents, topK = topK)
            )

            if (response.isSuccessful && response.body()?.error == null) {
                Result.success(response.body()?.results ?: emptyList())
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "重排失败"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
