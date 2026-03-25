package com.ai.socialworld.presentation.discover

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.model.Moment
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.domain.repository.MomentRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class MomentsViewModel @Inject constructor(
    private val momentRepository: MomentRepository,
    private val characterRepository: CharacterRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(MomentsUiState())
    val uiState: StateFlow<MomentsUiState> = _uiState.asStateFlow()

    private val characterNames = mutableMapOf<String, String>()
    private val characterAvatars = mutableMapOf<String, String?>()

    init {
        loadMoments()
    }

    private fun loadMoments() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }

            characterRepository.getAllCharacters().collect { characters ->
                characters.forEach { char ->
                    characterNames[char.id.toString()] = char.name
                    characterAvatars[char.id.toString()] = char.avatar
                }
            }
        }

        viewModelScope.launch {
            momentRepository.getAllMoments().collect { moments ->
                _uiState.update { state ->
                    state.copy(
                        moments = moments.map { it.toMomentItem() },
                        isLoading = false
                    )
                }
            }
        }
    }

    fun likeMoment(momentId: String) {
        viewModelScope.launch {
            val userId = "user"
            val isLiked = momentRepository.isLikedBy(momentId, userId)
            if (isLiked) {
                momentRepository.unlikeMoment(momentId, userId)
            } else {
                momentRepository.likeMoment(momentId, userId)
            }
            refreshMoment(momentId)
        }
    }

    fun commentMoment(momentId: String, content: String) {
        viewModelScope.launch {
            val userId = "user"
            momentRepository.addComment(momentId, userId, content)
            refreshMoment(momentId)
        }
    }

    fun createMoment(content: String, imageUrl: String? = null) {
        viewModelScope.launch {
            val userId = "user"
            momentRepository.createMoment(userId, content, imageUrl)
        }
    }

    private suspend fun refreshMoment(momentId: String) {
        val moment = momentRepository.getMomentById(momentId)
        moment?.let {
            _uiState.update { state ->
                state.copy(
                    moments = state.moments.map { item ->
                        if (item.id == momentId) item.toMomentItem() else item
                    }
                )
            }
        }
    }

    private fun Moment.toMomentItem(): MomentItem {
        return MomentItem(
            id = id,
            authorId = characterId,
            authorName = characterNames[characterId] ?: "未知",
            authorAvatar = characterAvatars[characterId],
            content = content,
            imageUrl = imageUrl,
            timestamp = createdAt.toEpochMilli(),
            likes = likes.size,
            likedBy = likes.map { characterNames[it.characterId] ?: it.characterId },
            isLiked = likes.any { it.characterId == "user" },
            comments = comments.map { comment ->
                CommentItem(
                    id = comment.id,
                    authorId = comment.characterId,
                    authorName = characterNames[comment.characterId] ?: "未知",
                    content = comment.content,
                    timestamp = comment.timestamp.toEpochMilli()
                )
            }
        )
    }

    private fun MomentItem.toMomentItem(): MomentItem = this
}

data class MomentsUiState(
    val moments: List<MomentItem> = emptyList(),
    val isLoading: Boolean = false
)

data class MomentItem(
    val id: String,
    val authorId: String,
    val authorName: String,
    val authorAvatar: String? = null,
    val content: String,
    val imageUrl: String? = null,
    val timestamp: Long = System.currentTimeMillis(),
    val likes: Int = 0,
    val likedBy: List<String> = emptyList(),
    val isLiked: Boolean = false,
    val comments: List<CommentItem> = emptyList()
)

data class CommentItem(
    val id: String,
    val authorId: String,
    val authorName: String,
    val content: String,
    val timestamp: Long = System.currentTimeMillis()
)