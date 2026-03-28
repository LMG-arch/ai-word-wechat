package com.ai.wechat.service

import com.ai.wechat.data.memory.MemoryEngine
import com.ai.wechat.data.memory.MemoryType
import com.ai.wechat.data.memory.RelationshipType
import com.ai.wechat.data.model.GroupChat
import com.ai.wechat.data.model.GroupChatMember
import com.ai.wechat.data.model.GroupChatType
import com.ai.wechat.db.dao.GroupChatDao
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.Instant
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 关系引擎
 * 负责亲密度计算、关系演变、朋友圈机制
 */
@Singleton
class RelationshipEngine @Inject constructor(
    private val memoryEngine: MemoryEngine,
    private val groupChatDao: GroupChatDao
) {

    companion object {
        // 亲密度阈值
        private const val THRESHOLD_STRANGER = 20
        private const val THRESHOLD_ACQUAINTANCE = 40
        private const val THRESHOLD_FRIEND = 60
        private const val THRESHOLD_CLOSE_FRIEND = 80

        // 每日衰减
        private const val DAILY_DECAY = 1
        private const val STALE_DAYS = 3
    }

    /**
     * 更新亲密度
     */
    suspend fun updateIntimacy(
        fromId: String,
        toId: String,
        action: InteractionAction
    ): IntimacyChangeResult = withContext(Dispatchers.IO) {
        val currentRel = memoryEngine.getCurrentRelationship(fromId, toId)
        
        // 如果是新关系，先创建
        if (currentRel == null) {
            memoryEngine.storeRelationship(
                fromId = fromId,
                toId = toId,
                type = RelationshipType.FRIEND_WITH,
                properties = mapOf("intimacy" to 0.0),
                validFrom = Instant.now()
            )
        }

        // 计算变化值
        val delta = when (action) {
            InteractionAction.CHAT -> (1..3).random()
            InteractionAction.LIKE -> 1
            InteractionAction.COMMENT -> 2
            InteractionAction.MEET -> (2..5).random()
            InteractionAction.COLLABORATE -> (1..10).random()
            InteractionAction.CONFLICT -> -(5..15).random()
            InteractionAction.GIFT -> (5..15).random()
        }

        // 关系系数调节
        val currentIntimacy = currentRel?.intimacy ?: 0.0
        val coefficient = when {
            currentIntimacy < THRESHOLD_STRANGER -> 1.2  // 陌生人加成
            currentIntimacy > THRESHOLD_CLOSE_FRIEND -> 0.8 // 密友边际递减
            else -> 1.0
        }

        val newIntimacy = (currentIntimacy + delta * coefficient)
            .coerceIn(0.0, 100.0)

        // 更新关系
        memoryEngine.storeRelationship(
            fromId = fromId,
            toId = toId,
            type = RelationshipType.FRIEND_WITH,
            properties = mapOf("intimacy" to newIntimacy),
            validFrom = Instant.now()
        )

        // 检测阈值跨越
        val thresholdCrossed = checkThresholdCrossing(currentIntimacy, newIntimacy)

        IntimacyChangeResult(
            oldIntimacy = currentIntimacy,
            newIntimacy = newIntimacy,
            thresholdCrossed = thresholdCrossed
        )
    }

    /**
     * 每日衰减任务
     */
    suspend fun dailyDecay() = withContext(Dispatchers.IO) {
        val staleRelations = memoryEngine.getStaleRelationships(STALE_DAYS)
        
        staleRelations.forEach { rel ->
            val newIntimacy = (rel.intimacy - DAILY_DECAY).coerceAtLeast(0.0)
            
            memoryEngine.storeRelationship(
                fromId = rel.targetId,
                toId = rel.targetId, // 这里需要修正为实际的 fromId
                type = RelationshipType.FRIEND_WITH,
                properties = mapOf("intimacy" to newIntimacy),
                validFrom = Instant.now(),
                validTo = if (newIntimacy < THRESHOLD_STRANGER) Instant.now() else null
            )
        }
    }

    /**
     * 获取关系状态
     */
    suspend fun getRelationshipStatus(intimacy: Double): RelationshipStatus {
        return when {
            intimacy < THRESHOLD_STRANGER -> RelationshipStatus.STRANGER
            intimacy < THRESHOLD_ACQUAINTANCE -> RelationshipStatus.ACQUAINTANCE
            intimacy < THRESHOLD_FRIEND -> RelationshipStatus.FRIEND
            intimacy < THRESHOLD_CLOSE_FRIEND -> RelationshipStatus.GOOD_FRIEND
            else -> RelationshipStatus.BEST_FRIEND
        }
    }

    /**
     * 检测阈值跨越
     */
    private suspend fun checkThresholdCrossing(
        oldIntimacy: Double,
        newIntimacy: Double
    ): ThresholdCrossing? {
        // 突破 20：自动加好友
        if (oldIntimacy < THRESHOLD_STRANGER && newIntimacy >= THRESHOLD_STRANGER) {
            return ThresholdCrossing.BECOME_FRIENDS
        }
        // 跌破 20 持续 24 小时：触发关系破裂（由外部定时任务处理）
        if (oldIntimacy >= THRESHOLD_STRANGER && newIntimacy < THRESHOLD_STRANGER) {
            return ThresholdCrossing.BREAK_RELATIONSHIP
        }
        return null
    }

    /**
     * 创建私人群聊
     */
    suspend fun createPrivateGroupChat(
        characterAId: String,
        characterBId: String,
        characterAName: String,
        characterBName: String
    ): String = withContext(Dispatchers.IO) {
        val groupId = UUID.randomUUID().toString()
        val now = System.currentTimeMillis()

        val groupChat = GroupChat(
            id = groupId,
            name = "${characterAName}和${characterBName}",
            type = GroupChatType.PRIVATE,
            avatarUrl = null,
            creatorId = characterAId,
            createdAt = now,
            memberCount = 2,
            lastMessage = null,
            lastMessageTime = null,
            isActive = true
        )

        groupChatDao.insertGroupChat(groupChat)

        // 添加成员
        groupChatDao.insertMember(GroupChatMember(
            groupChatId = groupId,
            characterId = characterAId,
            joinedAt = now,
            isOwner = true
        ))

        groupChatDao.insertMember(GroupChatMember(
            groupChatId = groupId,
            characterId = characterBId,
            joinedAt = now,
            isOwner = false
        ))

        groupId
    }

    /**
     * 解散私人群聊
     */
    suspend fun dissolvePrivateGroupChat(groupId: String) = withContext(Dispatchers.IO) {
        groupChatDao.deactivateGroupChat(groupId)
    }
}

/**
 * 互动行为类型
 */
enum class InteractionAction {
    CHAT,           // 聊天
    LIKE,           // 点赞
    COMMENT,        // 评论
    MEET,           // 见面
    COLLABORATE,    // 合作
    CONFLICT,       // 冲突
    GIFT            // 赠送
}

/**
 * 关系状态
 */
enum class RelationshipStatus(val displayName: String) {
    STRANGER("陌生人"),
    ACQUAINTANCE("认识"),
    FRIEND("熟人"),
    GOOD_FRIEND("好友"),
    BEST_FRIEND("密友")
}

/**
 * 阈值跨越类型
 */
enum class ThresholdCrossing {
    BECOME_FRIENDS,      // 成为好友
    BREAK_RELATIONSHIP   // 关系破裂
}

/**
 * 亲密度变化结果
 */
data class IntimacyChangeResult(
    val oldIntimacy: Double,
    val newIntimacy: Double,
    val thresholdCrossed: ThresholdCrossing?
)
