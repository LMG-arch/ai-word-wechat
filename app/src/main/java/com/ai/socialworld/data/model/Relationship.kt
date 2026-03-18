package com.ai.socialworld.data.model

data class Relationship(
    val id: Long,
    val fromCharacterId: Long,
    val toCharacterId: Long,
    val type: RelationshipType,
    val strength: Float,
    val createdAt: Long
)

enum class RelationshipType {
    FRIEND,
    FAMILY,
    COLLEAGUE,
    ACQUAINTANCE,
    STRANGER,
    ENEMY
}
