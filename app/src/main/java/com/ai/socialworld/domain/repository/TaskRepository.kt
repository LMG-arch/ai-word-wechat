package com.ai.socialworld.domain.repository

import com.ai.socialworld.data.model.*
import kotlinx.coroutines.flow.Flow

/**
 * 任务仓库接口
 */
interface TaskRepository {
    
    // ==================== 任务相关 ====================
    
    /**
     * 插入任务
     */
    suspend fun insertTask(task: Task): Long
    
    /**
     * 更新任务
     */
    suspend fun updateTask(task: Task)
    
    /**
     * 获取所有任务
     */
    fun getAllTasks(): Flow<List<Task>>
    
    /**
     * 获取指定状态的任务
     */
    fun getTasksByStatus(status: TaskStatus): Flow<List<Task>>
    
    /**
     * 获取任务详情
     */
    suspend fun getTaskById(taskId: String): Task?
    
    /**
     * 更新任务状态
     */
    suspend fun updateTaskStatus(taskId: String, status: TaskStatus)
    
    /**
     * 更新任务执行人
     */
    suspend fun updateTaskAssignee(taskId: String, assigneeId: String)
    
    /**
     * 获取角色接取的任务
     */
    fun getTasksByAssignee(assigneeId: String): Flow<List<Task>>
    
    /**
     * 获取可接取的任务
     */
    suspend fun getAvailableTasks(): List<Task>
    
    /**
     * 删除任务
     */
    suspend fun deleteTask(taskId: String)
    
    // ==================== 任务提交 ====================
    
    /**
     * 插入提交记录
     */
    suspend fun insertSubmission(submission: TaskSubmission): Long
    
    /**
     * 获取提交记录
     */
    suspend fun getSubmissionById(submissionId: String): TaskSubmission?
    
    /**
     * 获取任务的所有提交
     */
    suspend fun getSubmissionsByTask(taskId: String): List<TaskSubmission>
    
    /**
     * 更新提交状态
     */
    suspend fun updateSubmissionStatus(submissionId: String, status: SubmissionStatus)
    
    /**
     * 添加提交反馈
     */
    suspend fun addSubmissionFeedback(submissionId: String, feedback: String)
    
    // ==================== 投票 ====================
    
    /**
     * 插入投票
     */
    suspend fun insertVote(vote: com.ai.socialworld.domain.service.Vote)
    
    /**
     * 获取提交的所有投票
     */
    suspend fun getVotesBySubmission(submissionId: String): List<com.ai.socialworld.domain.service.Vote>
    
    // ==================== 公司相关 ====================
    
    /**
     * 获取公司
     */
    suspend fun getCompanyById(companyId: String): Company?
    
    /**
     * 获取公司成员
     */
    suspend fun getCompanyMembers(companyId: String): List<CompanyMember>
    
    /**
     * 获取公司的任务
     */
    fun getTasksByCompany(companyId: String): Flow<List<Task>>
}
