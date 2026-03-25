package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.ApiConfig
import com.ai.socialworld.data.model.ApiType
import com.ai.socialworld.data.remote.*
import com.ai.socialworld.domain.repository.ApiConfigRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 图像生成服务
 * 支持多种图像生成模型，自动切换备用API
 */
@Singleton
class ImageGenerationService @Inject constructor(
    private val apiConfigRepository: ApiConfigRepository
) {
    
    private val retrofitBuilder = Retrofit.Builder()
        .addConverterFactory(GsonConverterFactory.create())
    
    /**
     * 生成角色头像
     * @param characterDescription 角色描述
     * @param age 年龄
     * @param gender 性别
     * @param occupation 职业
     * @param personality 性格
     * @return 图像生成结果
     */
    suspend fun generateCharacterAvatar(
        characterDescription: String,
        age: Int,
        gender: String,
        occupation: String,
        personality: String
    ): ImageGenerationResult = withContext(Dispatchers.IO) {
        
        // 构建提示词
        val prompt = buildAvatarPrompt(
            characterDescription,
            age,
            gender,
            occupation,
            personality
        )
        
        // 获取图像API配置
        val apiConfigs = apiConfigRepository.getEnabledApiConfigs(ApiType.IMAGE)
        
        if (apiConfigs.isEmpty()) {
            return@withContext ImageGenerationResult.Error("未配置图像生成API")
        }
        
        // 按优先级尝试API
        for (config in apiConfigs.sortedBy { it.priority }) {
            val result = tryGenerateImage(config, prompt)
            if (result is ImageGenerationResult.Success) {
                return@withContext result
            }
        }
        
        ImageGenerationResult.Error("所有图像生成API都失败了")
    }
    
    /**
     * 生成任务图像
     * @param taskDescription 任务描述
     * @param requirements 需求
     * @param style 风格要求
     * @return 图像生成结果
     */
    suspend fun generateTaskImage(
        taskDescription: String,
        requirements: String,
        style: String = "epic"
    ): ImageGenerationResult = withContext(Dispatchers.IO) {
        
        // 构建提示词
        val prompt = buildTaskImagePrompt(taskDescription, requirements, style)
        
        // 获取图像API配置
        val apiConfigs = apiConfigRepository.getEnabledApiConfigs(ApiType.IMAGE)
        
        if (apiConfigs.isEmpty()) {
            return@withContext ImageGenerationResult.Error("未配置图像生成API")
        }
        
        // 按优先级尝试API
        for (config in apiConfigs.sortedBy { it.priority }) {
            val result = tryGenerateImage(config, prompt)
            if (result is ImageGenerationResult.Success) {
                return@withContext result
            }
        }
        
        ImageGenerationResult.Error("所有图像生成API都失败了")
    }
    
    /**
     * 尝试使用指定配置生成图像
     */
    private suspend fun tryGenerateImage(
        config: ApiConfig,
        prompt: String
    ): ImageGenerationResult {
        return try {
            val retrofit = retrofitBuilder
                .baseUrl(config.apiUrl)
                .build()
            
            val api = retrofit.create(ImageGenerationApi::class.java)
            
            when {
                config.modelName.contains("dall-e", ignoreCase = true) -> {
                    generateWithOpenAI(api, config, prompt)
                }
                config.modelName.contains("stable", ignoreCase = true) ||
                config.apiUrl.contains("stability", ignoreCase = true) -> {
                    generateWithStabilityAI(api, config, prompt)
                }
                else -> {
                    generateWithGenericAPI(api, config, prompt)
                }
            }
        } catch (e: Exception) {
            ImageGenerationResult.Error("API调用失败: ${e.message}")
        }
    }
    
    /**
     * 使用OpenAI DALL-E生成图像
     */
    private suspend fun generateWithOpenAI(
        api: ImageGenerationApi,
        config: ApiConfig,
        prompt: String
    ): ImageGenerationResult {
        val request = OpenAIImageRequest(
            model = config.modelName,
            prompt = prompt,
            n = 1,
            size = "1024x1024",
            quality = "standard",
            style = "vivid"
        )
        
        val response = api.generateImageOpenAI(
            authorization = "Bearer ${config.apiKey}",
            request = request
        )
        
        return if (response.isSuccessful) {
            val data = response.body()?.data?.firstOrNull()
            if (data != null) {
                ImageGenerationResult.Success(
                    imageUrl = data.url,
                    base64Image = data.b64_json,
                    revisedPrompt = data.revised_prompt
                )
            } else {
                ImageGenerationResult.Error("响应数据为空")
            }
        } else {
            ImageGenerationResult.Error(
                message = response.errorBody()?.string() ?: "未知错误",
                code = response.code()
            )
        }
    }
    
    /**
     * 使用Stability AI生成图像
     */
    private suspend fun generateWithStabilityAI(
        api: ImageGenerationApi,
        config: ApiConfig,
        prompt: String
    ): ImageGenerationResult {
        val request = StabilityAIRequest(
            text_prompts = listOf(
                TextPrompt(text = prompt, weight = 1.0f),
                TextPrompt(
                    text = "cartoon, anime, 2d, low quality, blurry, watermark",
                    weight = -1.0f
                )  // 负面提示词
            ),
            cfg_scale = 7.0f,
            height = 1024,
            width = 1024,
            samples = 1,
            steps = 30,
            style_preset = "cinematic"  // 电影质感风格
        )
        
        val engineId = config.modelName.ifEmpty { "stable-diffusion-xl-1024-v1-0" }
        
        val response = api.generateImageStability(
            engineId = engineId,
            authorization = "Bearer ${config.apiKey}",
            request = request
        )
        
        return if (response.isSuccessful) {
            val artifact = response.body()?.artifacts?.firstOrNull()
            if (artifact != null) {
                ImageGenerationResult.Success(
                    base64Image = artifact.base64
                )
            } else {
                ImageGenerationResult.Error("响应数据为空")
            }
        } else {
            ImageGenerationResult.Error(
                message = response.errorBody()?.string() ?: "未知错误",
                code = response.code()
            )
        }
    }
    
    /**
     * 使用通用API生成图像
     */
    private suspend fun generateWithGenericAPI(
        api: ImageGenerationApi,
        config: ApiConfig,
        prompt: String
    ): ImageGenerationResult {
        val requestBody = mapOf(
            "prompt" to prompt,
            "negative_prompt" to "cartoon, anime, 2d, low quality, blurry, watermark",
            "width" to 1024,
            "height" to 1024,
            "seed" to (-1),
            "steps" to 30
        )
        
        val headers = mapOf(
            "Authorization" to "Bearer ${config.apiKey}",
            "Content-Type" to "application/json"
        )
        
        val response = api.generateImage(
            url = "/generate",
            headers = headers,
            request = requestBody
        )
        
        return if (response.isSuccessful) {
            val body = response.body()
            val imageUrl = body?.get("image_url") as? String
            val base64Image = body?.get("image_base64") as? String
            
            if (imageUrl != null || base64Image != null) {
                ImageGenerationResult.Success(
                    imageUrl = imageUrl,
                    base64Image = base64Image
                )
            } else {
                ImageGenerationResult.Error("响应数据为空")
            }
        } else {
            ImageGenerationResult.Error(
                message = response.errorBody()?.string() ?: "未知错误",
                code = response.code()
            )
        }
    }
    
    /**
     * 构建头像生成提示词
     */
    private fun buildAvatarPrompt(
        description: String,
        age: Int,
        gender: String,
        occupation: String,
        personality: String
    ): String {
        val ageGroup = when (age) {
            in 0..12 -> "a child"
            in 13..17 -> "a teenager"
            in 18..30 -> "a young adult"
            in 31..50 -> "a middle-aged person"
            else -> "an elderly person"
        }
        
        val genderStr = if (gender == "MALE") "male" else "female"
        
        return buildString {
            append("Professional portrait of $ageGroup $genderStr, ")
            append("occupation: $occupation, ")
            append("personality: $personality. ")
            append("$description. ")
            append("High quality, realistic, detailed facial features, ")
            append("professional lighting, 8k resolution, ")
            append("cinematic photography style")
        }
    }
    
    /**
     * 构建任务图像生成提示词
     */
    private fun buildTaskImagePrompt(
        taskDescription: String,
        requirements: String,
        style: String
    ): String {
        return buildString {
            append("$taskDescription. ")
            append("Requirements: $requirements. ")
            
            when (style.lowercase()) {
                "epic" -> {
                    append("Epic composition, grand scale, dramatic lighting, ")
                    append("cinematic atmosphere, highly detailed, ")
                    append("8k resolution, masterpiece, best quality")
                }
                "realistic" -> {
                    append("Photorealistic, highly detailed, ")
                    append("professional photography, natural lighting, ")
                    append("8k resolution, sharp focus")
                }
                "artistic" -> {
                    append("Artistic style, creative composition, ")
                    append("vibrant colors, detailed artwork, ")
                    append("high quality, masterpiece")
                }
                else -> {
                    append("High quality, detailed, ")
                    append("professional, 8k resolution")
                }
            }
            
            // 添加负面提示词
            append(". Negative: cartoon, anime, 2d, low quality, blurry, watermark, text")
        }
    }
}
