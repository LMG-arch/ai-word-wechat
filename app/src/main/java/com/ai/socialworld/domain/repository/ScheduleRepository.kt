package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.Schedule
import com.ai.socialworld.data.model.ScheduleStatus
import kotlinx.coroutines.flow.Flow

/**
 * 日程仓库接口
 */
interface ScheduleRepository {
    
    /**
     * 插入日程
     */
    suspend fun insertSchedule(schedule: Schedule): Long
    
    /**
     * 更新日程
     */
    suspend fun updateSchedule(schedule: Schedule)
    
    /**
     * 删除日程
     */
    suspend fun deleteSchedule(schedule: Schedule)
    
    /**
     * 获取角色的日程（按日期）
     */
    fun getSchedulesByCharacter(characterId: String): Flow<List<Schedule>>
    
    /**
     * 获取角色指定日期的日程
     */
    suspend fun getSchedulesByDate(characterId: String, date: Long): List<Schedule>
    
    /**
     * 获取当前进行中的日程
     */
    suspend fun getCurrentSchedule(characterId: String, timestamp: Long): Schedule?
    
    /**
     * 更新日程状态
     */
    suspend fun updateScheduleStatus(scheduleId: String, status: ScheduleStatus)
    
    /**
     * 获取角色今天的日程
     */
    suspend fun getTodaySchedules(characterId: String): List<Schedule>
}
