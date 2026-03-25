package com.ai.socialworld.presentation.components

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*

/**
 * 底部导航栏
 */
@Composable
fun BottomNavigationBar(
    currentRoute: String,
    onNavigate: (String) -> Unit
) {
    val items = listOf(
        BottomNavItem("chat", "聊天", Icons.Default.Chat),
        BottomNavItem("contacts", "通讯录", Icons.Default.Contacts),
        BottomNavItem("groups", "群聊", Icons.Default.Group),
        BottomNavItem("tasks", "任务", Icons.Default.Task),
        BottomNavItem("discover", "发现", Icons.Default.Explore),
        BottomNavItem("me", "我", Icons.Default.Person)
    )

    NavigationBar {
        items.forEach { item ->
            NavigationBarItem(
                icon = { Icon(item.icon, contentDescription = item.label) },
                label = { Text(item.label) },
                selected = currentRoute == item.route,
                onClick = { onNavigate(item.route) }
            )
        }
    }
}

data class BottomNavItem(
    val route: String,
    val label: String,
    val icon: ImageVector
)
