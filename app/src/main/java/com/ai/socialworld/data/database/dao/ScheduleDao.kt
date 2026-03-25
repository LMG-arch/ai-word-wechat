package com.ai.socialworld.data.database.dao

import androidx.room.*
import com.ai.socialworld.data.database.entity.*
import kotlinx.coroutines.flow.Flow

/**
 * 日程数据访问对象
 */
@Dao
interface ScheduleDao {
    @Query("SELECT * FROM schedules WHERE characterId = :characterId ORDER BY date DESC")
    fun getSchedulesByCharacter(characterId: String): Flow<List<ScheduleEntity>>
    
    @Query("SELECT * FROM schedules WHERE characterId = :characterId AND date = :date")
    suspend fun getScheduleByDate(characterId: String, date: String): ScheduleEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSchedule(schedule: ScheduleEntity)
    
    @Update
    suspend fun updateSchedule(schedule: ScheduleEntity)
    
    @Delete
    suspend fun deleteSchedule(schedule: ScheduleEntity)
    
    // 位置相关
    @Query("SELECT * FROM locations")
    fun getAllLocations(): Flow<List<LocationEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertLocation(location: LocationEntity)
    
    @Query("SELECT * FROM location_history WHERE characterId = :characterId ORDER BY arrivedAt DESC")
    fun getLocationHistory(characterId: String): Flow<List<LocationHistoryEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertLocationHistory(history: LocationHistoryEntity)
    
    @Query("UPDATE location_history SET leftAt = :leftAt WHERE id = :id")
    suspend fun updateLocationHistoryLeftAt(id: String, leftAt: Long)
}
