package com.ai.socialworld.data.database.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 日程实体（Room数据库）
 */
@Entity(tableName = "schedules")
data class ScheduleEntity(
    @PrimaryKey
    val id: String,
    val characterId: String,
    val date: String, // YYYY-MM-DD格式
    val eventsJson: String, // JSON序列化的日程事件
    val createdAt: Long = System.currentTimeMillis()
)

/**
 * 位置历史实体
 */
@Entity(tableName = "location_history")
data class LocationHistoryEntity(
    @PrimaryKey
    val id: String,
    val characterId: String,
    val locationId: String,
    val arrivedAt: Long,
    val leftAt: Long? = null
)

/**
 * 位置实体
 */
@Entity(tableName = "locations")
data class LocationEntity(
    @PrimaryKey
    val id: String,
    val name: String,
    val type: String, // OFFICE, RESTAURANT, BAR, PARK, HOME, OTHER
    val latitude: Double,
    val longitude: Double
)
