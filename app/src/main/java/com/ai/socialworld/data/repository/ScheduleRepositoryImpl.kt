package com.ai.socialworld.data.repository

import com.ai.socialworld.data.local.ScheduleDao
import com.ai.socialworld.data.model.Schedule
import com.ai.socialworld.data.model.ScheduleStatus
import com.ai.socialworld.domain.repository.ScheduleRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 日程仓库实现
 */
@Singleton
class ScheduleRepositoryImpl @Inject constructor(
    private val scheduleDao: ScheduleDao
) : ScheduleRepository {
    
    override suspend fun insertSchedule(schedule: Schedule): Long {
        return scheduleDao.insert(schedule)
    }
    
    override suspend fun updateSchedule(schedule: Schedule) {
        scheduleDao.update(schedule)
    }
    
    override suspend fun deleteSchedule(schedule: Schedule) {
        scheduleDao.delete(schedule)
    }
    
    override fun getSchedulesByCharacter(characterId: String): Flow<List<Schedule>> {
        return scheduleDao.getSchedulesByCharacter(characterId)
    }
    
    override suspend fun getSchedulesByDate(characterId: String, date: Long): List<Schedule> {
        return scheduleDao.getSchedulesByDate(characterId, date)
    }
    
    override suspend fun getCurrentSchedule(characterId: String, timestamp: Long): Schedule? {
        return scheduleDao.getCurrentSchedule(characterId, timestamp)
    }
    
    override suspend fun updateScheduleStatus(scheduleId: String, status: ScheduleStatus) {
        scheduleDao.updateStatus(scheduleId, status)
    }
    
    override suspend fun getTodaySchedules(characterId: String): List<Schedule> {
        val now = System.currentTimeMillis()
        val startOfDay = now - (now % (24 * 60 * 60 * 1000))
        val endOfDay = startOfDay + (24 * 60 * 60 * 1000)
        
        return scheduleDao.getTodaySchedules(characterId, startOfDay, endOfDay)
    }
}
