package com.ai.socialworld.presentation.discover

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 朋友圈ViewModel
 */
@HiltViewModel
class MomentsViewModel @Inject constructor() : ViewModel() {

    private val _uiState = MutableStateFlow(MomentsUiState())
    val uiState: StateFlow<MomentsUiState> = _uiState.asStateFlow()

    init {
        loadMoments()
    }

    private fun loadMoments() {
        // TODO: 从数据库加载真实数据
        val mockMoments = listOf(
            Moment(
                id = "1",
                authorId = "char1",
                authorName = "小明",
                content = "今天完成了一个很有挑战性的任务，感觉收获满满！",
                likes = 12,
                likedBy = listOf("小红", "小刚", "小李"),
                isLiked = false,
                comments = listOf(
                    Comment(
                        id = "c1",
                        authorId = "char2",
                        authorName = "小红",
                        content = "恭喜！继续加油！"
                    )
                )
            ),
            Moment(
                id = "2",
                authorId = "char3",
                authorName = "小红",
                content = "今天的天气真好，适合出去走走~",
                likes = 8,
                likedBy = listOf("小明"),
                isLiked = true,
                comments = emptyList()
            ),
            Moment(
                id = "3",
                authorId = "char4",
                authorName = "小刚",
                content = "反思一下今天的工作，发现还有很多需要改进的地方。",
                likes = 5,
                likedBy = emptyList(),
                isLiked = false,
                comments = listOf(
                    Comment(
                        id = "c2",
                        authorId = "char1",
                        authorName = "小明",
                        content = "反思是进步的开始"
                    ),
                    Comment(
                        id = "c3",
                        authorId = "char2",
                        authorName = "小红",
                        content = "加油！"
                    )
                )
            )
        )
        
        _uiState.update { it.copy(moments = mockMoments) }
    }

    fun likeMoment(momentId: String) {
        viewModelScope.launch {
            _uiState.update { state ->
                state.copy(
                    moments = state.moments.map { moment ->
                        if (moment.id == momentId) {
                            moment.copy(
                                isLiked = !moment.isLiked,
                                likes = if (moment.isLiked) moment.likes - 1 else moment.likes + 1
                            )
                        } else {
                            moment
                        }
                    }
                )
            }
        }
    }

    fun commentMoment(momentId: String, content: String) {
        viewModelScope.launch {
            // TODO: 保存评论到数据库
            _uiState.update { state ->
                state.copy(
                    moments = state.moments.map { moment ->
                        if (moment.id == momentId) {
                            val newComment = Comment(
                                id = System.currentTimeMillis().toString(),
                                authorId = "user",
                                authorName = "我",
                                content = content
                            )
                            moment.copy(
                                comments = moment.comments + newComment
                            )
                        } else {
                            moment
                        }
                    }
                )
            }
        }
    }

    fun createMoment(content: String, imageUrl: String? = null) {
        viewModelScope.launch {
            // TODO: 保存动态到数据库
            val newMoment = Moment(
                id = System.currentTimeMillis().toString(),
                authorId = "user",
                authorName = "我",
                content = content,
                imageUrl = imageUrl
            )
            _uiState.update { state ->
                state.copy(moments = listOf(newMoment) + state.moments)
            }
        }
    }
}

/**
 * 朋友圈UI状态
 */
data class MomentsUiState(
    val moments: List<Moment> = emptyList(),
    val isLoading: Boolean = false
)
