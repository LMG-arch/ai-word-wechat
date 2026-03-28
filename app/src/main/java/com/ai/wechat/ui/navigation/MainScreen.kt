package com.ai.wechat.ui.navigation

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavController

/**
 * 底部导航项
 */
data class BottomNavItem(
    val screen: Screen,
    val title: String,
    val icon: ImageVector
)

@Composable
fun MainScreen(navController: NavController) {
    val navItems = listOf(
        BottomNavItem(Screen.ChatList, "聊天", Icons.Filled.Chat),
        BottomNavItem(Screen.Contacts, "通讯录", Icons.Filled.Contacts),
        BottomNavItem(Screen.Groups, "群聊", Icons.Filled.People),
        BottomNavItem(Screen.Tasks, "任务", Icons.Filled.Assignment),
        BottomNavItem(Screen.Discover, "发现", Icons.Filled.Explore),
        BottomNavItem(Screen.Mine, "我", Icons.Filled.Person)
    )

    var selectedTab by remember { mutableStateOf(0) }

    Scaffold(
        bottomBar = {
            NavigationBar {
                navItems.forEachIndexed { index, item ->
                    NavigationBarItem(
                        icon = { Icon(item.icon, contentDescription = item.title) },
                        label = { Text(item.title) },
                        selected = selectedTab == index,
                        onClick = { selectedTab = index }
                    )
                }
            }
        }
    ) { paddingValues ->
        androidx.compose.runtime.Composable {
            when (selectedTab) {
                0 -> ChatListScreen(
                    onCharacterClick = { characterId ->
                        navController.navigate(Screen.CharacterDetail.createRoute(characterId))
                    },
                    onChatClick = { characterId ->
                        navController.navigate(Screen.ChatDetail.createRoute(characterId))
                    }
                )
                1 -> ContactsScreen(
                    onCharacterClick = { characterId ->
                        navController.navigate(Screen.CharacterDetail.createRoute(characterId))
                    }
                )
                2 -> GroupListScreen(
                    onGroupClick = { }
                )
                3 -> TaskListScreen(
                    onTaskClick = { }
                )
                4 -> DiscoverScreen()
                5 -> MineScreen()
            }
        }
    }
}
