package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.Relationship
import com.ai.socialworld.data.model.RelationshipChange
import kotlinx.coroutines.flow.Flow

/**
 * 关系仓库接口
 */
interface RelationshipRepository {
    
    /**
     * 插入关系
     */
    suspend fun insertRelationship(relationship: Relationship): Long
    
    /**
     * 更新关系
     */
    suspend fun updateRelationship(relationship: Relationship)
    
    /**
     * 删除关系
     */
    suspend fun deleteRelationship(relationship: Relationship)
    
    /**
     * 获取两个角色之间的关系
     */
    suspend fun getRelationshipBetween(characterId: String, targetId: String): Relationship?
    
    /**
     * 获取角色的所有关系
     */
    suspend fun getRelationshipsByCharacter(characterId: String): List<Relationship>
    
    /**
     * 获取角色的所有关系（Flow）
     */
    fun getRelationshipsByCharacterFlow(characterId: String): Flow<List<Relationship>>
    
    /**
     * 获取超过指定时间未互动的关系
     */
    suspend fun getStaleRelationships(beforeTime: Long): List<Relationship>
    
    /**
     * 插入关系变化记录
     */
    suspend fun insertChange(change: RelationshipChange)
    
    /**
     * 获取关系变化历史
     */
    suspend fun getRelationshipHistory(relationshipId: String): List<RelationshipChange>
    
    /**
     * 获取高亲密度关系
     */
    suspend fun getHighIntimacyRelationships(
        characterId: String,
        minIntimacy: Int
    ): List<Relationship>
}
