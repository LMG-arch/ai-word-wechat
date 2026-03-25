package com.ai.socialworld.data.local

import androidx.room.*
import com.ai.socialworld.data.model.Schedule
import com.ai.socialworld.data.model.ScheduleStatus
import kotlinx.coroutines.flow.Flow

/**
 * 日程DAO
 */
@Dao
interface ScheduleDao {
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(schedule: Schedule): Long
    
    @Update
    suspend fun update(schedule: Schedule)
    
    @Delete
    suspend fun delete(schedule: Schedule)
    
    @Query("SELECT * FROM schedules WHERE characterId = :characterId ORDER BY startTime ASC")
    fun getSchedulesByCharacter(characterId: String): Flow<List<Schedule>>
    
    @Query("SELECT * FROM schedules WHERE characterId = :characterId AND date = :date ORDER BY startTime ASC")
    suspend fun getSchedulesByDate(characterId: String, date: Long): List<Schedule>
    
    @Query("""
        SELECT * FROM schedules 
        WHERE characterId = :characterId 
        AND startTime <= :timestamp 
        AND endTime > :timestamp 
        LIMIT 1
    """)
    suspend fun getCurrentSchedule(characterId: String, timestamp: Long): Schedule?
    
    @Query("UPDATE schedules SET status = :status WHERE id = :scheduleId")
    suspend fun updateStatus(scheduleId: String, status: ScheduleStatus)
    
    @Query("""
        SELECT * FROM schedules 
        WHERE characterId = :characterId 
        AND date >= :startOfDay 
        AND date < :endOfDay 
        ORDER BY startTime ASC
    """)
    suspend fun getTodaySchedules(characterId: String, startOfDay: Long, endOfDay: Long): List<Schedule>
    
    @Query("DELETE FROM schedules WHERE characterId = :characterId AND date < :beforeDate")
    suspend fun deleteOldSchedules(characterId: String, beforeDate: Long)
}
