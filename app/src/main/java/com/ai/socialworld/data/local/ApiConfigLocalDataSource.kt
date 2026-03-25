package com.ai.socialworld.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.core.content.edit
import com.ai.socialworld.data.model.ApiConfig
import com.ai.socialworld.data.model.ApiProvider
import com.ai.socialworld.data.model.ApiType
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * API配置本地数据源
 */
@Singleton
class ApiConfigLocalDataSource @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val gson = Gson()

    companion object {
        private const val PREFS_NAME = "api_config_prefs"
        private const val KEY_LANGUAGE_MODELS = "language_models"
        private const val KEY_IMAGE_MODELS = "image_models"
        private const val KEY_VECTOR_MODELS = "vector_models"
        private const val KEY_RERANK_MODELS = "rerank_models"
        private const val KEY_CURRENT_LANGUAGE_MODEL = "current_language_model"
        private const val KEY_CURRENT_IMAGE_MODEL = "current_image_model"
        private const val KEY_CURRENT_VECTOR_MODEL = "current_vector_model"
        private const val KEY_CURRENT_RERANK_MODEL = "current_rerank_model"
    }

    // 保存API配置列表
    fun saveApiConfigs(type: ApiType, configs: List<ApiConfig>) {
        val key = when (type) {
            ApiType.LANGUAGE_MODEL -> KEY_LANGUAGE_MODELS
            ApiType.IMAGE_MODEL -> KEY_IMAGE_MODELS
            ApiType.VECTOR_MODEL -> KEY_VECTOR_MODELS
            ApiType.RERANK_MODEL -> KEY_RERANK_MODELS
        }
        val json = gson.toJson(configs)
        prefs.edit { putString(key, json) }
    }

    // 获取API配置列表
    fun getApiConfigs(type: ApiType): List<ApiConfig> {
        val key = when (type) {
            ApiType.LANGUAGE_MODEL -> KEY_LANGUAGE_MODELS
            ApiType.IMAGE_MODEL -> KEY_IMAGE_MODELS
            ApiType.VECTOR_MODEL -> KEY_VECTOR_MODELS
            ApiType.RERANK_MODEL -> KEY_RERANK_MODELS
        }
        val json = prefs.getString(key, null) ?: return getDefaultConfigs(type)
        return try {
            val typeToken = object : TypeToken<List<ApiConfig>>() {}.type
            gson.fromJson<List<ApiConfig>>(json, typeToken) ?: getDefaultConfigs(type)
        } catch (e: Exception) {
            getDefaultConfigs(type)
        }
    }

    // 保存当前选中的配置ID
    fun saveCurrentConfigId(type: ApiType, configId: String) {
        val key = when (type) {
            ApiType.LANGUAGE_MODEL -> KEY_CURRENT_LANGUAGE_MODEL
            ApiType.IMAGE_MODEL -> KEY_CURRENT_IMAGE_MODEL
            ApiType.VECTOR_MODEL -> KEY_CURRENT_VECTOR_MODEL
            ApiType.RERANK_MODEL -> KEY_CURRENT_RERANK_MODEL
        }
        prefs.edit { putString(key, configId) }
    }

    // 获取当前选中的配置ID
    fun getCurrentConfigId(type: ApiType): String? {
        val key = when (type) {
            ApiType.LANGUAGE_MODEL -> KEY_CURRENT_LANGUAGE_MODEL
            ApiType.IMAGE_MODEL -> KEY_CURRENT_IMAGE_MODEL
            ApiType.VECTOR_MODEL -> KEY_CURRENT_VECTOR_MODEL
            ApiType.RERANK_MODEL -> KEY_CURRENT_RERANK_MODEL
        }
        return prefs.getString(key, null)
    }

    // 获取默认配置
    private fun getDefaultConfigs(type: ApiType): List<ApiConfig> {
        return when (type) {
            ApiType.LANGUAGE_MODEL -> listOf(
                ApiConfig(
                    id = "deepseek_default",
                    type = ApiType.LANGUAGE_MODEL,
                    name = "DeepSeek",
                    baseUrl = "https://api.deepseek.com/v1",
                    apiKey = "",
                    modelName = "deepseek-chat",
                    priority = 0
                )
            )
            ApiType.IMAGE_MODEL -> listOf(
                ApiConfig(
                    id = "sd_default",
                    type = ApiType.IMAGE_MODEL,
                    name = "Stable Diffusion",
                    baseUrl = "https://api.stability.ai/v1",
                    apiKey = "",
                    modelName = "stable-diffusion-xl-1024-v1-0",
                    priority = 0
                )
            )
            else -> emptyList()
        }
    }

    // 清除所有配置
    fun clearAllConfigs() {
        prefs.edit { clear() }
    }
}
