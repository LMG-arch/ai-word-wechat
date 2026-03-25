package com.ai.socialworld.presentation.tasks

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.model.Task
import com.ai.socialworld.data.model.TaskDifficulty
import com.ai.socialworld.data.model.TaskStatus
import com.ai.socialworld.data.model.TaskType
import com.ai.socialworld.domain.repository.TaskRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class TasksViewModel @Inject constructor(
    private val taskRepository: TaskRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(TasksUiState())
    val uiState: StateFlow<TasksUiState> = _uiState.asStateFlow()

    private var allTasks: List<TaskItemData> = emptyList()

    init {
        loadTasks()
    }

    private fun loadTasks() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }

            taskRepository.getAllTasks().collect { tasks ->
                allTasks = tasks.map { it.toTaskItemData() }
                _uiState.update { it.copy(tasks = allTasks, isLoading = false) }
            }
        }
    }

    fun filterTasks(tabIndex: Int) {
        val filtered = when (tabIndex) {
            0 -> allTasks
            1 -> allTasks.filter { it.status == TaskStatus.PENDING }
            2 -> allTasks.filter { it.status == TaskStatus.IN_PROGRESS }
            3 -> allTasks.filter { it.status == TaskStatus.COMPLETED }
            else -> allTasks
        }
        _uiState.update { it.copy(tasks = filtered) }
    }

    fun acceptTask(taskId: String) {
        viewModelScope.launch {
            taskRepository.updateTaskAssignee(taskId, "user")
            taskRepository.updateTaskStatus(taskId, TaskStatus.IN_PROGRESS)
        }
    }

    fun createTask(title: String, description: String, difficulty: TaskDifficulty, reward: Int) {
        viewModelScope.launch {
            val task = Task(
                id = System.currentTimeMillis().toString(),
                title = title,
                description = description,
                type = TaskType.WORK,
                difficulty = difficulty,
                reward = reward,
                status = TaskStatus.PENDING,
                assigneeId = null,
                createdBy = "user",
                createdAt = System.currentTimeMillis(),
                updatedAt = System.currentTimeMillis()
            )
            taskRepository.insertTask(task)
        }
    }

    private fun Task.toTaskItemData(): TaskItemData {
        return TaskItemData(
            id = id,
            title = title,
            description = description,
            difficulty = difficulty,
            reward = reward,
            status = status
        )
    }
}

data class TasksUiState(
    val tasks: List<TaskItemData> = emptyList(),
    val isLoading: Boolean = false
)

data class TaskItemData(
    val id: String,
    val title: String,
    val description: String,
    val difficulty: TaskDifficulty,
    val reward: Int,
    val status: TaskStatus
)