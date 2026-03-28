package com.ai.wechat.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 任务实体
 */
@Entity(tableName = "tasks")
data class Task(
    @PrimaryKey
    val id: String,
    val title: String,
    val description: String,
    val type: TaskType,
    val reward: Double,
    val status: TaskStatus = TaskStatus.PENDING,
    val requirements: String?,
    val assigneeType: AssigneeType = AssigneeType.INDIVIDUAL,
    val assigneeId: String?,
    val companyId: String?,
    val creatorId: String,
    val createdAt: Long,
    val deadlineAt: Long?,
    val completedAt: Long?,
    val result: String?,
    val imageUrl: String?
)

/**
 * 任务类型
 */
enum class TaskType {
    TEXT_GENERATION,  // 文本生成
    IMAGE_GENERATION, // 图像生成
    CODE_WRITING,     // 代码编写
    RESEARCH,         // 调研分析
    CREATIVE_DESIGN   // 创意设计
}

/**
 * 任务状态
 */
enum class TaskStatus {
    PENDING,      // 待接取
    IN_PROGRESS,  // 进行中
    REVIEWING,    // 审核中
    COMPLETED,    // 已完成
    FAILED        // 失败
}

/**
 * 接取主体类型
 */
enum class AssigneeType {
    INDIVIDUAL, // 个人
    COMPANY     // 公司
}
