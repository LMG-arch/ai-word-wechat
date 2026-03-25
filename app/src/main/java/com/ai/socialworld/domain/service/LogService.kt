package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.LogType
import com.ai.socialworld.data.model.SystemLog
import com.ai.socialworld.domain.repository.ApiConfigRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 日志服务
 * 管理系统日志的记录、查询和过滤
 */
@Singleton
class LogService @Inject constructor(
    private val apiConfigRepository: ApiConfigRepository
) {
    
    private val dateFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
    
    /**
     * 记录日志
     */
    suspend fun log(
        characterId: String? = null,
        characterName: String? = null,
        type: LogType,
        content: String
    ) = withContext(Dispatchers.IO) {
        apiConfigRepository.addLog(characterId, characterName, type, content)
    }
    
    /**
     * 记录任务日志
     */
    suspend fun logTask(
        characterId: String?,
        characterName: String?,
        content: String
    ) {
        log(characterId, characterName, LogType.TASK, content)
    }
    
    /**
     * 记录社交日志
     */
    suspend fun logSocial(
        characterId: String?,
        characterName: String?,
        content: String
    ) {
        log(characterId, characterName, LogType.SOCIAL, content)
    }
    
    /**
     * 记录记忆日志
     */
    suspend fun logMemory(
        characterId: String?,
        characterName: String?,
        content: String
    ) {
        log(characterId, characterName, LogType.MEMORY, content)
    }
    
    /**
     * 记录经济日志
     */
    suspend fun logEconomy(
        characterId: String?,
        characterName: String?,
        content: String
    ) {
        log(characterId, characterName, LogType.ECONOMY, content)
    }
    
    /**
     * 记录系统日志
     */
    suspend fun logSystem(content: String) {
        log(null, null, LogType.SYSTEM, content)
    }
    
    /**
     * 获取最近日志
     */
    fun getRecentLogs(limit: Int = 100): Flow<List<LogEntry>> {
        return apiConfigRepository.getRecentLogs(limit).map { logs ->
            logs.map { it.toLogEntry() }
        }
    }
    
    /**
     * 格式化日志
     */
    fun formatLog(log: SystemLog): String {
        val time = dateFormat.format(Date(log.timestamp))
        val type = "[${log.logType}]"
        val name = log.characterName?.let { "[$it]" } ?: ""
        
        return "[$time] $name $type ${log.content}"
    }
    
    /**
     * 按类型过滤日志
     */
    fun filterLogsByType(logs: List<SystemLog>, type: LogType): List<SystemLog> {
        return logs.filter { it.logType == type }
    }
    
    /**
     * 按角色过滤日志
     */
    fun filterLogsByCharacter(logs: List<SystemLog>, characterId: String): List<SystemLog> {
        return logs.filter { it.characterId == characterId }
    }
    
    /**
     * 按关键词搜索日志
     */
    fun searchLogs(logs: List<SystemLog>, keyword: String): List<SystemLog> {
        if (keyword.isBlank()) return logs
        return logs.filter { 
            it.content.contains(keyword, ignoreCase = true) ||
            it.characterName?.contains(keyword, ignoreCase = true) == true
        }
    }
}

/**
 * 日志条目（用于UI显示）
 */
data class LogEntry(
    val id: String,
    val timestamp: Long,
    val formattedTime: String,
    val characterId: String?,
    val characterName: String?,
    val type: LogType,
    val content: String,
    val formattedLog: String
)

/**
 * 扩展函数：转换为LogEntry
 */
fun SystemLog.toLogEntry(): LogEntry {
    val dateFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
    val time = dateFormat.format(Date(timestamp))
    val type = LogType.valueOf(logType)
    val name = characterName?.let { "[$it]" } ?: ""
    
    return LogEntry(
        id = id,
        timestamp = timestamp,
        formattedTime = time,
        characterId = characterId,
        characterName = characterName,
        type = type,
        content = content,
        formattedLog = "[$time] $name [${type}] $content"
    )
}
