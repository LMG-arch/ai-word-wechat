package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.*
import com.ai.socialworld.domain.repository.ApiConfigRepository
import com.ai.socialworld.domain.repository.TaskRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 任务执行服务
 * 处理个人任务和公司任务的执行流程
 */
@Singleton
class TaskExecutionService @Inject constructor(
    private val taskRepository: TaskRepository,
    private val languageModelService: LanguageModelService,
    private val imageGenerationService: ImageGenerationService,
    private val reflectionEngine: ReflectionEngine,
    private val apiConfigRepository: ApiConfigRepository
) {
    
    /**
     * 执行个人任务
     */
    suspend fun executePersonalTask(
        taskId: String,
        characterId: String
    ): TaskResult = withContext(Dispatchers.IO) {
        
        // 1. 获取任务
        val task = taskRepository.getTaskById(taskId)
            ?: return@withContext TaskResult.Error("任务不存在")
        
        if (task.status != TaskStatus.ASSIGNED && task.status != TaskStatus.PENDING) {
            return@withContext TaskResult.Error("任务状态不正确: ${task.status}")
        }
        
        // 2. 更新状态为进行中
        taskRepository.updateTaskStatus(taskId, TaskStatus.IN_PROGRESS)
        
        // 3. 生成成果
        val generateResult = generateTaskOutput(task, characterId)
        
        when (generateResult) {
            is GenerateResult.Success -> {
                // 4. 创建提交记录
                val submission = TaskSubmission(
                    taskId = taskId,
                    characterId = characterId,
                    content = generateResult.content,
                    submittedAt = System.currentTimeMillis(),
                    status = SubmissionStatus.PENDING_REVIEW
                )
                
                taskRepository.insertSubmission(submission)
                
                // 5. 记录日志
                apiConfigRepository.addLog(
                    characterId = characterId,
                    characterName = null,
                    logType = com.ai.socialworld.domain.repository.LogType.TASK,
                    content = "开始执行任务: ${task.title}"
                )
                
                TaskResult.Success(
                    submissionId = submission.id,
                    message = "任务初稿已生成，等待审核"
                )
            }
            is GenerateResult.Error -> {
                // 任务执行失败
                taskRepository.updateTaskStatus(taskId, TaskStatus.FAILED)
                
                TaskResult.Error(generateResult.message)
            }
        }
    }
    
    /**
     * 审核任务提交
     */
    suspend fun reviewSubmission(
        submissionId: String,
        approved: Boolean,
        feedback: String = ""
    ): TaskResult = withContext(Dispatchers.IO) {
        
        val submission = taskRepository.getSubmissionById(submissionId)
            ?: return@withContext TaskResult.Error("提交记录不存在")
        
        val task = taskRepository.getTaskById(submission.taskId)
            ?: return@withContext TaskResult.Error("任务不存在")
        
        if (approved) {
            // 通过审核
            taskRepository.updateSubmissionStatus(
                submissionId, 
                SubmissionStatus.APPROVED
            )
            
            // 发放奖励
            val rewardResult = distributeReward(task, submission.characterId)
            
            // 更新任务状态
            taskRepository.updateTaskStatus(task.id, TaskStatus.COMPLETED)
            
            // 触发反思
            reflectionEngine.triggerReflection(
                taskId = task.id,
                characterId = submission.characterId,
                success = true
            )
            
            // 记录日志
            apiConfigRepository.addLog(
                characterId = submission.characterId,
                characterName = null,
                logType = com.ai.socialworld.domain.repository.LogType.TASK,
                content = "完成任务: ${task.title}, 获得奖励 ${task.reward}"
            )
            
            TaskResult.Success(
                message = "任务完成！获得奖励: ${task.reward} 资金"
            )
        } else {
            // 拒绝
            taskRepository.updateSubmissionStatus(
                submissionId,
                SubmissionStatus.REJECTED
            )
            
            // 记录反馈
            taskRepository.addSubmissionFeedback(submissionId, feedback)
            
            TaskResult.Success(
                message = "任务被拒绝，请修改后重新提交"
            )
        }
    }
    
    /**
     * 执行公司任务
     */
    suspend fun executeCompanyTask(
        taskId: String,
        companyId: String,
        executorId: String
    ): TaskResult = withContext(Dispatchers.IO) {
        
        val task = taskRepository.getTaskById(taskId)
            ?: return@withContext TaskResult.Error("任务不存在")
        
        // 更新状态
        taskRepository.updateTaskStatus(taskId, TaskStatus.IN_PROGRESS)
        taskRepository.updateTaskAssignee(taskId, executorId)
        
        // 生成初稿
        val generateResult = generateTaskOutput(task, executorId)
        
        when (generateResult) {
            is GenerateResult.Success -> {
                val submission = TaskSubmission(
                    taskId = taskId,
                    characterId = executorId,
                    content = generateResult.content,
                    submittedAt = System.currentTimeMillis(),
                    status = SubmissionStatus.PENDING_VOTE
                )
                
                taskRepository.insertSubmission(submission)
                
                // 记录日志
                apiConfigRepository.addLog(
                    characterId = executorId,
                    characterName = null,
                    logType = com.ai.socialworld.domain.repository.LogType.TASK,
                    content = "公司任务初稿完成: ${task.title}"
                )
                
                TaskResult.Success(
                    submissionId = submission.id,
                    message = "初稿已提交，等待团队投票"
                )
            }
            is GenerateResult.Error -> {
                TaskResult.Error(generateResult.message)
            }
        }
    }
    
    /**
     * 公司投票
     */
    suspend fun voteOnSubmission(
        submissionId: String,
        companyId: String,
        voterId: String,
        approved: Boolean,
        comment: String = ""
    ): VoteResult = withContext(Dispatchers.IO) {
        
        val submission = taskRepository.getSubmissionById(submissionId)
            ?: return@withContext VoteResult.Error("提交不存在")
        
        val company = taskRepository.getCompanyById(companyId)
            ?: return@withContext VoteResult.Error("公司不存在")
        
        // 检查投票者是否是公司成员
        val members = taskRepository.getCompanyMembers(companyId)
        if (members.none { it.characterId == voterId }) {
            return@withContext VoteResult.Error("非公司成员，无权投票")
        }
        
        // 记录投票
        val vote = Vote(
            submissionId = submissionId,
            characterId = voterId,
            approved = approved,
            comment = comment,
            votedAt = System.currentTimeMillis()
        )
        
        taskRepository.insertVote(vote)
        
        // 检查投票结果
        val votes = taskRepository.getVotesBySubmission(submissionId)
        val totalMembers = members.size
        val participationRate = votes.size.toFloat() / totalMembers
        val approvalRate = votes.count { it.approved }.toFloat() / votes.size.coerceAtLeast(1)
        
        // 检查是否达到投票阈值
        if (participationRate >= 0.5f) {
            // 参与率达标
            if (approvalRate >= 0.6f) {
                // 赞成率达标，通过
                return@withContext VoteResult.Passed(
                    approvalRate = approvalRate,
                    participationRate = participationRate
                )
            } else if (votes.size == totalMembers) {
                // 所有人都投票了但未通过
                return@withContext VoteResult.Rejected(
                    approvalRate = approvalRate,
                    needRevision = true
                )
            }
        }
        
        // 等待更多投票
        VoteResult.Pending(
            currentParticipation = votes.size,
            totalMembers = totalMembers,
            currentApproval = votes.count { it.approved },
            requiredParticipation = (totalMembers * 0.5f).toInt().coerceAtLeast(1)
        )
    }
    
    /**
     * 重新提交（修改后）
     */
    suspend fun reviseSubmission(
        submissionId: String,
        characterId: String
    ): TaskResult = withContext(Dispatchers.IO) {
        
        val oldSubmission = taskRepository.getSubmissionById(submissionId)
            ?: return@withContext TaskResult.Error("提交不存在")
        
        val task = taskRepository.getTaskById(oldSubmission.taskId)
            ?: return@withContext TaskResult.Error("任务不存在")
        
        // 检查修改次数
        val submissions = taskRepository.getSubmissionsByTask(task.id)
        if (submissions.size >= 3) {
            return@withContext TaskResult.Error("修改次数已达上限（最多3次）")
        }
        
        // 生成新版本
        val feedbacks = submissions.mapNotNull { it.feedback }
        val generateResult = generateTaskOutputWithFeedback(task, characterId, feedbacks)
        
        when (generateResult) {
            is GenerateResult.Success -> {
                val newSubmission = TaskSubmission(
                    taskId = task.id,
                    characterId = characterId,
                    content = generateResult.content,
                    submittedAt = System.currentTimeMillis(),
                    status = SubmissionStatus.PENDING_VOTE,
                    version = submissions.size + 1
                )
                
                taskRepository.insertSubmission(newSubmission)
                
                TaskResult.Success(
                    submissionId = newSubmission.id,
                    message = "新版本已提交，等待投票"
                )
            }
            is GenerateResult.Error -> {
                TaskResult.Error(generateResult.message)
            }
        }
    }
    
    /**
     * 生成任务输出
     */
    private suspend fun generateTaskOutput(
        task: Task,
        characterId: String
    ): GenerateResult {
        return when (task.type) {
            TaskType.TEXT -> {
                languageModelService.generateChatResponse(
                    character = Character(name = ""), // TODO: 获取角色
                    userMessage = "请完成以下任务：\n${task.description}",
                    relatedMemories = emptyList()
                ).let { result ->
                    when (result) {
                        is ChatResult.Success -> GenerateResult.Success(result.content)
                        is ChatResult.Error -> GenerateResult.Error(result.message)
                    }
                }
            }
            TaskType.IMAGE -> {
                // 图像生成
                imageGenerationService.generateTaskImage(
                    taskDescription = task.description,
                    style = ImageStyle.EPIC
                ).let { result ->
                    when (result) {
                        is com.ai.socialworld.domain.service.ImageResult.Success -> 
                            GenerateResult.Success(result.imageUrl)
                        is com.ai.socialworld.domain.service.ImageResult.Error -> 
                            GenerateResult.Error(result.message)
                    }
                }
            }
            TaskType.CODE -> {
                languageModelService.generateChatResponse(
                    character = Character(name = ""),
                    userMessage = "请编写代码完成以下任务：\n${task.description}\n\n只输出代码，不要解释。",
                    relatedMemories = emptyList()
                ).let { result ->
                    when (result) {
                        is ChatResult.Success -> GenerateResult.Success(result.content)
                        is ChatResult.Error -> GenerateResult.Error(result.message)
                    }
                }
            }
            TaskType.RESEARCH -> {
                languageModelService.generateChatResponse(
                    character = Character(name = ""),
                    userMessage = "请调研以下主题并输出报告：\n${task.description}",
                    relatedMemories = emptyList()
                ).let { result ->
                    when (result) {
                        is ChatResult.Success -> GenerateResult.Success(result.content)
                        is ChatResult.Error -> GenerateResult.Error(result.message)
                    }
                }
            }
            TaskType.DESIGN -> {
                imageGenerationService.generateTaskImage(
                    taskDescription = task.description,
                    style = ImageStyle.EPIC
                ).let { result ->
                    when (result) {
                        is com.ai.socialworld.domain.service.ImageResult.Success -> 
                            GenerateResult.Success(result.imageUrl)
                        is com.ai.socialworld.domain.service.ImageResult.Error -> 
                            GenerateResult.Error(result.message)
                    }
                }
            }
        }
    }
    
    /**
     * 基于反馈重新生成
     */
    private suspend fun generateTaskOutputWithFeedback(
        task: Task,
        characterId: String,
        feedbacks: List<String>
    ): GenerateResult {
        val prompt = buildString {
            append("请完成以下任务：\n${task.description}\n\n")
            if (feedbacks.isNotEmpty()) {
                append("之前的反馈意见：\n")
                feedbacks.forEachIndexed { index, feedback ->
                    append("${index + 1}. $feedback\n")
                }
                append("\n请根据反馈修改。")
            }
        }
        
        return when (task.type) {
            TaskType.TEXT, TaskType.CODE, TaskType.RESEARCH -> {
                languageModelService.generateChatResponse(
                    character = Character(name = ""),
                    userMessage = prompt,
                    relatedMemories = emptyList()
                ).let { result ->
                    when (result) {
                        is ChatResult.Success -> GenerateResult.Success(result.content)
                        is ChatResult.Error -> GenerateResult.Error(result.message)
                    }
                }
            }
            TaskType.IMAGE, TaskType.DESIGN -> {
                imageGenerationService.generateTaskImage(
                    taskDescription = prompt,
                    style = ImageStyle.EPIC
                ).let { result ->
                    when (result) {
                        is com.ai.socialworld.domain.service.ImageResult.Success -> 
                            GenerateResult.Success(result.imageUrl)
                        is com.ai.socialworld.domain.service.ImageResult.Error -> 
                            GenerateResult.Error(result.message)
                    }
                }
            }
        }
    }
    
    /**
     * 发放奖励
     */
    private suspend fun distributeReward(task: Task, characterId: String): Boolean {
        // TODO: 调用经济服务增加资金
        return true
    }
}

// ==================== 结果类型 ====================

sealed class TaskResult {
    data class Success(
        val submissionId: String? = null,
        val message: String
    ) : TaskResult()
    
    data class Error(val message: String) : TaskResult()
}

sealed class VoteResult {
    data class Pending(
        val currentParticipation: Int,
        val totalMembers: Int,
        val currentApproval: Int,
        val requiredParticipation: Int
    ) : VoteResult()
    
    data class Passed(
        val approvalRate: Float,
        val participationRate: Float
    ) : VoteResult()
    
    data class Rejected(
        val approvalRate: Float,
        val needRevision: Boolean = false
    ) : VoteResult()
    
    data class Error(val message: String) : VoteResult()
}

sealed class GenerateResult {
    data class Success(val content: String) : GenerateResult()
    data class Error(val message: String) : GenerateResult()
}

// ==================== 辅助数据类 ====================

data class Vote(
    val submissionId: String,
    val characterId: String,
    val approved: Boolean,
    val comment: String,
    val votedAt: Long
)

enum class SubmissionStatus {
    PENDING_REVIEW,    // 等待用户审核
    PENDING_VOTE,      // 等待公司投票
    APPROVED,          // 已通过
    REJECTED,          // 已拒绝
    REVISING           // 修改中
}

enum class ImageStyle {
    EPIC,       // 史诗感
    REALISTIC,  // 写实
    ARTISTIC    // 艺术风格
}
