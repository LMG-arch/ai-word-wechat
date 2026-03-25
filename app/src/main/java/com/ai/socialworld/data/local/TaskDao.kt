package com.ai.socialworld.data.local

import androidx.room.*
import com.ai.socialworld.data.model.*
import kotlinx.coroutines.flow.Flow

/**
 * 任务DAO
 */
@Dao
interface TaskDao {
    
    // ==================== 任务相关 ====================
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(task: Task): Long
    
    @Update
    suspend fun update(task: Task)
    
    @Delete
    suspend fun delete(task: Task)
    
    @Query("SELECT * FROM tasks ORDER BY createdAt DESC")
    fun getAllTasks(): Flow<List<Task>>
    
    @Query("SELECT * FROM tasks WHERE status = :status ORDER BY createdAt DESC")
    fun getTasksByStatus(status: TaskStatus): Flow<List<Task>>
    
    @Query("SELECT * FROM tasks WHERE id = :taskId")
    suspend fun getTaskById(taskId: String): Task?
    
    @Query("UPDATE tasks SET status = :status WHERE id = :taskId")
    suspend fun updateStatus(taskId: String, status: TaskStatus)
    
    @Query("UPDATE tasks SET assigneeId = :assigneeId WHERE id = :taskId")
    suspend fun updateAssignee(taskId: String, assigneeId: String)
    
    @Query("SELECT * FROM tasks WHERE assigneeId = :assigneeId ORDER BY createdAt DESC")
    fun getTasksByAssignee(assigneeId: String): Flow<List<Task>>
    
    @Query("SELECT * FROM tasks WHERE status = 'PENDING' OR status = 'ASSIGNED' ORDER BY createdAt DESC")
    suspend fun getAvailableTasks(): List<Task>
    
    @Query("SELECT * FROM tasks WHERE companyId = :companyId ORDER BY createdAt DESC")
    fun getTasksByCompany(companyId: String): Flow<List<Task>>
    
    @Query("DELETE FROM tasks WHERE id = :taskId")
    suspend fun deleteById(taskId: String)
    
    @Query("SELECT COUNT(*) FROM tasks WHERE assigneeId = :characterId AND status IN ('ASSIGNED', 'IN_PROGRESS')")
    suspend fun getActiveTaskCount(characterId: String): Int
    
    // ==================== 任务提交 ====================
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSubmission(submission: TaskSubmission): Long
    
    @Update
    suspend fun updateSubmission(submission: TaskSubmission)
    
    @Query("SELECT * FROM task_submissions WHERE id = :submissionId")
    suspend fun getSubmissionById(submissionId: String): TaskSubmission?
    
    @Query("SELECT * FROM task_submissions WHERE taskId = :taskId ORDER BY submittedAt DESC")
    suspend fun getSubmissionsByTask(taskId: String): List<TaskSubmission>
    
    @Query("UPDATE task_submissions SET status = :status WHERE id = :submissionId")
    suspend fun updateSubmissionStatus(submissionId: String, status: String)
    
    @Query("UPDATE task_submissions SET feedback = :feedback WHERE id = :submissionId")
    suspend fun addSubmissionFeedback(submissionId: String, feedback: String)
    
    @Query("SELECT * FROM task_submissions WHERE characterId = :characterId ORDER BY submittedAt DESC")
    fun getSubmissionsByCharacter(characterId: String): Flow<List<TaskSubmission>>
}
