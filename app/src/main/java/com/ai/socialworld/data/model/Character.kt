package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.io.Serializable

enum class LifeStage : Serializable {
    CHILD,
    TEEN,
    ADULT,
    MIDDLE_AGED,
    SENIOR
}

@Entity(tableName = "characters")
data class Character(
    @PrimaryKey
    val id: String,
    val name: String,
    val age: Int,
    val gender: String,
    val occupation: String,
    val personality: String,
    val money: Double = 50.0,
    val createdAt: Long = System.currentTimeMillis(),
    val avatarUrl: String? = null,
    val signature: String? = null,
    val currentMood: String? = null,
    val lifeStage: LifeStage = LifeStage.ADULT
) : Serializable
) : Serializable
