package com.ai.socialworld.presentation.discover

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ai.socialworld.presentation.components.TopAppBar

/**
 * 发现页面（仿微信发现 tab）
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiscoverScreen(
    onNavigateToMoments: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(title = "发现")
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // 朋友圈
            DiscoverItem(
                icon = Icons.Default.PhotoCamera,
                title = "朋友圈",
                onClick = onNavigateToMoments
            )
            
            Divider()
            
            // 直播
            DiscoverItem(
                icon = Icons.Default.LiveTv,
                title = "直播",
                onClick = { /* TODO */ }
            )
            
            Divider()
            
            // 小程序
            DiscoverItem(
                icon = Icons.Default.Apps,
                title = "小程序",
                onClick = { /* TODO */ }
            )
            
            Divider()
            
            // 游戏
            DiscoverItem(
                icon = Icons.Default.SportsEsports,
                title = "游戏",
                onClick = { /* TODO */ }
            )
            
            Divider()
            
            // 迷你应用
            DiscoverItem(
                icon = Icons.Default.Web,
                title = "迷你应用",
                onClick = { /* TODO */ }
            )
            
            Divider()
            
            // 购物
            DiscoverItem(
                icon = Icons.Default.ShoppingCart,
                title = "购物",
                onClick = { /* TODO */ }
            )
            
            Divider()
            
            // AI世界
            DiscoverItem(
                icon = Icons.Default.AutoAwesome,
                title = "AI世界",
                onClick = { /* TODO */ }
            )
        }
    }
}

@Composable
private fun DiscoverItem(
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

@Composable
private fun ListItem(
    headlineContent: @Composable () -> Unit,
    leadingContent: @Composable (() -> Unit)? = null,
    trailingContent: @Composable (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    androidx.compose.material3.ListItem(
        headlineContent = headlineContent,
        leadingContent = leadingContent,
        trailingContent = trailingContent,
        modifier = modifier
    )
}

@Composable
private fun Divider() {
    HorizontalDivider(modifier = Modifier.padding(start = 56.dp))
}
