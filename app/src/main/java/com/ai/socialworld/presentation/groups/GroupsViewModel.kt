package com.ai.socialworld.presentation.groups

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 群组ViewModel
 */
@HiltViewModel
class GroupsViewModel @Inject constructor() : ViewModel() {

    private val _uiState = MutableStateFlow(GroupsUiState())
    val uiState: StateFlow<GroupsUiState> = _uiState.asStateFlow()

    init {
        loadGroups()
    }

    private fun loadGroups() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            
            // TODO: 从数据库加载真实数据
            // 暂时使用模拟数据
            val mockGroups = listOf(
                GroupItemData(
                    id = "1",
                    name = "设计团队",
                    description = "负责产品UI/UX设计的团队",
                    memberCount = 5,
                    unreadCount = 3
                ),
                GroupItemData(
                    id = "2",
                    name = "开发小组",
                    description = "核心功能开发团队",
                    memberCount = 8,
                    unreadCount = 0
                ),
                GroupItemData(
                    id = "3",
                    name = "产品讨论",
                    description = "产品规划和需求讨论",
                    memberCount = 12,
                    unreadCount = 7
                )
            )
            
            _uiState.update { it.copy(groups = mockGroups, isLoading = false) }
        }
    }

    fun createGroup(name: String, description: String) {
        viewModelScope.launch {
            // TODO: 实现创建群组逻辑
        }
    }

    fun joinGroup(groupId: String) {
        viewModelScope.launch {
            // TODO: 实现加入群组逻辑
        }
    }
}

/**
 * 群组UI状态
 */
data class GroupsUiState(
    val groups: List<GroupItemData> = emptyList(),
    val isLoading: Boolean = false
)
