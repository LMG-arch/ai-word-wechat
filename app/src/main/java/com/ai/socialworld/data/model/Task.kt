package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 任务状态
 */
enum class TaskStatus {
    PENDING,      // 待分配
    ASSIGNED,     // 已分配
    IN_PROGRESS,  // 进行中
    COMPLETED,    // 已完成
    FAILED,       // 失败
    CANCELLED     // 已取消
}

/**
 * 任务难度
 */
enum class TaskDifficulty {
    EASY,     // 简单
    MEDIUM,   // 中等
    HARD,     // 困难
    EPIC      // 史诗
}

/**
 * 任务类型
 */
enum class TaskType {
    DESIGN,       // 设计任务
    DEVELOPMENT,  // 开发任务
    WRITING,      // 写作任务
    RESEARCH,     // 研究任务
    SOCIAL,       // 社交任务
    GENERAL       // 通用任务
}

/**
 * 任务实体
 */
@Entity(tableName = "tasks")
data class Task(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val title: String,                    // 任务标题
    val description: String,              // 任务描述
    val type: TaskType = TaskType.GENERAL, // 任务类型
    val difficulty: TaskDifficulty = TaskDifficulty.MEDIUM, // 难度
    val reward: Int = 100,                // 奖励资金
    val deadline: Long? = null,           // 截止时间 (Long)
    val status: TaskStatus = TaskStatus.PENDING, // 状态
    val assigneeId: Long? = null,         // 被分配者ID
    val creatorId: Long? = null,          // 创建者ID
    val createdAt: Long = System.currentTimeMillis(), // 创建时间 (Long)
    val completedAt: Long? = null,        // 完成时间 (Long)
    val requiredSkills: String = "",      // 所需技能（JSON）
    val deliverable: String = "",         // 交付物要求
    val evaluationCriteria: String = ""   // 评估标准
)

/**
 * 任务提交记录
 */
@Entity(tableName = "task_submissions")
data class TaskSubmission(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val taskId: Long,                     // 任务ID
    val characterId: Long,                // 提交者ID
    val content: String,                  // 提交内容
    val attachments: String = "",         // 附件（JSON）
    val submittedAt: Long = System.currentTimeMillis(), // 提交时间 (Long)
    val score: Int? = null,               // 评分
    val feedback: String = "",            // 反馈
    val isAccepted: Boolean = false       // 是否被接受
)
