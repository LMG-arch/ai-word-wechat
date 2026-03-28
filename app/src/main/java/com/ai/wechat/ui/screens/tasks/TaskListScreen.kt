package com.ai.wechat.ui.screens.tasks

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ai.wechat.data.model.Task
import com.ai.wechat.data.model.TaskStatus
import com.ai.wechat.data.model.TaskType

@Composable
fun TaskListScreen(
    onTaskClick: (String) -> Unit
) {
    // TODO: 从 ViewModel 获取实际数据
    val tasks = remember { mutableStateListOf<Task>() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("任务") },
                actions = {
                    IconButton(onClick = { /* TODO: 创建任务 */ }) {
                        Icon(Icons.Filled.Add, contentDescription = "创建任务")
                    }
                },
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
            items(tasks) { task ->
                TaskItem(
                    task = task,
                    onClick = { onTaskClick(task.id) }
                )
            }
        }
    }
}

@Composable
fun TaskItem(
    task: Task,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = task.title,
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.weight(1f)
                )

                Spacer(modifier = Modifier.width(8.dp))

                // 状态标签
                StatusBadge(task.status)
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = task.description,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 2
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                // 任务类型
                AssistChip(
                    onClick = { },
                    label = { Text(task.type.displayName) }
                )

                // 奖励
                Text(
                    text = "奖励：${task.reward}",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
    }
}

@Composable
fun StatusBadge(status: TaskStatus) {
    val (text, color) = when (status) {
        TaskStatus.PENDING -> "待接取" to MaterialTheme.colorScheme.secondary
        TaskStatus.IN_PROGRESS -> "进行中" to MaterialTheme.colorScheme.primary
        TaskStatus.REVIEWING -> "审核中" to MaterialTheme.colorScheme.tertiary
        TaskStatus.COMPLETED -> "已完成" to MaterialTheme.colorScheme.primary
        TaskStatus.FAILED -> "失败" to MaterialTheme.colorScheme.error
    }

    Surface(
        color = color.copy(alpha = 0.2f),
        shape = MaterialTheme.shapes.small
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            color = color,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        )
    }
}

val TaskType.displayName: String
    get() = when (this) {
        TaskType.TEXT_GENERATION -> "文本生成"
        TaskType.IMAGE_GENERATION -> "图像生成"
        TaskType.CODE_WRITING -> "代码编写"
        TaskType.RESEARCH -> "调研分析"
        TaskType.CREATIVE_DESIGN -> "创意设计"
    }
