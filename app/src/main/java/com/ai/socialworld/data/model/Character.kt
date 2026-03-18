package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.Instant

/**
 * 角色实体（Room 数据库）
 */
@Entity(tableName = "characters")
data class Character(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    val name: String,
    
    val description: String = "",
    
    val avatarUrl: String? = null,
    
    val personality: String = "",
    
    val background: String = "",
    
    val createdAt: Instant = Instant.now(),
    
    val updatedAt: Instant = Instant.now(),
    
    val isDeleted: Boolean = false
)
