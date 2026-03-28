package com.ai.wechat.db.dao

import androidx.room.*
import com.ai.wechat.data.model.Task
import com.ai.wechat.data.model.TaskStatus
import kotlinx.coroutines.flow.Flow

/**
 * 任务数据访问对象
 */
@Dao
interface TaskDao {

    @Query("SELECT * FROM tasks ORDER BY createdAt DESC")
    fun getAllTasks(): Flow<List<Task>>

    @Query("SELECT * FROM tasks WHERE status = :status ORDER BY createdAt DESC")
    fun getTasksByStatus(status: TaskStatus): Flow<List<Task>>

    @Query("SELECT * FROM tasks WHERE id = :id")
    suspend fun getTaskById(id: String): Task?

    @Query("SELECT * FROM tasks WHERE id = :id")
    fun getTaskByIdFlow(id: String): Flow<Task?>

    @Query("SELECT * FROM tasks WHERE assigneeId = :characterId ORDER BY createdAt DESC")
    fun getTasksByAssignee(characterId: String): Flow<List<Task>>

    @Query("SELECT * FROM tasks WHERE companyId = :companyId ORDER BY createdAt DESC")
    fun getTasksByCompany(companyId: String): Flow<List<Task>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTask(task: Task)

    @Update
    suspend fun updateTask(task: Task)

    @Delete
    suspend fun deleteTask(task: Task)

    @Query("UPDATE tasks SET status = :status, updatedAt = :updatedAt WHERE id = :id")
    suspend fun updateStatus(id: String, status: TaskStatus, updatedAt: Long = System.currentTimeMillis())

    @Query("UPDATE tasks SET result = :result, imageUrl = :imageUrl, completedAt = :completedAt, status = :status WHERE id = :id")
    suspend fun completeTask(id: String, result: String?, imageUrl: String?, completedAt: Long, status: TaskStatus)
}
