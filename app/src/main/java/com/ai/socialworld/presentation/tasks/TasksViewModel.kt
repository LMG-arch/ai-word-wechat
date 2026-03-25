package com.ai.socialworld.presentation.tasks

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.model.Task
import com.ai.socialworld.data.model.TaskDifficulty
import com.ai.socialworld.data.model.TaskStatus
import com.ai.socialworld.domain.repository.TaskRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 任务中心ViewModel
 */
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
            
            // TODO: 从数据库加载真实数据
            // 暂时使用模拟数据
            allTasks = listOf(
                TaskItemData(
                    id = "1",
                    title = "设计一个APP图标",
                    description = "为社交应用设计一个现代、简洁的图标，需要体现连接和沟通的概念",
                    difficulty = TaskDifficulty.MEDIUM,
                    reward = 200,
                    status = TaskStatus.PENDING
                ),
                TaskItemData(
                    id = "2",
                    title = "写一篇产品推广文案",
                    description = "为新推出的AI助手产品撰写一篇吸引人的推广文案",
                    difficulty = TaskDifficulty.EASY,
                    reward = 100,
                    status = TaskStatus.PENDING
                ),
                TaskItemData(
                    id = "3",
                    title = "开发一个聊天功能",
                    description = "实现完整的即时通讯功能，包括消息发送、接收、历史记录等",
                    difficulty = TaskDifficulty.HARD,
                    reward = 500,
                    status = TaskStatus.IN_PROGRESS
                ),
                TaskItemData(
                    id = "4",
                    title = "用户调研报告",
                    description = "完成一份关于目标用户群体的调研报告",
                    difficulty = TaskDifficulty.MEDIUM,
                    reward = 300,
                    status = TaskStatus.COMPLETED
                )
            )
            
            _uiState.update { it.copy(tasks = allTasks, isLoading = false) }
        }
    }

    fun filterTasks(tabIndex: Int) {
        val filtered = when (tabIndex) {
            0 -> allTasks // 全部
            1 -> allTasks.filter { it.status == TaskStatus.PENDING } // 待接取
            2 -> allTasks.filter { it.status == TaskStatus.IN_PROGRESS } // 进行中
            3 -> allTasks.filter { it.status == TaskStatus.COMPLETED } // 已完成
            else -> allTasks
        }
        _uiState.update { it.copy(tasks = filtered) }
    }

    fun acceptTask(taskId: String) {
        viewModelScope.launch {
            // TODO: 实现接取任务逻辑
        }
    }

    fun createTask(title: String, description: String, difficulty: TaskDifficulty, reward: Int) {
        viewModelScope.launch {
            // TODO: 实现创建任务逻辑
        }
    }
}

/**
 * 任务中心UI状态
 */
data class TasksUiState(
    val tasks: List<TaskItemData> = emptyList(),
    val isLoading: Boolean = false
)
