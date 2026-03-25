package com.ai.socialworld.data.remote

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

/**
 * 图像生成API接口
 * 支持多种图像生成服务：OpenAI DALL-E, Stability AI, Midjourney API等
 */
interface ImageGenerationApi {
    
    /**
     * OpenAI DALL-E 图像生成
     */
    @POST("v1/images/generations")
    suspend fun generateImageOpenAI(
        @Header("Authorization") authorization: String,
        @Body request: OpenAIImageRequest
    ): Response<OpenAIImageResponse>
    
    /**
     * Stability AI 图像生成
     */
    @POST("v1/generation/{engine_id}/text-to-image")
    suspend fun generateImageStability(
        @Path("engine_id") engineId: String,
        @Header("Authorization") authorization: String,
        @Header("Content-Type") contentType: String = "application/json",
        @Body request: StabilityAIRequest
    ): Response<StabilityAIResponse>
    
    /**
     * 通用图像生成接口
     */
    @POST
    suspend fun generateImage(
        @Url url: String,
        @HeaderMap headers: Map<String, String>,
        @Body request: Map<String, Any>
    ): Response<Map<String, Any>>
}

/**
 * OpenAI图像生成请求
 */
data class OpenAIImageRequest(
    val model: String = "dall-e-3",
    val prompt: String,
    val n: Int = 1,
    val size: String = "1024x1024",
    val quality: String = "standard",  // standard 或 hd
    val style: String = "vivid"        // vivid 或 natural
)

/**
 * OpenAI图像生成响应
 */
data class OpenAIImageResponse(
    val created: Long,
    val data: List<OpenAIImageData>
)

data class OpenAIImageData(
    val url: String?,
    val b64_json: String?,
    val revised_prompt: String?
)

/**
 * Stability AI图像生成请求
 */
data class StabilityAIRequest(
    val text_prompts: List<TextPrompt>,
    val cfg_scale: Float = 7.0f,
    val height: Int = 1024,
    val width: Int = 1024,
    val samples: Int = 1,
    val steps: Int = 30,
    val style_preset: String? = null  // 3d-model, anime, cinematic, digital-art等
)

data class TextPrompt(
    val text: String,
    val weight: Float = 1.0f
)

/**
 * Stability AI图像生成响应
 */
data class StabilityAIResponse(
    val artifacts: List<Artifact>
)

data class Artifact(
    val base64: String,
    val seed: Long,
    val finishReason: String
)

/**
 * 图像生成结果
 */
sealed class ImageGenerationResult {
    data class Success(
        val imageUrl: String? = null,
        val base64Image: String? = null,
        val revisedPrompt: String? = null
    ) : ImageGenerationResult()
    
    data class Error(
        val message: String,
        val code: Int? = null
    ) : ImageGenerationResult()
}
