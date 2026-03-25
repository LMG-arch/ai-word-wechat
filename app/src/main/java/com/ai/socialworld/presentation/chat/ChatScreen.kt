package com.ai.socialworld.presentation.chat

import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.rememberAsyncImagePainter
import com.ai.socialworld.presentation.components.EmptyState
import com.ai.socialworld.presentation.components.TopAppBar

/**
 * 聊天列表页面（仿微信）
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    viewModel: ChatListViewModel = hiltViewModel(),
    onNavigateToChat: (String) -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    var searchQuery by remember { mutableStateOf("") }
    
    // 过滤聊天列表
    val filteredItems = uiState.chatItems.filter {
        it.name.contains(searchQuery, ignoreCase = true)
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = "微信",
                actions = {
                    IconButton(onClick = { /* TODO: 添加聊天 */ }) {
                        Icon(
                            imageVector = Icons.Default.Add,
                            contentDescription = "添加"
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // 搜索栏
            SearchBar(
                query = searchQuery,
                onQueryChange = { 
                    searchQuery = it
                    viewModel.searchCharacters(it)
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp)
            )
            
            // 聊天列表
            if (uiState.isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else if (filteredItems.isEmpty()) {
                EmptyState(
                    icon = Icons.Default.Chat,
                    message = if (searchQuery.isEmpty()) {
                        "暂无聊天消息\n去通讯录添加角色开始聊天吧"
                    } else {
                        "未找到匹配的角色"
                    }
                )
            } else {
                LazyColumn {
                    items(filteredItems) { item ->
                        ChatListItem(
                            item = item,
                            onClick = { onNavigateToChat(item.characterId) }
                        )
                        Divider()
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        placeholder = { Text("搜索") },
        leadingIcon = {
            Icon(
                imageVector = Icons.Default.Search,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
        },
        modifier = modifier,
        singleLine = true,
        colors = TextFieldDefaults.outlinedTextFieldColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    )
}

@Composable
private fun ChatListItem(
    item: ChatItem,
    onClick: () -> Unit
) {
    ListItem(
        headlineContent = {
            Text(
                text = item.name,
                fontWeight = FontWeight.Medium
            )
        },
        supportingContent = {
            Text(
                text = item.lastMessage,
                maxLines = 1,
                style = MaterialTheme.typography.bodyMedium
            )
        },
        leadingContent = {
            // 头像
            if (item.avatarUrl != null) {
                Image(
                    painter = rememberAsyncImagePainter(item.avatarUrl),
                    contentDescription = null,
                    modifier = Modifier.size(48.dp),
                    contentScale = ContentScale.Crop
                )
            } else {
                Surface(
                    modifier = Modifier.size(48.dp),
                    shape = MaterialTheme.shapes.small,
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Default.Chat,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                }
            }
        },
        trailingContent = {
            Column(
                horizontalAlignment = Alignment.End
            ) {
                if (item.time.isNotEmpty()) {
                    Text(
                        text = item.time,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                if (item.unreadCount > 0) {
                    Badge(
                        containerColor = MaterialTheme.colorScheme.error
                    ) {
                        Text(
                            text = if (item.unreadCount > 99) "99+" else item.unreadCount.toString(),
                            color = MaterialTheme.colorScheme.onError
                        )
                    }
                }
            }
        },
        modifier = Modifier.clickable { onClick() }
    )
}

// 数据类
data class ChatItem(
    val characterId: String,
    val name: String,
    val avatarUrl: String? = null,
    val lastMessage: String = "",
    val time: String = "",
    val unreadCount: Int = 0
)
