package com.ai.socialworld.presentation.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.model.Character
import com.ai.socialworld.domain.repository.CharacterRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 聊天列表ViewModel
 */
@HiltViewModel
class ChatListViewModel @Inject constructor(
    private val characterRepository: CharacterRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatListUiState())
    val uiState: StateFlow<ChatListUiState> = _uiState.asStateFlow()

    init {
        loadCharacters()
    }

    private fun loadCharacters() {
        viewModelScope.launch {
            characterRepository.getAllCharacters()
                .map { characters ->
                    characters.map { it.toChatItem() }
                }
                .onEach { chatItems ->
                    _uiState.update { it.copy(chatItems = chatItems, isLoading = false) }
                }
                .launchIn(viewModelScope)
        }
    }

    fun searchCharacters(query: String) {
        _uiState.update { it.copy(searchQuery = query) }
        // 实际搜索逻辑已在UI层通过filter实现
    }

    private fun Character.toChatItem(): ChatItem {
        return ChatItem(
            characterId = this.id.toString(),
            name = this.name,
            avatarUrl = this.avatarUrl,
            lastMessage = "点击开始聊天", // 实际应从聊天记录获取
            time = "",
            unreadCount = 0
        )
    }
}

/**
 * 聊天列表UI状态
 */
data class ChatListUiState(
    val chatItems: List<ChatItem> = emptyList(),
    val searchQuery: String = "",
    val isLoading: Boolean = true
)
