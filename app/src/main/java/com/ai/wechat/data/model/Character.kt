package com.ai.wechat.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * AI 角色实体
 */
@Entity(tableName = "characters")
data class Character(
    @PrimaryKey
    val id: String,
    val name: String,
    val age: Int,
    val gender: String,
    val occupation: String,
    val personality: String,
    val avatarUrl: String?,
    val signature: String?,
    val money: Double = 50.0,
    val mood: String = "normal",
    val currentLocationId: String?,
    val companyId: String?,
    val createdAt: Long,
    val updatedAt: Long,
    val lastAvatarChangeTime: Long = 0L,
    val lastSignatureChangeTime: Long = 0L,
    val isAlive: Boolean = true,
    val deathTime: Long? = null
)

/**
 * 角色年龄段
 */
enum class AgeStage(val minAge: Int, val maxAge: Int) {
    CHILD(0, 12),
    TEENAGER(13, 17),
    YOUTH(18, 40),
    MIDDLE_AGE(41, 60),
    SENIOR(61, Int.MAX_VALUE)
}

/**
 * 获取角色当前年龄段
 */
fun Character.getAgeStage(): AgeStage {
    return AgeStage.values().find { age in it.minAge..it.maxAge } ?: AgeStage.YOUTH
}
