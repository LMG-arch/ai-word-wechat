package com.ai.wechat.ui.screens.groups

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.ai.wechat.data.model.GroupChat
import com.ai.wechat.data.model.GroupChatType

@Composable
fun GroupListScreen(
    onGroupClick: (String) -> Unit
) {
    // TODO: 从 ViewModel 获取实际数据
    val groupChats = remember { mutableStateListOf<GroupChat>() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("群聊") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            items(groupChats) { groupChat ->
                GroupChatItem(
                    groupChat = groupChat,
                    onClick = { onGroupClick(groupChat.id) }
                )
            }
        }
    }
}

@Composable
fun GroupChatItem(
    groupChat: GroupChat,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // 群头像
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(MaterialTheme.shapes.small)
        ) {
            AsyncImage(
                model = groupChat.avatarUrl,
                contentDescription = groupChat.name,
                modifier = Modifier.fillMaxSize()
            )
        }

        Spacer(modifier = Modifier.width(12.dp))

        // 内容
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Row {
                    Text(
                        text = groupChat.name,
                        style = MaterialTheme.typography.titleMedium,
                        maxLines = 1
                    )

                    Spacer(modifier = Modifier.width(8.dp))

                    // 群类型标识
                    val typeIcon = when (groupChat.type) {
                        GroupChatType.PRIVATE -> "👥"
                        GroupChatType.COMPANY -> "🏢"
                    }
                    Text(text = typeIcon)
                }

                groupChat.lastMessageTime?.let { time ->
                    Text(
                        text = formatTime(time),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = groupChat.lastMessage ?: "",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
    }

    HorizontalDivider()
}

private fun formatTime(timestamp: Long): String {
    val now = System.currentTimeMillis()
    val diff = now - timestamp
    return when {
        diff < 60000 -> "刚刚"
        diff < 3600000 -> "${diff / 60000}分钟前"
        diff < 86400000 -> "${diff / 3600000}小时前"
        else -> "${diff / 86400000}天前"
    }
}
