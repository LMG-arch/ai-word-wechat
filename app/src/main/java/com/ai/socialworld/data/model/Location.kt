package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * 位置实体
 */
@Entity(tableName = "locations")
data class Location(
    @PrimaryKey
    val id: String,
    val name: String,                    // 位置名称
    val type: LocationType,              // 位置类型
    val latitude: Double,                // 纬度
    val longitude: Double,               // 经度
    val description: String = ""         // 描述
)

/**
 * 位置类型
 */
enum class LocationType {
    HOME,           // 家
    OFFICE,         // 办公室
    RESTAURANT,     // 餐厅
    CAFE,           // 咖啡馆
    BAR,            // 酒吧
    PARK,           // 公园
    SHOPPING_MALL,  // 商场
    SCHOOL,         // 学校
    HOSPITAL,       // 医院
    OTHER           // 其他
}

/**
 * 角色位置记录
 */
@Entity(
    tableName = "character_locations",
    foreignKeys = [
        ForeignKey(
            entity = Character::class,
            parentColumns = ["id"],
            childColumns = ["characterId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index(value = ["characterId"]), Index(value = ["timestamp"])]
)
data class CharacterLocation(
    @PrimaryKey
    val id: String,
    val characterId: String,
    val locationId: String,
    val latitude: Double,
    val longitude: Double,
    val timestamp: Long = System.currentTimeMillis(),
    val leftAt: Long? = null,            // 离开时间（null表示仍在）
    val activity: String? = null        // 正在做什么
)

/**
 * 相遇记录
 */
@Entity(tableName = "encounters")
data class Encounter(
    @PrimaryKey
    val id: String,
    val characterId1: String,
    val characterId2: String,
    val locationId: String,
    val latitude: Double,
    val longitude: Double,
    val startTime: Long,
    val endTime: Long? = null,           // null表示仍在相遇
    val interactionType: EncounterType? = null
)

/**
 * 相遇类型
 */
enum class EncounterType {
    PASS_BY,        // 擦肩而过
    BRIEF_CHAT,     // 简短交谈
    LONG_CONVERSATION, // 深入交谈
    COFFEE,         // 一起喝咖啡
    MEAL,           // 一起吃饭
    WORK_TOGETHER   // 一起工作
}
