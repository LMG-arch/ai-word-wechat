package com.ai.socialworld.presentation.logs

import androidx.compose.foundation.background
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
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.ai.socialworld.data.model.LogType

/**
 * 日志面板页面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LogPanelScreen(
    viewModel: LogPanelViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    var selectedType by remember { mutableStateOf<LogType?>(null) }
    var searchText by remember { mutableStateOf("") }
    var isRunning by remember { mutableStateOf(false) }
    var timeMultiplier by remember { mutableStateOf(1) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // 顶部控制栏
        TopAppBar(
            title = { Text("日志面板") },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer
            ),
            actions = {
                // 时间控制
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.padding(end = 8.dp)
                ) {
                    IconButton(onClick = { isRunning = !isRunning }) {
                        Icon(
                            imageVector = if (isRunning) Icons.Default.Pause else Icons.Default.PlayArrow,
                            contentDescription = if (isRunning) "暂停" else "开始"
                        )
                    }
                    
                    Text(
                        text = "${timeMultiplier}x",
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.padding(horizontal = 8.dp)
                    )
                    
                    // 速度调节
                    Slider(
                        value = timeMultiplier.toFloat(),
                        onValueChange = { timeMultiplier = it.toInt().coerceIn(1, 30) },
                        valueRange = 1f..30f,
                        modifier = Modifier.width(100.dp)
                    )
                }
            }
        )
        
        // 过滤栏
        FilterBar(
            selectedType = selectedType,
            onTypeSelected = { selectedType = it },
            searchText = searchText,
            onSearchTextChanged = { searchText = it }
        )
        
        // 日志列表
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            contentPadding = PaddingValues(8.dp)
        ) {
            // 显示过滤后的日志
            val filteredLogs = if (searchText.isNotBlank()) {
                uiState.logs.filter { 
                    it.content.contains(searchText, ignoreCase = true) ||
                    it.characterName?.contains(searchText, ignoreCase = true) == true
                }
            } else {
                uiState.logs
            }
            
            val finalLogs = if (selectedType != null) {
                filteredLogs.filter { it.type == selectedType }
            } else {
                filteredLogs
            }
            
            items(finalLogs) { log ->
                LogItem(log = log)
            }
        }
        
        // 底部状态栏
        BottomStatusBar(
            totalLogs = uiState.logs.size,
            filteredLogs = finalLogs.size,
            isRunning = isRunning
        )
    }
}

/**
 * 过滤栏
 */
@Composable
fun FilterBar(
    selectedType: LogType?,
    onTypeSelected: (LogType?) -> Unit,
    searchText: String,
    onSearchTextChanged: (String) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // 类型过滤
        FilterChip(
            selected = selectedType == null,
            onClick = { onTypeSelected(null) },
            label = { Text("全部") }
        )
        
        LogType.values().forEach { type ->
            FilterChip(
                selected = selectedType == type,
                onClick = { onTypeSelected(type) },
                label = { Text(type.name) },
                colors = FilterChipDefaults.filterChipColors(
                    containerColor = getTypeColor(type).copy(alpha = 0.2f)
                )
            )
        }
    }
    
    // 搜索框
    OutlinedTextField(
        value = searchText,
        onValueChange = onSearchTextChanged,
        placeholder = { Text("搜索日志...") },
        leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
        singleLine = true,
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 8.dp)
    )
}

/**
 * 日志条目
 */
@Composable
fun LogItem(log: com.ai.socialworld.domain.service.LogEntry) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        colors = CardDefaults.cardColors(
            containerColor = getTypeColor(log.type).copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            verticalAlignment = Alignment.Top
        ) {
            // 时间
            Text(
                text = "[${log.formattedTime}]",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = FontFamily.Monospace,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.width(80.dp)
            )
            
            // 角色名
            log.characterName?.let { name ->
                Text(
                    text = "[$name]",
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(start = 4.dp)
                )
            }
            
            // 类型标签
            Surface(
                color = getTypeColor(log.type),
                shape = MaterialTheme.shapes.small,
                modifier = Modifier.padding(start = 4.dp)
            ) {
                Text(
                    text = "[${log.type.name}]",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White,
                    modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                )
            }
            
            // 内容
            Text(
                text = log.content,
                style = MaterialTheme.typography.bodySmall,
                fontFamily = FontFamily.Monospace,
                modifier = Modifier
                    .weight(1f)
                    .padding(start = 8.dp)
            )
        }
    }
}

/**
 * 底部状态栏
 */
@Composable
fun BottomStatusBar(
    totalLogs: Int,
    filteredLogs: Int,
    isRunning: Boolean
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surfaceVariant,
        tonalElevation = 2.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "总计: $totalLogs 条 | 显示: $filteredLogs 条",
                style = MaterialTheme.typography.bodySmall
            )
            
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (isRunning) {
                    Icon(
                        imageVector = Icons.Default.Circle,
                        contentDescription = "运行中",
                        tint = Color.Green,
                        modifier = Modifier.size(12.dp)
                    )
                    Text(
                        text = " 运行中",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.Green
                    )
                } else {
                    Icon(
                        imageVector = Icons.Default.Pause,
                        contentDescription = "已暂停",
                        tint = Color.Gray,
                        modifier = Modifier.size(12.dp)
                    )
                    Text(
                        text = " 已暂停",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.Gray
                    )
                }
            }
        }
    }
}

/**
 * 获取日志类型颜色
 */
@Composable
fun getTypeColor(type: LogType): Color {
    return when (type) {
        LogType.TASK -> Color(0xFF4CAF50)    // 绿色
        LogType.SOCIAL -> Color(0xFF2196F3)   // 蓝色
        LogType.MEMORY -> Color(0xFF9C27B0)   // 紫色
        LogType.ECONOMY -> Color(0xFFFF9800)   // 橙色
        LogType.SYSTEM -> Color(0xFF607D8B)   // 灰色
    }
}
