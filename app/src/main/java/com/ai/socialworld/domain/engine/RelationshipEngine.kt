package com.ai.socialworld.domain.engine

import com.ai.socialworld.data.model.*
import com.ai.socialworld.domain.repository.MemoryRepository
import com.ai.socialworld.domain.service.TimeDecayService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 关系引擎
 * 处理亲密度计算、关系演变、社交互动等
 */
@Singleton
class RelationshipEngine @Inject constructor(
    private val memoryRepository: MemoryRepository,
    private val timeDecayService: TimeDecayService
) {
    /**
     * 更新亲密度
     */
    suspend fun updateIntimacy(
        fromId: String,
        toId: String,
        action: InteractionAction
    ): Int {
        // 获取当前关系
        val currentRel = memoryRepository.getCurrentRelationship(fromId, toId)
        val currentIntimacy = currentRel?.intimacy ?: 0
        
        // 计算变化值
        val delta = action.calculateDelta()
        
        // 关系系数调节
        val coefficient = when {
            currentIntimacy in 0..20 -> RelationshipCoefficient.STRANGER
            currentIntimacy in 81..100 -> RelationshipCoefficient.CLOSE_FRIEND
            else -> 1.0
        }
        
        val newIntimacy = (currentIntimacy + delta * coefficient).toInt()
            .coerceIn(0, 100)
        
        // 存储关系（带时间戳）
        memoryRepository.storeRelationship(
            fromId = fromId,
            toId = toId,
            type = RelationshipType.FRIEND_WITH,
            properties = mapOf("intimacy" to newIntimacy),
            validFrom = currentRel?.validFrom ?: Instant.now(),
            validTo = if (newIntimacy < 20) Instant.now() else null
        )
        
        // 检查阈值变化
        checkThresholdCrossing(fromId, toId, currentIntimacy, newIntimacy)
        
        return newIntimacy
    }
    
    /**
     * 每日衰减任务
     */
    suspend fun dailyDecay() {
        val staleRelations = memoryRepository.getStaleRelationships(3)
        staleRelations.forEach { rel ->
            val newIntimacy = (rel.intimacy - 1).coerceAtLeast(0)
            memoryRepository.storeRelationship(
                fromId = rel.fromId,
                toId = rel.toId,
                type = RelationshipType.FRIEND_WITH,
                properties = mapOf("intimacy" to newIntimacy),
                validFrom = rel.validFrom,
                validTo = if (newIntimacy < 20) Instant.now() else null
            )
        }
    }
    
    /**
     * 检查阈值变化
     */
    private suspend fun checkThresholdCrossing(
        fromId: String,
        toId: String,
        oldIntimacy: Int,
        newIntimacy: Int
    ) {
        // 突破20：自动加好友，创建私人群聊
        if (oldIntimacy < 20 && newIntimacy >= 20) {
            // TODO: 创建私人群聊
        }
        
        // 跌破20持续24小时：触发关系破裂
        if (oldIntimacy >= 20 && newIntimacy < 20) {
            // TODO: 触发关系破裂事件
        }
    }
    
    /**
     * 获取关系状态
     */
    fun getRelationshipStatus(intimacy: Int): RelationshipStatus {
        return when (intimacy) {
            in 0..20 -> RelationshipStatus.STRANGER
            in 21..40 -> RelationshipStatus.ACQUAINTANCE
            in 41..60 -> RelationshipStatus.FAMILIAR
            in 61..80 -> RelationshipStatus.FRIEND
            in 81..100 -> RelationshipStatus.CLOSE_FRIEND
            else -> RelationshipStatus.STRANGER
        }
    }
}
