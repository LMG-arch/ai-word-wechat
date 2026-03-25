package com.ai.socialworld.presentation.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.model.ApiConfig
import com.ai.socialworld.data.model.ApiType
import com.ai.socialworld.domain.repository.ApiConfigRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

/**
 * API配置ViewModel
 */
@HiltViewModel
class ApiConfigViewModel @Inject constructor(
    private val apiConfigRepository: ApiConfigRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ApiConfigUiState())
    val uiState: StateFlow<ApiConfigUiState> = _uiState.asStateFlow()

    init {
        loadConfigs()
    }

    private fun loadConfigs() {
        viewModelScope.launch {
            combine(
                apiConfigRepository.getApiConfigsByType(ApiType.LANGUAGE),
                apiConfigRepository.getApiConfigsByType(ApiType.IMAGE),
                apiConfigRepository.getApiConfigsByType(ApiType.VECTOR)
            ) { language, image, vector ->
                ApiConfigUiState(
                    languageConfigs = language.map { it.toUiItem() },
                    imageConfigs = image.map { it.toUiItem() },
                    vectorConfigs = vector.map { it.toUiItem() }
                )
            }.collect { _uiState.value = it }
        }
    }

    fun addConfig(name: String, apiType: ApiType, apiUrl: String, apiKey: String, modelName: String) {
        viewModelScope.launch {
            val config = ApiConfig(
                id = UUID.randomUUID().toString(),
                name = name,
                apiType = apiType,
                apiUrl = apiUrl,
                apiKey = apiKey,
                modelName = modelName,
                isPrimary = false, // 新配置默认非主配置
                priority = 0
            )
            apiConfigRepository.saveApiConfig(config)
        }
    }

    fun deleteConfig(config: ApiConfigUiItem) {
        viewModelScope.launch {
            apiConfigRepository.deleteApiConfig(
                ApiConfig(
                    id = config.id,
                    name = config.name,
                    apiType = config.apiType,
                    apiUrl = config.apiUrl,
                    apiKey = config.apiKey,
                    modelName = config.modelName,
                    isPrimary = config.isPrimary
                )
            )
        }
    }

    fun setPrimaryConfig(apiType: ApiType, configId: String) {
        viewModelScope.launch {
            apiConfigRepository.setPrimaryConfig(apiType, configId)
        }
    }

    fun testConnection() {
        viewModelScope.launch {
            _uiState.update { it.copy(isTesting = true, testResult = null) }
            
            // TODO: 实现实际的API连接测试
            kotlinx.coroutines.delay(1000)
            
            _uiState.update { 
                it.copy(
                    isTesting = false,
                    testResult = TestResult(
                        success = true,
                        message = "连接测试功能待实现"
                    )
                )
            }
        }
    }

    private fun ApiConfig.toUiItem(): ApiConfigUiItem {
        return ApiConfigUiItem(
            id = this.id,
            name = this.name,
            apiType = this.apiType,
            apiUrl = this.apiUrl,
            apiKey = "${this.apiKey.take(4)}****${this.apiKey.takeLast(4)}", // 隐藏部分API Key
            modelName = this.modelName,
            isPrimary = this.isPrimary
        )
    }
}

/**
 * API配置UI状态
 */
data class ApiConfigUiState(
    val languageConfigs: List<ApiConfigUiItem> = emptyList(),
    val imageConfigs: List<ApiConfigUiItem> = emptyList(),
    val vectorConfigs: List<ApiConfigUiItem> = emptyList(),
    val isTesting: Boolean = false,
    val testResult: TestResult? = null
)

data class TestResult(
    val success: Boolean,
    val message: String
)
