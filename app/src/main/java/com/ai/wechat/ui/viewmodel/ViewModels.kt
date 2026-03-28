package com.ai.wechat.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.wechat.service.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

/**
 * 聊天列表 ViewModel
 */
class ChatListViewModel(
    private val chatMessageDao: com.ai.wechat.db.dao.ChatMessageDao
) : ViewModel() {

    private val _conversations = MutableStateFlow<List<com.ai.wechat.data.model.Conversation>>(emptyList())
    val conversations: StateFlow<List<com.ai.wechat.data.model.Conversation>> = _conversations.asStateFlow()

    init {
        loadConversations()
    }

    private fun loadConversations() {
        viewModelScope.launch {
            chatMessageDao.getAllConversationIds().collect { conversationIds ->
                // TODO: 构建会话列表
                _conversations.value = emptyList()
            }
        }
    }

    fun markAsRead(conversationId: String, receiverId: String) {
        viewModelScope.launch {
            chatMessageDao.markAsRead(conversationId, receiverId)
        }
    }
}

/**
 * 通讯录 ViewModel
 */
class ContactsViewModel(
    private val characterManager: CharacterManager
) : ViewModel() {

    val characters = characterManager.getAllCharacters()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
}

/**
 * 角色详情 ViewModel
 */
class CharacterDetailViewModel(
    private val characterManager: CharacterManager,
    private val memoryEngine: com.ai.wechat.data.memory.MemoryEngine
) : ViewModel() {

    private val _character = MutableStateFlow<com.ai.wechat.data.model.Character?>(null)
    val character: StateFlow<com.ai.wechat.data.model.Character?> = _character.asStateFlow()

    fun loadCharacter(characterId: String) {
        viewModelScope.launch {
            characterManager.getCharacter(characterId)?.let {
                _character.value = it
            }
        }
    }

    fun updateMoney(characterId: String, amount: Double) {
        viewModelScope.launch {
            characterManager.updateMoney(characterId, amount)
        }
    }
}

/**
 * 任务列表 ViewModel
 */
class TaskListViewModel(
    private val taskSystem: TaskSystem
) : ViewModel() {

    val tasks = taskSystem.getAllTasks()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
}

/**
 * 群聊列表 ViewModel
 */
class GroupListViewModel(
    private val groupChatDao: com.ai.wechat.db.dao.GroupChatDao
) : ViewModel() {

    val groupChats = groupChatDao.getAllGroupChats()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
}
