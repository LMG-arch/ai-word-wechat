package com.ai.socialworld.presentation.profile

import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import coil.compose.rememberAsyncImagePainter
import com.ai.socialworld.presentation.components.TopAppBar

/**
 * 个人中心页面（仿微信"我"页面）
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(
    onNavigateToSettings: () -> Unit,
    onNavigateToApiConfig: () -> Unit,
    onNavigateToWorldSettings: () -> Unit,
    onNavigateToLogPanel: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(title = "我")
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // 用户信息卡片
            UserInfoCard()
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // 设置列表
            SettingsSection(
                onNavigateToSettings = onNavigateToSettings,
                onNavigateToApiConfig = onNavigateToApiConfig,
                onNavigateToWorldSettings = onNavigateToWorldSettings,
                onNavigateToLogPanel = onNavigateToLogPanel
            )
        }
    }
}

@Composable
private fun UserInfoCard() {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 头像
            Surface(
                modifier = Modifier.size(64.dp),
                shape = MaterialTheme.shapes.medium,
                color = MaterialTheme.colorScheme.primaryContainer
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = Icons.Default.Person,
                        contentDescription = null,
                        modifier = Modifier.size(32.dp),
                        tint = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }
            
            Spacer(modifier = Modifier.width(16.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "管理员",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "微信号: admin123",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            Icon(Icons.Default.QrCode, contentDescription = "二维码")
        }
    }
}

@Composable
private fun SettingsSection(
    onNavigateToSettings: () -> Unit,
    onNavigateToApiConfig: () -> Unit,
    onNavigateToWorldSettings: () -> Unit,
    onNavigateToLogPanel: () -> Unit
) {
    Column {
        // API配置
        SettingsItem(
            icon = Icons.Default.Api,
            title = "API配置",
            onClick = onNavigateToApiConfig
        )
        
        HorizontalDivider(modifier = Modifier.padding(start = 56.dp))
        
        // 世界设置
        SettingsItem(
            icon = Icons.Default.Public,
            title = "世界设置",
            onClick = onNavigateToWorldSettings
        )
        
        HorizontalDivider(modifier = Modifier.padding(start = 56.dp))
        
        // 日志面板
        SettingsItem(
            icon = Icons.Default.Terminal,
            title = "日志面板",
            onClick = onNavigateToLogPanel
        )
        
        HorizontalDivider(modifier = Modifier.padding(start = 56.dp))
        
        // 通用设置
        SettingsItem(
            icon = Icons.Default.Settings,
            title = "设置",
            onClick = onNavigateToSettings
        )
        
        HorizontalDivider(modifier = Modifier.padding(start = 56.dp))
        
        // 关于
        SettingsItem(
            icon = Icons.Default.Info,
            title = "关于",
            onClick = { /* TODO */ }
        )
    }
}

@Composable
private fun SettingsItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    onClick: () -> Unit
) {
    ListItem(
        headlineContent = { Text(title) },
        leadingContent = {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary
            )
        },
        trailingContent = {
            Icon(Icons.Default.ChevronRight, contentDescription = null)
        },
        modifier = Modifier.clickable { onClick() }
    )
}
