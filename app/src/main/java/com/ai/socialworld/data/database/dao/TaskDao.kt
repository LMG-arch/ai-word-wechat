package com.ai.socialworld.data.database.dao

import androidx.room.*
import com.ai.socialworld.data.database.entity.TaskEntity
import com.ai.socialworld.data.model.TaskStatus
import com.ai.socialworld.data.model.TaskType
import kotlinx.coroutines.flow.Flow

/**
 * 任务数据访问对象
 */
@Dao
interface TaskDao {
    @Query("SELECT * FROM tasks WHERE isDeleted = 0 ORDER BY createdAt DESC")
    fun getAllTasks(): Flow<List<TaskEntity>>
    
    @Query("SELECT * FROM tasks WHERE id = :id")
    suspend fun getTaskById(id: String): TaskEntity?
    
    @Query("SELECT * FROM tasks WHERE status = :status AND isDeleted = 0")
    fun getTasksByStatus(status: TaskStatus): Flow<List<TaskEntity>>
    
    @Query("SELECT * FROM tasks WHERE type = :type AND isDeleted = 0")
    fun getTasksByType(type: TaskType): Flow<List<TaskEntity>>
    
    @Query("SELECT * FROM tasks WHERE assigneeId = :characterId AND isDeleted = 0")
    fun getTasksByAssignee(characterId: String): Flow<List<TaskEntity>>
    
    @Query("SELECT * FROM tasks WHERE companyId = :companyId AND isDeleted = 0")
    fun getTasksByCompany(companyId: String): Flow<List<TaskEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTask(task: TaskEntity)
    
    @Update
    suspend fun updateTask(task: TaskEntity)
    
    @Delete
    suspend fun deleteTask(task: TaskEntity)
    
    @Query("UPDATE tasks SET isDeleted = 1 WHERE id = :id")
    suspend fun softDeleteTask(id: String)
    
    @Query("UPDATE tasks SET status = :status WHERE id = :id")
    suspend fun updateTaskStatus(id: String, status: TaskStatus)
    
    @Query("UPDATE tasks SET progress = :progress WHERE id = :id")
    suspend fun updateTaskProgress(id: String, progress: Int)
    
    @Query("SELECT COUNT(*) FROM tasks WHERE isDeleted = 0")
    suspend fun getTaskCount(): Int
}
