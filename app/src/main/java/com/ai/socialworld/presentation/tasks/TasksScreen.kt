package com.ai.socialworld.presentation.tasks

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.ai.socialworld.data.model.TaskDifficulty
import com.ai.socialworld.data.model.TaskStatus
import com.ai.socialworld.presentation.components.TopAppBar

/**
 * 任务中心页面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TasksScreen(
    viewModel: TasksViewModel = hiltViewModel(),
    onNavigateToTaskDetail: (String) -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    var selectedTab by remember { mutableStateOf(0) }
    
    val tabs = listOf("全部", "待接取", "进行中", "已完成")
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = "任务中心",
                actions = {
                    IconButton(onClick = { /* TODO: 创建任务 */ }) {
                        Icon(Icons.Default.Add, contentDescription = "创建任务")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier.padding(paddingValues)
        ) {
            // Tab切换
            TabRow(selectedTabIndex = selectedTab) {
                tabs.forEachIndexed { index, title ->
                    Tab(
                        selected = selectedTab == index,
                        onClick = { 
                            selectedTab = index
                            viewModel.filterTasks(index)
                        },
                        text = { Text(title) }
                    )
                }
            }
            
            // 任务列表
            if (uiState.isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else if (uiState.tasks.isEmpty()) {
                EmptyTaskState()
            } else {
                LazyColumn {
                    items(uiState.tasks) { task ->
                        TaskItem(
                            task = task,
                            onClick = { onNavigateToTaskDetail(task.id) }
                        )
                        Divider()
                    }
                }
            }
        }
    }
}

@Composable
private fun TaskItem(
    task: TaskItemData,
    onClick: () -> Unit
) {
    ListItem(
        headlineContent = {
            Text(
                text = task.title,
                fontWeight = FontWeight.Medium
            )
        },
        supportingContent = {
            Column {
                Text(
                    text = task.description,
                    maxLines = 2,
                    style = MaterialTheme.typography.bodyMedium
                )
                Row(
                    modifier = Modifier.padding(top = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // 难度标签
                    DifficultyChip(difficulty = task.difficulty)
                    Spacer(modifier = Modifier.width(8.dp))
                    // 奖励
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.AttachMoney,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                        Text(
                            text = "${task.reward}",
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    // 状态标签
                    StatusChip(status = task.status)
                }
            }
        },
        trailingContent = {
            if (task.status == TaskStatus.PENDING) {
                Button(onClick = onClick) {
                    Text("接取")
                }
            } else {
                IconButton(onClick = onClick) {
                    Icon(Icons.Default.ChevronRight, contentDescription = "查看")
                }
            }
        },
        modifier = Modifier.clickable { onClick() }
    )
}

@Composable
private fun DifficultyChip(difficulty: TaskDifficulty) {
    val (color, text) = when (difficulty) {
        TaskDifficulty.EASY -> Color(0xFF4CAF50) to "简单"
        TaskDifficulty.MEDIUM -> Color(0xFFFF9800) to "中等"
        TaskDifficulty.HARD -> Color(0xFFF44336) to "困难"
        TaskDifficulty.EPIC -> Color(0xFF9C27B0) to "史诗"
    }
    
    Surface(
        color = color.copy(alpha = 0.1f),
        shape = MaterialTheme.shapes.small
    ) {
        Text(
            text = text,
            color = color,
            style = MaterialTheme.typography.labelSmall,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
        )
    }
}

@Composable
private fun StatusChip(status: TaskStatus) {
    val (color, text) = when (status) {
        TaskStatus.PENDING -> Color(0xFF2196F3) to "待接取"
        TaskStatus.ASSIGNED -> Color(0xFFFF9800) to "已分配"
        TaskStatus.IN_PROGRESS -> Color(0xFF9C27B0) to "进行中"
        TaskStatus.COMPLETED -> Color(0xFF4CAF50) to "已完成"
        TaskStatus.FAILED -> Color(0xFFF44336) to "失败"
        TaskStatus.CANCELLED -> Color(0xFF757575) to "已取消"
    }
    
    Surface(
        color = color.copy(alpha = 0.1f),
        shape = MaterialTheme.shapes.small
    ) {
        Text(
            text = text,
            color = color,
            style = MaterialTheme.typography.labelSmall,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
        )
    }
}

@Composable
private fun EmptyTaskState() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(
                imageVector = Icons.Default.Assignment,
                contentDescription = null,
                modifier = Modifier.size(64.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "暂无任务",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

// 数据类
data class TaskItemData(
    val id: String,
    val title: String,
    val description: String,
    val difficulty: TaskDifficulty,
    val reward: Int,
    val status: TaskStatus
)
