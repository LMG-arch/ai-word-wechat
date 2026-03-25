package com.ai.socialworld.presentation.logs

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.domain.service.LogEntry
import com.ai.socialworld.domain.service.LogService
import com.ai.socialworld.domain.service.WorldTimeManager
import com.ai.socialworld.domain.service.toLogEntry
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 日志面板ViewModel
 */
@HiltViewModel
class LogPanelViewModel @Inject constructor(
    private val logService: LogService,
    private val worldTimeManager: WorldTimeManager
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(LogPanelUiState())
    val uiState: StateFlow<LogPanelUiState> = _uiState.asStateFlow()
    
    init {
        loadLogs()
        observeWorldTime()
    }
    
    /**
     * 加载日志
     */
    private fun loadLogs() {
        viewModelScope.launch {
            logService.getRecentLogs(200).collect { logs ->
                _uiState.update { it.copy(logs = logs) }
            }
        }
    }
    
    /**
     * 观察世界时间
     */
    private fun observeWorldTime() {
        viewModelScope.launch {
            worldTimeManager.worldTime.collect { time ->
                _uiState.update { it.copy(worldTime = time) }
            }
        }
    }
    
    /**
     * 开始世界
     */
    fun startWorld() {
        worldTimeManager.startWorld()
    }
    
    /**
     * 暂停世界
     */
    fun pauseWorld() {
        worldTimeManager.pauseWorld()
    }
    
    /**
     * 设置时间倍速
     */
    fun setTimeMultiplier(multiplier: Int) {
        worldTimeManager.setTimeMultiplier(multiplier)
    }
    
    /**
     * 清除日志
     */
    fun clearLogs() {
        _uiState.update { it.copy(logs = emptyList()) }
    }
    
    /**
     * 过滤日志
     */
    fun filterLogs(type: com.ai.socialworld.data.model.LogType?) {
        viewModelScope.launch {
            val filtered = if (type != null) {
                logService.getRecentLogs(200).map { logs ->
                    logs.filter { it.type == type }
                }
            } else {
                logService.getRecentLogs(200)
            }
            
            filtered.collect { logs ->
                _uiState.update { it.copy(logs = logs) }
            }
        }
    }
    
    /**
     * 搜索日志
     */
    fun searchLogs(keyword: String) {
        viewModelScope.launch {
            val logs = _uiState.value.logs
            val filtered = logService.searchLogs(
                logs.map { 
                    com.ai.socialworld.data.model.SystemLog(
                        id = it.id,
                        timestamp = it.timestamp,
                        characterId = it.characterId,
                        characterName = it.characterName,
                        logType = it.type.name,
                        content = it.content
                    )
                },
                keyword
            )
            
            _uiState.update { 
                it.copy(
                    logs = filtered.map { log -> log.toLogEntry() }
                )
            }
        }
    }
}

/**
 * 日志面板UI状态
 */
data class LogPanelUiState(
    val logs: List<LogEntry> = emptyList(),
    val worldTime: Long = System.currentTimeMillis(),
    val isLoading: Boolean = false,
    val error: String? = null
)
