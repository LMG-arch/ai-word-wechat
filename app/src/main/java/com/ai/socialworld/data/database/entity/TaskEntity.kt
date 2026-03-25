package com.ai.socialworld.data.database.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.ai.socialworld.data.database.Converters
import com.ai.socialworld.data.model.AssigneeType
import com.ai.socialworld.data.model.TaskStatus
import com.ai.socialworld.data.model.TaskType
import java.time.Instant

/**
 * 任务实体（Room数据库）
 */
@Entity(tableName = "tasks")
@TypeConverters(Converters::class)
data class TaskEntity(
    @PrimaryKey
    val id: String,
    val title: String,
    val description: String,
    val type: TaskType,
    val reward: Int,
    val status: TaskStatus = TaskStatus.PENDING,
    val requirements: String = "",
    val createdAt: Long = System.currentTimeMillis(),
    val deadline: Long? = null,
    val assigneeType: AssigneeType = AssigneeType.PERSONAL,
    val assigneeId: String? = null,
    val companyId: String? = null,
    val progress: Int = 0,
    val result: String? = null,
    val reflectionId: String? = null,
    val isDeleted: Boolean = false
)
