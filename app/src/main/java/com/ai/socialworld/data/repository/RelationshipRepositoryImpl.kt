package com.ai.socialworld.data.repository

import com.ai.socialworld.data.local.RelationshipDao
import com.ai.socialworld.data.model.Relationship
import com.ai.socialworld.data.model.RelationshipChange
import com.ai.socialworld.domain.repository.RelationshipRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 关系仓库实现
 */
@Singleton
class RelationshipRepositoryImpl @Inject constructor(
    private val relationshipDao: RelationshipDao
) : RelationshipRepository {
    
    override suspend fun insertRelationship(relationship: Relationship): Long {
        return relationshipDao.insert(relationship)
    }
    
    override suspend fun updateRelationship(relationship: Relationship) {
        relationshipDao.update(relationship)
    }
    
    override suspend fun deleteRelationship(relationship: Relationship) {
        relationshipDao.delete(relationship)
    }
    
    override suspend fun getRelationshipBetween(characterId: String, targetId: String): Relationship? {
        return relationshipDao.getRelationshipBetween(characterId, targetId)
    }
    
    override suspend fun getRelationshipsByCharacter(characterId: String): List<Relationship> {
        return relationshipDao.getRelationshipsByCharacter(characterId)
    }
    
    override fun getRelationshipsByCharacterFlow(characterId: String): Flow<List<Relationship>> {
        return relationshipDao.getRelationshipsByCharacterFlow(characterId)
    }
    
    override suspend fun getStaleRelationships(beforeTime: Long): List<Relationship> {
        return relationshipDao.getStaleRelationships(beforeTime)
    }
    
    override suspend fun insertChange(change: RelationshipChange) {
        relationshipDao.insertChange(change)
    }
    
    override suspend fun getRelationshipHistory(relationshipId: String): List<RelationshipChange> {
        return relationshipDao.getRelationshipHistory(relationshipId)
    }
    
    override suspend fun getHighIntimacyRelationships(
        characterId: String,
        minIntimacy: Int
    ): List<Relationship> {
        return relationshipDao.getHighIntimacyRelationships(characterId, minIntimacy)
    }
}
