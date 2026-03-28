package com.ai.wechat.service

import com.ai.wechat.data.memory.MemoryEngine
import com.ai.wechat.data.memory.MemoryType
import com.ai.wechat.data.model.*
import com.ai.wechat.db.dao.TaskDao
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 任务系统
 * 负责任务管理、执行、审核
 */
@Singleton
class TaskSystem @Inject constructor(
    private val taskDao: TaskDao,
    private val memoryEngine: MemoryEngine,
    private val aiWeChatService: AiWeChatService,
    private val economyService: EconomyService
) {

    /**
     * 创建任务
     */
    suspend fun createTask(
        title: String,
        description: String,
        type: TaskType,
        reward: Double,
        assigneeType: AssigneeType,
        creatorId: String,
        deadlineAt: Long? = null,
        requirements: String? = null
    ): Result<Task> = withContext(Dispatchers.IO) {
        try {
            val taskId = UUID.randomUUID().toString()
            val now = System.currentTimeMillis()

            val task = Task(
                id = taskId,
                title = title,
                description = description,
                type = type,
                reward = reward,
                status = TaskStatus.PENDING,
                requirements = requirements,
                assigneeType = assigneeType,
                assigneeId = null,
                companyId = null,
                creatorId = creatorId,
                createdAt = now,
                deadlineAt = deadlineAt,
                completedAt = null,
                result = null,
                imageUrl = null
            )

            taskDao.insertTask(task)
            Result.success(task)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 接取任务（个人）
     */
    suspend fun acceptTask(
        taskId: String,
        characterId: String
    ): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val task = taskDao.getTaskById(taskId)
                ?: return@withContext Result.failure(Exception("任务不存在"))

            if (task.status != TaskStatus.PENDING) {
                return@withContext Result.failure(Exception("任务已被接取"))
            }

            if (task.assigneeType != AssigneeType.INDIVIDUAL) {
                return@withContext Result.failure(Exception("该任务只能由公司接取"))
            }

            taskDao.updateTask(task.copy(
                assigneeId = characterId,
                status = TaskStatus.IN_PROGRESS
            ))

            memoryEngine.storeMemory(
                characterId = characterId,
                content = "${characterId}接取了任务：${task.title}",
                type = MemoryType.TASK,
                importance = 0.6f
            )

            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 执行个人任务
     */
    suspend fun executePersonalTask(
        taskId: String
    ): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val task = taskDao.getTaskById(taskId)
                ?: return@withContext Result.failure(Exception("任务不存在"))

            val characterId = task.assigneeId
                ?: return@withContext Result.failure(Exception("任务未分配"))

            // 根据任务类型生成成果
            val result = when (task.type) {
                TaskType.IMAGE -> {
                    val prompt = task.description
                    aiWeChatService.generateImage(prompt).getOrNull()
                        ?: return@withContext Result.failure(Exception("图像生成失败"))
                }
                TaskType.TEXT, TaskType.CODE, TaskType.RESEARCH, TaskType.CREATIVE_DESIGN -> {
                    val prompt = task.description
                    aiWeChatService.generateText(prompt).getOrNull()
                        ?: return@withContext Result.failure(Exception("文本生成失败"))
                }
            }

            // 提交审核
            taskDao.updateTask(task.copy(
                result = result,
                status = TaskStatus.REVIEWING
            ))

            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 用户审核任务
     */
    suspend fun approveTask(
        taskId: String,
        approved: Boolean
    ): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val task = taskDao.getTaskById(taskId)
                ?: return@withContext Result.failure(Exception("任务不存在"))

            if (task.status != TaskStatus.REVIEWING) {
                return@withContext Result.failure(Exception("任务不在审核状态"))
            }

            val characterId = task.assigneeId ?: ""
            val now = System.currentTimeMillis()

            if (approved) {
                // 发放奖励
                economyService.transferMoney("SYSTEM", characterId, task.reward)

                // 完成任务
                taskDao.updateTask(task.copy(
                    status = TaskStatus.COMPLETED,
                    completedAt = now
                ))

                // 触发反思
                // （由外部调用 ReflectionEngine 处理）

                memoryEngine.storeMemory(
                    characterId = characterId,
                    content = "${characterId}完成任务\"${task.title}\"，获得${task.reward}奖励",
                    type = MemoryType.TASK,
                    importance = 0.7f
                )
            } else {
                // 审核不通过
                taskDao.updateTask(task.copy(
                    status = TaskStatus.FAILED
                ))

                memoryEngine.storeMemory(
                    characterId = characterId,
                    content = "${characterId}的任务\"${task.title}\"未通过审核",
                    type = MemoryType.TASK,
                    importance = 0.8f
                )
            }

            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 获取所有任务
     */
    fun getAllTasks(): Flow<List<Task>> = taskDao.getAllTasks()

    /**
     * 获取任务详情
     */
    suspend fun getTask(taskId: String): Task? = taskDao.getTaskById(taskId)

    /**
     * 获取角色的任务
     */
    fun getTasksByCharacter(characterId: String): Flow<List<Task>> =
        taskDao.getTasksByAssignee(characterId)
}
