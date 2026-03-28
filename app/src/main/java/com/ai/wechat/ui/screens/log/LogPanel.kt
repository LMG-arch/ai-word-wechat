package com.ai.wechat.ui.screens.log

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.fonts.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ai.wechat.ui.theme.SuccessColor

/**
 * 日志条目
 */
data class LogEntry(
    val timestamp: String,
    val characterName: String,
    val actionType: String,
    val description: String
)

/**
 * 实时日志面板
 */
@Composable
fun LogPanel(
    logs: List<LogEntry>,
    onClear: () -> Unit
) {
    val listState = rememberLazyListState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("实时日志") },
                actions = {
                    IconButton(onClick = onClear) {
                        Icon(Icons.Filled.Clear, contentDescription = "清空")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { paddingValues ->
        if (logs.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Text("暂无日志", style = MaterialTheme.typography.bodyLarge)
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                state = listState,
                contentPadding = PaddingValues(12.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                items(logs) { log ->
                    LogEntryItem(log = log)
                }
            }
        }
    }
}

@Composable
fun LogEntryItem(log: LogEntry) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)
            )
            .padding(8.dp)
    ) {
        // 时间戳
        Text(
            text = "[${log.timestamp}]",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.width(90.dp)
        )

        // 角色名
        Text(
            text = "[${log.characterName}]",
            style = MaterialTheme.typography.labelMedium,
            color = SuccessColor,
            modifier = Modifier.width(100.dp),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )

        // 行为类型
        Text(
            text = "[${log.actionType}]",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.width(80.dp)
        )

        // 描述
        Text(
            text = log.description,
            style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.weight(1f)
        )
    }
}

/**
 * 日志面板（简化版，用于嵌入其他页面）
 */
@Composable
fun CompactLogPanel(
    logs: List<LogEntry>,
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()

    LazyColumn(
        modifier = modifier
            .fillMaxWidth()
            .height(200.dp)
            .background(
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.1f)
            ),
        state = listState,
        contentPadding = PaddingValues(8.dp),
        verticalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        items(logs.takeLast(20)) { log ->
            CompactLogEntryItem(log = log)
        }
    }
}

@Composable
fun CompactLogEntryItem(log: LogEntry) {
    Text(
        text = "[${log.timestamp}] [${log.characterName}] [${log.actionType}] ${log.description}",
        style = MaterialTheme.typography.bodySmall,
        fontSize = 10.sp,
        maxLines = 2,
        overflow = TextOverflow.Ellipsis
    )
}
