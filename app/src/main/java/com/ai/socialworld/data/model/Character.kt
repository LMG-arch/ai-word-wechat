package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.Instant
import java.time.LocalTime

/**
 * 角色实体（Room 数据库）
 * 根据开发文档定义完整的角色属性
 */
@Entity(tableName = "characters")
data class Character(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    // 基础信息
    val name: String,
    val age: Int = 18,
    val gender: Gender = Gender.MALE,
    val occupation: String = "",
    
    // 性格与背景
    val personality: String = "",
    val background: String = "",
    
    // 经济系统
    val money: Int = 50, // 初始资金50
    
    // 头像与签名
    val avatarUrl: String? = null,
    val signature: String = "",
    val lastAvatarUpdate: Long? = null,    // 使用Long时间戳
    val lastSignatureUpdate: Long? = null, // 使用Long时间戳
    val avatarUpdateCount: Int = 0,        // 本周头像更新次数
    val signatureUpdateCount: Int = 0,      // 本周签名更新次数
    
    // 声音设定
    val voiceId: String? = null,
    
    // 生命周期
    val growthStage: GrowthStage = GrowthStage.YOUTH,
    val isAlive: Boolean = true,
    val deathReason: String? = null,
    
    // 时间戳 (使用Long代替Instant以兼容API 24+)
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis(),
    
    // 软删除
    val isDeleted: Boolean = false
)

/**
 * 性别枚举
 */
enum class Gender {
    MALE,
    FEMALE
}

/**
 * 成长阶段
 */
enum class GrowthStage(val ageRange: IntRange, val description: String) {
    CHILD(0..12, "儿童期"),
    TEENAGER(13..17, "青少年期"),
    YOUTH(18..40, "青年期"),
    MIDDLE(41..60, "中年期"),
    ELDER(61..150, "老年期");
    
    companion object {
        fun fromAge(age: Int): GrowthStage {
            return entries.find { age in it.ageRange } ?: YOUTH
        }
    }
}

/**
 * 角色扩展属性
 */
fun Character.canWork(): Boolean {
    return age >= 18 && isAlive
}

fun Character.canCreateCompany(): Boolean {
    return age >= 18 && money >= 200 && isAlive
}

fun Character.canUpdateAvatar(): Boolean {
    return avatarUpdateCount < 2
}

fun Character.canUpdateSignature(): Boolean {
    return signatureUpdateCount < 2
}
