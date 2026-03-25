package com.ai.socialworld.presentation.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.ai.socialworld.data.model.ApiType
import com.ai.socialworld.presentation.components.TopAppBar
import java.util.UUID

/**
 * API配置页面 - 支持多模型配置
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ApiConfigScreen(
    viewModel: ApiConfigViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    var showAddDialog by remember { mutableStateOf(false) }
    var selectedType by remember { mutableStateOf<ApiType?>(null) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = "API配置",
                onNavigateBack = onNavigateBack,
                actions = {
                    IconButton(onClick = { showAddDialog = true }) {
                        Icon(Icons.Default.Add, contentDescription = "添加配置")
                    }
                }
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
        ) {
            // 语言模型配置
            item {
                ConfigSectionTitle("语言模型", Icons.Default.Chat)
            }
            items(uiState.languageConfigs) { config ->
                ApiConfigItem(
                    config = config,
                    isPrimary = config.isPrimary,
                    onSetPrimary = { viewModel.setPrimaryConfig(ApiType.LANGUAGE, config.id) },
                    onDelete = { viewModel.deleteConfig(config) }
                )
            }
            
            item { Spacer(modifier = Modifier.height(16.dp)) }
            
            // 图像模型配置
            item {
                ConfigSectionTitle("图像模型", Icons.Default.Image)
            }
            items(uiState.imageConfigs) { config ->
                ApiConfigItem(
                    config = config,
                    isPrimary = config.isPrimary,
                    onSetPrimary = { viewModel.setPrimaryConfig(ApiType.IMAGE, config.id) },
                    onDelete = { viewModel.deleteConfig(config) }
                )
            }
            
            item { Spacer(modifier = Modifier.height(16.dp)) }
            
            // 向量模型配置
            item {
                ConfigSectionTitle("向量模型", Icons.Default.Memory)
            }
            items(uiState.vectorConfigs) { config ->
                ApiConfigItem(
                    config = config,
                    isPrimary = config.isPrimary,
                    onSetPrimary = { viewModel.setPrimaryConfig(ApiType.VECTOR, config.id) },
                    onDelete = { viewModel.deleteConfig(config) }
                )
            }
        }
    }
    
    // 添加配置对话框
    if (showAddDialog) {
        AddApiConfigDialog(
            onDismiss = { showAddDialog = false },
            onConfirm = { name, apiType, apiUrl, apiKey, modelName ->
                viewModel.addConfig(
                    name = name,
                    apiType = apiType,
                    apiUrl = apiUrl,
                    apiKey = apiKey,
                    modelName = modelName
                )
                showAddDialog = false
            }
        )
    }
}

@Composable
private fun ConfigSectionTitle(title: String, icon: androidx.compose.ui.graphics.vector.ImageVector) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        verticalAlignment = androidx.compose.ui.Alignment.CenterVertically
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = androidx.compose.ui.text.font.FontWeight.Bold
        )
    }
}

@Composable
private fun ApiConfigItem(
    config: ApiConfigUiItem,
    isPrimary: Boolean,
    onSetPrimary: () -> Unit,
    onDelete: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = androidx.compose.ui.Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = config.name,
                        style = MaterialTheme.typography.titleSmall
                    )
                    Text(
                        text = config.modelName,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = config.apiUrl,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                
                Row {
                    if (isPrimary) {
                        Badge(
                            containerColor = MaterialTheme.colorScheme.primary
                        ) {
                            Text("主", color = MaterialTheme.colorScheme.onPrimary)
                        }
                    } else {
                        TextButton(onClick = onSetPrimary) {
                            Text("设为主")
                        }
                    }
                    
                    IconButton(onClick = onDelete) {
                        Icon(Icons.Default.Delete, contentDescription = "删除")
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AddApiConfigDialog(
    onDismiss: () -> Unit,
    onConfirm: (name: String, apiType: ApiType, apiUrl: String, apiKey: String, modelName: String) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var apiType by remember { mutableStateOf(ApiType.LANGUAGE) }
    var apiUrl by remember { mutableStateOf("") }
    var apiKey by remember { mutableStateOf("") }
    var modelName by remember { mutableStateOf("") }
    var expanded by remember { mutableStateOf(false) }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("添加API配置") },
        text = {
            Column {
                // 名称
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("配置名称") },
                    modifier = Modifier.fillMaxWidth()
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // 类型选择
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = it }
                ) {
                    OutlinedTextField(
                        value = when (apiType) {
                            ApiType.LANGUAGE -> "语言模型"
                            ApiType.IMAGE -> "图像模型"
                            ApiType.VECTOR -> "向量模型"
                        },
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("API类型") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    
                    ExposedDropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false }
                    ) {
                        DropdownMenuItem(
                            text = { Text("语言模型") },
                            onClick = { apiType = ApiType.LANGUAGE; expanded = false }
                        )
                        DropdownMenuItem(
                            text = { Text("图像模型") },
                            onClick = { apiType = ApiType.IMAGE; expanded = false }
                        )
                        DropdownMenuItem(
                            text = { Text("向量模型") },
                            onClick = { apiType = ApiType.VECTOR; expanded = false }
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // API URL
                OutlinedTextField(
                    value = apiUrl,
                    onValueChange = { apiUrl = it },
                    label = { Text("API地址") },
                    placeholder = { Text("https://api.openai.com/v1") },
                    modifier = Modifier.fillMaxWidth()
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // API Key
                OutlinedTextField(
                    value = apiKey,
                    onValueChange = { apiKey = it },
                    label = { Text("API Key") },
                    modifier = Modifier.fillMaxWidth()
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // 模型名称
                OutlinedTextField(
                    value = modelName,
                    onValueChange = { modelName = it },
                    label = { Text("模型名称") },
                    placeholder = { 
                        when (apiType) {
                            ApiType.LANGUAGE -> Text("gpt-4, claude-3等")
                            ApiType.IMAGE -> Text("dall-e-3, stable-diffusion等")
                            ApiType.VECTOR -> Text("text-embedding-3等")
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    if (name.isNotBlank() && apiUrl.isNotBlank() && apiKey.isNotBlank() && modelName.isNotBlank()) {
                        onConfirm(name, apiType, apiUrl, apiKey, modelName)
                    }
                }
            ) {
                Text("添加")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消")
            }
        }
    )
}

// 数据类
data class ApiConfigUiItem(
    val id: String,
    val name: String,
    val apiType: ApiType,
    val apiUrl: String,
    val apiKey: String,
    val modelName: String,
    val isPrimary: Boolean
)
