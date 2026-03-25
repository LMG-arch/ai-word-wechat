package com.ai.socialworld.presentation.groups

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.database.entity.ChatGroupEntity
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.data.repository.SocialRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class GroupsViewModel @Inject constructor(
    private val socialRepository: SocialRepository,
    private val characterRepository: CharacterRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(GroupsUiState())
    val uiState: StateFlow<GroupsUiState> = _uiState.asStateFlow()

    private val characterNames = mutableMapOf<String, String>()

    init {
        loadGroups()
    }

    private fun loadGroups() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }

            characterRepository.getAllCharacters().collect { characters ->
                characters.forEach { char ->
                    characterNames[char.id.toString()] = char.name
                }
            }
        }

        viewModelScope.launch {
            socialRepository.getAllChatGroups().collect { groups ->
                _uiState.update { state ->
                    state.copy(
                        groups = groups.map { it.toGroupItemData() },
                        isLoading = false
                    )
                }
            }
        }
    }

    fun createGroup(name: String, description: String) {
        viewModelScope.launch {
            val userId = "user"
            socialRepository.createChatGroup(name, userId, description)
        }
    }

    fun joinGroup(groupId: String) {
        viewModelScope.launch {
            // TODO: 实现加入群组逻辑
        }
    }

    private fun ChatGroupEntity.toGroupItemData(): GroupItemData {
        val memberIdList = if (memberIds.isBlank()) emptyList() else memberIds.split(",")
        return GroupItemData(
            id = id,
            name = name,
            description = description,
            memberCount = memberIdList.size,
            unreadCount = 0
        )
    }
}

data class GroupsUiState(
    val groups: List<GroupItemData> = emptyList(),
    val isLoading: Boolean = false
)

data class GroupItemData(
    val id: String,
    val name: String,
    val description: String,
    val memberCount: Int,
    val unreadCount: Int = 0
)