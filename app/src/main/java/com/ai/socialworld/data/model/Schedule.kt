package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 日程实体
 */
@Entity(tableName = "schedules")
data class Schedule(
    @PrimaryKey
    val id: String,
    val characterId: String,           // 角色ID
    val date: String,                  // 日期 (YYYY-MM-DD)
    val events: String = "[]",         // 事件列表 JSON
    val createdAt: Long = System.currentTimeMillis()  // 使用Long
)

/**
 * 日程事件
 */
data class ScheduleEvent(
    val id: String,
    val startTime: String,             // 开始时间 (HH:mm)
    val endTime: String,               // 结束时间 (HH:mm)
    val location: String,              // 地点
    val activity: String,              // 活动
    val relatedEntityId: String? = null, // 相关实体ID (如朋友ID)
    val isCompleted: Boolean = false   // 是否已完成
)

/**
 * 位置记录
 */
@Entity(tableName = "locations")
data class Location(
    @PrimaryKey
    val id: String,
    val characterId: String,
    val name: String,                  // 地点名称
    val type: LocationType,
    val latitude: Double? = null,      // 纬度
    val longitude: Double? = null,     // 经度
    val arrivedAt: Long = System.currentTimeMillis(),  // 到达时间
    val leftAt: Long? = null           // 离开时间
)

/**
 * 地点类型
 */
enum class LocationType {
    HOME,       // 家
    OFFICE,     // 办公室
    RESTAURANT, // 餐厅
    CAFE,       // 咖啡厅
    BAR,        // 酒吧
    PARK,       // 公园
    SHOP,       // 商店
    OTHER       // 其他
}
