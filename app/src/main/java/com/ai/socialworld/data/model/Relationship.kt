package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 关系类型
 */
enum class RelationshipType {
    FRIEND_WITH,    // 好友关系
    WORK_AT,        // 工作关系
    FAMILY          // 家庭关系
}

/**
 * 关系实体
 */
@Entity(tableName = "relationships")
data class Relationship(
    @PrimaryKey
    val id: String,
    val fromId: String,                // 起始角色ID
    val toId: String,                  // 目标角色ID
    val type: RelationshipType = RelationshipType.FRIEND_WITH,
    val intimacy: Int = 0,             // 亲密度 (0-100)
    val validFrom: Long = System.currentTimeMillis(), // 关系开始时间 (Long)
    val validTo: Long? = null,        // 关系结束时间 (Long)
    val lastInteractionAt: Long = System.currentTimeMillis(), // 最后互动时间
    val interactionCount: Int = 0      // 互动次数
)

/**
 * 关系状态
 */
enum class RelationshipStatus(val minIntimacy: Int, val maxIntimacy: Int, val description: String) {
    STRANGER(0, 20, "陌生人"),
    ACQUAINTANCE(21, 40, "认识"),
    FAMILIAR(41, 60, "熟人"),
    FRIEND(61, 80, "好友"),
    BEST_FRIEND(81, 100, "密友");
    
    companion object {
        fun fromIntimacy(intimacy: Int): RelationshipStatus {
            return entries.find { intimacy in it.minIntimacy..it.maxIntimacy } ?: STRANGER
        }
    }
}

/**
 * 互动行为
 */
enum class InteractionAction(val baseDelta: IntRange) {
    CHAT(1..3),           // 聊天
    LIKE(1..1),           // 点赞
    COMMENT(2..2),        // 评论
    MEET(2..5),           // 见面
    COLLABORATE(1..10),   // 合作
    CONFLICT((-15)..(-5)) // 冲突
}

/**
 * 关系变化记录
 */
@Entity(tableName = "relationship_changes")
data class RelationshipChange(
    @PrimaryKey
    val id: String,
    val relationshipId: String,
    val oldIntimacy: Int,
    val newIntimacy: Int,
    val action: InteractionAction,
    val timestamp: Long = System.currentTimeMillis()  // 使用Long
)
