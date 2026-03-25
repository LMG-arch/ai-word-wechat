package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.*
import com.ai.socialworld.domain.repository.ApiConfigRepository
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.domain.repository.RelationshipRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.random.Random

/**
 * 关系引擎
 * 管理角色间的亲密度和关系演变
 */
@Singleton
class RelationshipEngine @Inject constructor(
    private val relationshipRepository: RelationshipRepository,
    private val characterRepository: CharacterRepository,
    private val apiConfigRepository: ApiConfigRepository
) {
    
    // 亲密度阈值
    companion object {
        const val STRANGER_THRESHOLD = 20      // 陌生人
        const val ACQUAINTANCE_THRESHOLD = 40 // 认识
        const val FAMILIAR_THRESHOLD = 60      // 熟人
        const val FRIEND_THRESHOLD = 80        // 好友
        // 81-100: 密友
        
        // 关系衰减阈值（超过3天不互动）
        const val DECAY_DAYS = 3
        const val DECAY_AMOUNT = 1
    }
    
    /**
     * 处理互动
     * 更新亲密度并检测关系变化
     */
    suspend fun handleInteraction(
        fromCharacterId: String,
        toCharacterId: String,
        interactionType: InteractionType,
        additionalValue: Float = 0f
    ): RelationshipResult = withContext(Dispatchers.IO) {
        
        // 获取或创建关系
        var relationship = relationshipRepository.getRelationshipBetween(
            fromCharacterId, toCharacterId
        )
        
        if (relationship == null) {
            // 创建新关系
            relationship = Relationship(
                characterId = fromCharacterId,
                targetCharacterId = toCharacterId,
                intimacy = 0,
                status = RelationshipLevel.STRANGER,
                validFrom = System.currentTimeMillis()
            )
            relationshipRepository.insertRelationship(relationship)
        }
        
        // 计算亲密度变化
        val baseChange = calculateIntimacyChange(interactionType, additionalValue)
        
        // 应用关系系数
        val adjustedChange = applyRelationshipCoefficient(
            baseChange, 
            relationship.intimacy,
            relationship.interactionCount
        )
        
        val oldIntimacy = relationship.intimacy
        val newIntimacy = (relationship.intimacy + adjustedChange).coerceIn(0, 100)
        
        // 更新关系
        val updatedRelationship = relationship.copy(
            intimacy = newIntimacy,
            interactionCount = relationship.interactionCount + 1,
            lastInteractionAt = System.currentTimeMillis(),
            status = getRelationshipLevel(newIntimacy)
        )
        
        relationshipRepository.updateRelationship(updatedRelationship)
        
        // 检测阈值突破
        val thresholdCrossed = checkThresholdCrossing(oldIntimacy, newIntimacy)
        
        // 记录变化
        val change = RelationshipChange(
            relationshipId = relationship.id,
            oldIntimacy = oldIntimacy,
            newIntimacy = newIntimacy,
            changeAmount = adjustedChange,
            reason = interactionType.name,
            changedAt = System.currentTimeMillis()
        )
        relationshipRepository.insertChange(change)
        
        // 记录日志
        apiConfigRepository.addLog(
            characterId = fromCharacterId,
            characterName = null,
            logType = com.ai.socialworld.domain.repository.LogType.SOCIAL,
            content = "与${toCharacterId}互动: ${interactionType.name}, 亲密度 $oldIntimacy -> $newIntimacy"
        )
        
        RelationshipResult.Success(
            newIntimacy = newIntimacy,
            change = adjustedChange,
            thresholdCrossed = thresholdCrossed,
            newStatus = updatedRelationship.status
        )
    }
    
    /**
     * 计算亲密度变化
     */
    private fun calculateIntimacyChange(
        interactionType: InteractionType,
        additionalValue: Float
    ): Float {
        val baseChange = when (interactionType) {
            InteractionType.CHAT -> Random.nextInt(1, 4)      // +1~3
            InteractionType.LIKE -> 1f                        // +1
            InteractionType.COMMENT -> 2f                     // +2
            InteractionType.MEET -> Random.nextInt(2, 6).toFloat()  // +2~5
            InteractionType.COOPERATE -> Random.nextInt(1, 11).toFloat() // +1~10
            InteractionType.CONFLICT -> -Random.nextInt(5, 16).toFloat() // -5~15
            InteractionType.LONG_NO_INTERACTION -> -1f       // -1
            InteractionType.GIFT -> additionalValue.coerceIn(1f, 10f)
        }
        
        return baseChange
    }
    
    /**
     * 应用关系系数
     */
    private fun applyRelationshipCoefficient(
        baseChange: Float,
        currentIntimacy: Int,
        interactionCount: Int
    ): Float {
        val coefficient = when {
            // 初次互动
            interactionCount == 0 -> 1.2f
            // 密友间互动（边际效应递减）
            currentIntimacy >= FRIEND_THRESHOLD -> 0.8f
            // 普通情况
            else -> 1.0f
        }
        
        return baseChange * coefficient
    }
    
    /**
     * 检测阈值突破
     */
    private fun checkThresholdCrossing(oldIntimacy: Int, newIntimacy: Int): ThresholdCrossed? {
        return when {
            // 突破20：从陌生人变成认识
            oldIntimacy < STRANGER_THRESHOLD && newIntimacy >= STRANGER_THRESHOLD -> 
                ThresholdCrossed.BECOME_ACQUAINTED
            
            // 突破40：从认识变成熟人
            oldIntimacy < ACQUAINTANCE_THRESHOLD && newIntimacy >= ACQUAINTANCE_THRESHOLD -> 
                ThresholdCrossed.BECOME_FAMILIAR
            
            // 突破60：从熟人变成好友
            oldIntimacy < FAMILIAR_THRESHOLD && newIntimacy >= FAMILIAR_THRESHOLD -> 
                ThresholdCrossed.BECOME_FRIEND
            
            // 突破80：从好友变成密友
            oldIntimacy < FRIEND_THRESHOLD && newIntimacy >= FRIEND_THRESHOLD -> 
                ThresholdCrossed.BECOME_BEST_FRIEND
            
            // 跌破20：关系破裂
            oldIntimacy >= STRANGER_THRESHOLD && newIntimacy < STRANGER_THRESHOLD -> 
                ThresholdCrossed.RELATIONSHIP_BROKEN
            
            else -> null
        }
    }
    
    /**
     * 获取关系等级
     */
    fun getRelationshipLevel(intimacy: Int): RelationshipLevel {
        return when {
            intimacy < STRANGER_THRESHOLD -> RelationshipLevel.STRANGER
            intimacy < ACQUAINTANCE_THRESHOLD -> RelationshipLevel.ACQUAINTANCE
            intimacy < FAMILIAR_THRESHOLD -> RelationshipLevel.FAMILIAR
            intimacy < FRIEND_THRESHOLD -> RelationshipLevel.FRIEND
            else -> RelationshipLevel.BEST_FRIEND
        }
    }
    
    /**
     * 执行每日亲密度衰减
     */
    suspend fun performDailyDecay(): Int = withContext(Dispatchers.IO) {
        val now = System.currentTimeMillis()
        val threeDaysAgo = now - TimeUnit.DAYS.toMillis(DECAY_DAYS)
        
        // 获取所有超过3天未互动的关系
        val staleRelations = relationshipRepository.getStaleRelationships(threeDaysAgo)
        
        var decayCount = 0
        
        staleRelations.forEach { relationship ->
            if (relationship.intimacy > 0) {
                val newIntimacy = (relationship.intimacy - DECAY_AMOUNT).coerceAtLeast(0)
                
                val updated = relationship.copy(
                    intimacy = newIntimacy,
                    status = getRelationshipLevel(newIntimacy)
                )
                
                relationshipRepository.updateRelationship(updated)
                
                // 记录变化
                val change = RelationshipChange(
                    relationshipId = relationship.id,
                    oldIntimacy = relationship.intimacy,
                    newIntimacy = newIntimacy,
                    changeAmount = -DECAY_AMOUNT.toFloat(),
                    reason = "LONG_NO_INTERACTION",
                    changedAt = now
                )
                relationshipRepository.insertChange(change)
                
                decayCount++
                
                // 检查是否跌破阈值
                if (relationship.intimacy >= STRANGER_THRESHOLD && newIntimacy < STRANGER_THRESHOLD) {
                    // 触发关系破裂事件
                    handleRelationshipBroken(relationship)
                }
            }
        }
        
        decayCount
    }
    
    /**
     * 处理关系破裂
     */
    private suspend fun handleRelationshipBroken(relationship: Relationship) {
        // 记录关系结束时间
        val updated = relationship.copy(
            validTo = System.currentTimeMillis()
        )
        relationshipRepository.updateRelationship(updated)
        
        // 记录日志
        apiConfigRepository.addLog(
            characterId = relationship.characterId,
            characterName = null,
            logType = com.ai.socialworld.domain.repository.LogType.SOCIAL,
            content = "与${relationship.targetCharacterId}的关系破裂"
        )
        
        // TODO: 解散私人群聊（如果需要）
    }
    
    /**
     * 检查是否可以创建公司
     */
    suspend fun canCreateCompany(
        founderId: String,
        coFounderId: String
    ): Boolean = withContext(Dispatchers.IO) {
        val relationship = relationshipRepository.getRelationshipBetween(founderId, coFounderId)
        
        relationship != null && relationship.intimacy >= FAMILIAR_THRESHOLD
    }
    
    /**
     * 获取好友列表
     */
    suspend fun getFriends(
        characterId: String,
        minIntimacy: Int = STRANGER_THRESHOLD
    ): List<Relationship> = withContext(Dispatchers.IO) {
        relationshipRepository.getRelationshipsByCharacter(characterId)
            .filter { it.intimacy >= minIntimacy }
            .sortedByDescending { it.intimacy }
    }
    
    /**
     * 获取关系系数（用于对话等）
     */
    suspend fun getRelationshipCoefficient(
        characterId: String,
        targetId: String
    ): Float = withContext(Dispatchers.IO) {
        val relationship = relationshipRepository.getRelationshipBetween(characterId, targetId)
        
        when {
            relationship == null -> 1.2f  // 初次见面
            relationship.intimacy >= FRIEND_THRESHOLD -> 0.8f  // 密友
            else -> 1.0f
        }
    }
}

// ==================== 枚举和数据类 ====================

/**
 * 互动类型
 */
enum class InteractionType {
    CHAT,               // 聊天
    LIKE,               // 点赞
    COMMENT,            // 评论
    MEET,               // 见面
    COOPERATE,          // 合作
    CONFLICT,           // 冲突
    LONG_NO_INTERACTION,// 长期不互动
    GIFT                // 送礼
}

/**
 * 关系等级
 */
enum class RelationshipLevel {
    STRANGER,       // 陌生人 (0-19)
    ACQUAINTANCE,   // 认识 (20-39)
    FAMILIAR,       // 熟人 (40-59)
    FRIEND,         // 好友 (60-79)
    BEST_FRIEND     // 密友 (80-100)
}

/**
 * 阈值突破类型
 */
enum class ThresholdCrossed {
    BECOME_ACQUAINTED,  // 变成认识
    BECOME_FAMILIAR,    // 变成熟人
    BECOME_FRIEND,      // 变成好友
    BECOME_BEST_FRIEND, // 变成密友
    RELATIONSHIP_BROKEN // 关系破裂
}

/**
 * 关系操作结果
 */
sealed class RelationshipResult {
    data class Success(
        val newIntimacy: Int,
        val change: Float,
        val thresholdCrossed: ThresholdCrossed?,
        val newStatus: RelationshipLevel
    ) : RelationshipResult()
    
    data class Error(val message: String) : RelationshipResult()
}
