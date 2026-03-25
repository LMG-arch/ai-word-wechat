package com.ai.socialworld.data.local

import androidx.room.*
import com.ai.socialworld.data.model.Relationship
import com.ai.socialworld.data.model.RelationshipChange
import kotlinx.coroutines.flow.Flow

/**
 * 关系DAO
 */
@Dao
interface RelationshipDao {
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(relationship: Relationship): Long
    
    @Update
    suspend fun update(relationship: Relationship)
    
    @Delete
    suspend fun delete(relationship: Relationship)
    
    @Query("SELECT * FROM relationships WHERE characterId = :characterId AND targetCharacterId = :targetId LIMIT 1")
    suspend fun getRelationshipBetween(characterId: String, targetId: String): Relationship?
    
    @Query("SELECT * FROM relationships WHERE characterId = :characterId ORDER BY intimacy DESC")
    suspend fun getRelationshipsByCharacter(characterId: String): List<Relationship>
    
    @Query("SELECT * FROM relationships WHERE characterId = :characterId ORDER BY intimacy DESC")
    fun getRelationshipsByCharacterFlow(characterId: String): Flow<List<Relationship>>
    
    @Query("SELECT * FROM relationships WHERE lastInteractionAt < :beforeTime AND intimacy > 0")
    suspend fun getStaleRelationships(beforeTime: Long): List<Relationship>
    
    @Query("SELECT * FROM relationships WHERE characterId = :characterId AND intimacy >= :minIntimacy ORDER BY intimacy DESC")
    suspend fun getHighIntimacyRelationships(characterId: String, minIntimacy: Int): List<Relationship>
    
    @Query("DELETE FROM relationships WHERE characterId = :characterId AND targetCharacterId = :targetId")
    suspend fun deleteRelationshipBetween(characterId: String, targetId: String)
    
    // ==================== 关系变化记录 ====================
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertChange(change: RelationshipChange)
    
    @Query("SELECT * FROM relationship_changes WHERE relationshipId = :relationshipId ORDER BY changedAt DESC")
    suspend fun getRelationshipHistory(relationshipId: String): List<RelationshipChange>
    
    @Query("SELECT * FROM relationship_changes WHERE relationshipId = :relationshipId ORDER BY changedAt DESC LIMIT :limit")
    suspend fun getRecentRelationshipHistory(relationshipId: String, limit: Int): List<RelationshipChange>
}
