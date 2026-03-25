package com.ai.socialworld.presentation.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.model.Character
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.domain.service.ChatService
import com.ai.socialworld.domain.service.LogService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 聊天详情ViewModel
 */
@HiltViewModel
class ChatDetailViewModel @Inject constructor(
    private val characterRepository: CharacterRepository,
    private val chatService: ChatService,
    private val logService: LogService
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatDetailUiState())
    val uiState: StateFlow<ChatDetailUiState> = _uiState.asStateFlow()

    private var currentCharacter: Character? = null

    fun loadCharacter(characterId: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }

            val character = characterRepository.getCharacterById(characterId.toLong())
            currentCharacter = character

            character?.let {
                _uiState.update { state ->
                    state.copy(
                        characterName = it.name,
                        character = it,
                        isLoading = false
                    )
                }

                logService.logSocial(
                    characterId = it.id.toString(),
                    characterName = it.name,
                    content = "开始与用户聊天"
                )
            }
        }
    }

    fun sendMessage(content: String) {
        val character = currentCharacter ?: return

        viewModelScope.launch {
            val userMessage = ChatMessage(
                id = System.currentTimeMillis().toString(),
                content = content,
                isFromUser = true
            )

            _uiState.update { state ->
                state.copy(
                    messages = state.messages + userMessage,
                    isLoading = true
                )
            }

            logService.logSocial(
                characterId = character.id.toString(),
                characterName = character.name,
                content = "用户: $content"
            )

            val history = _uiState.value.messages.map { msg ->
                if (msg.isFromUser) "user" to msg.content
                else "assistant" to msg.content
            }

            when (val result = chatService.generateResponse(
                character = character,
                userMessage = content,
                chatHistory = history
            )) {
                is com.ai.socialworld.domain.service.ChatResult.Success -> {
                    val aiMessage = ChatMessage(
                        id = (System.currentTimeMillis() + 1).toString(),
                        content = result.content,
                        isFromUser = false
                    )

                    _uiState.update { state ->
                        state.copy(
                            messages = state.messages + aiMessage,
                            isLoading = false
                        )
                    }

                    logService.logSocial(
                        characterId = character.id.toString(),
                        characterName = character.name,
                        content = "${character.name}: ${result.content}"
                    )
                }

                is com.ai.socialworld.domain.service.ChatResult.Error -> {
                    _uiState.update { state ->
                        state.copy(
                            errorMessage = result.message,
                            isLoading = false
                        )
                    }
                }
            }
        }
    }

    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
}

/**
 * 聊天详情UI状态
 */
data class ChatDetailUiState(
    val characterName: String = "",
    val character: Character? = null,
    val messages: List<ChatMessage> = emptyList(),
    val isLoading: Boolean = false,
    val errorMessage: String? = null
)
