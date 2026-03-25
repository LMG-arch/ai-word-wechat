package com.ai.socialworld.data.repository

import com.ai.socialworld.data.local.CompanyDao
import com.ai.socialworld.data.local.TaskDao
import com.ai.socialworld.data.model.*
import com.ai.socialworld.domain.repository.TaskRepository
import com.ai.socialworld.domain.service.Vote
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 任务仓库实现
 */
@Singleton
class TaskRepositoryImpl @Inject constructor(
    private val taskDao: TaskDao,
    private val companyDao: CompanyDao
) : TaskRepository {
    
    // ==================== 任务相关 ====================
    
    override suspend fun insertTask(task: Task): Long {
        return taskDao.insert(task)
    }
    
    override suspend fun updateTask(task: Task) {
        taskDao.update(task)
    }
    
    override fun getAllTasks(): Flow<List<Task>> {
        return taskDao.getAllTasks()
    }
    
    override fun getTasksByStatus(status: TaskStatus): Flow<List<Task>> {
        return taskDao.getTasksByStatus(status)
    }
    
    override suspend fun getTaskById(taskId: String): Task? {
        return taskDao.getTaskById(taskId)
    }
    
    override suspend fun updateTaskStatus(taskId: String, status: TaskStatus) {
        taskDao.updateStatus(taskId, status)
    }
    
    override suspend fun updateTaskAssignee(taskId: String, assigneeId: String) {
        taskDao.updateAssignee(taskId, assigneeId)
    }
    
    override fun getTasksByAssignee(assigneeId: String): Flow<List<Task>> {
        return taskDao.getTasksByAssignee(assigneeId)
    }
    
    override suspend fun getAvailableTasks(): List<Task> {
        return taskDao.getAvailableTasks()
    }
    
    override suspend fun deleteTask(taskId: String) {
        taskDao.deleteById(taskId)
    }
    
    // ==================== 任务提交 ====================
    
    override suspend fun insertSubmission(submission: TaskSubmission): Long {
        return taskDao.insertSubmission(submission)
    }
    
    override suspend fun getSubmissionById(submissionId: String): TaskSubmission? {
        return taskDao.getSubmissionById(submissionId)
    }
    
    override suspend fun getSubmissionsByTask(taskId: String): List<TaskSubmission> {
        return taskDao.getSubmissionsByTask(taskId)
    }
    
    override suspend fun updateSubmissionStatus(submissionId: String, status: SubmissionStatus) {
        taskDao.updateSubmissionStatus(submissionId, status.name)
    }
    
    override suspend fun addSubmissionFeedback(submissionId: String, feedback: String) {
        taskDao.addSubmissionFeedback(submissionId, feedback)
    }
    
    // ==================== 投票 ====================
    
    // 投票数据存储在内存中（简化实现）
    // 实际项目中应该存储到数据库
    private val votesStorage = mutableMapOf<String, MutableList<Vote>>()
    
    override suspend fun insertVote(vote: Vote) {
        val list = votesStorage.getOrPut(vote.submissionId) { mutableListOf() }
        list.add(vote)
    }
    
    override suspend fun getVotesBySubmission(submissionId: String): List<Vote> {
        return votesStorage[submissionId] ?: emptyList()
    }
    
    // ==================== 公司相关 ====================
    
    override suspend fun getCompanyById(companyId: String): Company? {
        return companyDao.getCompanyById(companyId)
    }
    
    override suspend fun getCompanyMembers(companyId: String): List<CompanyMember> {
        return companyDao.getCompanyMembersSync(companyId)
    }
    
    override fun getTasksByCompany(companyId: String): Flow<List<Task>> {
        return taskDao.getTasksByCompany(companyId)
    }
}
