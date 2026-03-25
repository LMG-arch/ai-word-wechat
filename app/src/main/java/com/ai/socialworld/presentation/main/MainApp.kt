package com.ai.socialworld.presentation.main

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.ai.socialworld.presentation.components.BottomNavigationBar
import com.ai.socialworld.presentation.navigation.Screen
import com.ai.socialworld.presentation.chat.ChatScreen
import com.ai.socialworld.presentation.chat.ChatDetailScreen
import com.ai.socialworld.presentation.contacts.ContactsScreen
import com.ai.socialworld.presentation.groups.GroupsScreen
import com.ai.socialworld.presentation.tasks.TasksScreen
import com.ai.socialworld.presentation.discover.DiscoverScreen
import com.ai.socialworld.presentation.profile.ProfileScreen
import com.ai.socialworld.presentation.character.CreateCharacterScreen
import com.ai.socialworld.presentation.character.CharacterDetailScreen
import com.ai.socialworld.presentation.settings.ApiConfigScreen
import com.ai.socialworld.presentation.discover.MomentsScreen

/**
 * 主界面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainApp() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route ?: Screen.Chat.route
    
    // 底部导航栏可见性
    val showBottomBar = currentRoute in Screen.bottomNavItems.map { it.route }
    
    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                BottomNavigationBar(
                    currentRoute = currentRoute,
                    onNavigate = { route ->
                        navController.navigate(route) {
                            popUpTo(navController.graph.startDestinationId) {
                                saveState = true
                            }
                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                )
            }
        }
    ) { paddingValues ->
        NavHost(
            navController = navController,
            startDestination = Screen.Chat.route,
            modifier = Modifier.padding(paddingValues)
        ) {
            // 底部导航栏页面
            composable(Screen.Chat.route) {
                ChatScreen(
                    onNavigateToChat = { characterId ->
                        navController.navigate(Screen.ChatDetail.createRoute(characterId))
                    }
                )
            }
            
            composable(Screen.Contacts.route) {
                ContactsScreen(
                    onNavigateToCharacterDetail = { characterId ->
                        navController.navigate(Screen.CharacterDetail.createRoute(characterId))
                    },
                    onNavigateToCreateCharacter = {
                        navController.navigate(Screen.CreateCharacter.route)
                    }
                )
            }
            
            composable(Screen.Groups.route) {
                GroupsScreen(
                    onNavigateToGroupDetail = { groupId ->
                        navController.navigate(Screen.GroupDetail.createRoute(groupId))
                    }
                )
            }
            
            composable(Screen.Tasks.route) {
                TasksScreen(
                    onNavigateToTaskDetail = { taskId ->
                        navController.navigate(Screen.TaskDetail.createRoute(taskId))
                    }
                )
            }
            
            composable(Screen.Discover.route) {
                DiscoverScreen(
                    onNavigateToMoments = {
                        navController.navigate(Screen.Moments.route)
                    }
                )
            }
            
            composable(Screen.Me.route) {
                ProfileScreen(
                    onNavigateToSettings = {
                        navController.navigate(Screen.Settings.route)
                    },
                    onNavigateToApiConfig = {
                        navController.navigate(Screen.ApiConfig.route)
                    },
                    onNavigateToWorldSettings = {
                        navController.navigate(Screen.WorldSettings.route)
                    },
                    onNavigateToLogPanel = {
                        navController.navigate(Screen.LogPanel.route)
                    }
                )
            }
            
            // 子页面
            composable(Screen.CreateCharacter.route) {
                CreateCharacterScreen(
                    onNavigateBack = { navController.popBackStack() },
                    onCharacterCreated = { navController.popBackStack() }
                )
            }
            
            composable(Screen.ApiConfig.route) {
                ApiConfigScreen(
                    onNavigateBack = { navController.popBackStack() }
                )
            }
            
            // 聊天详情页
            composable(
                route = Screen.ChatDetail.route,
                arguments = listOf(
                    navArgument("characterId") { type = NavType.StringType }
                )
            ) { backStackEntry ->
                val characterId = backStackEntry.arguments?.getString("characterId") ?: ""
                ChatDetailScreen(
                    characterId = characterId,
                    onNavigateBack = { navController.popBackStack() }
                )
            }
            
            // 朋友圈页面
            composable(Screen.Moments.route) {
                MomentsScreen(
                    onNavigateBack = { navController.popBackStack() }
                )
            }

            // 角色详情页
            composable(
                route = Screen.CharacterDetail.route,
                arguments = listOf(
                    navArgument("characterId") { type = NavType.StringType }
                )
            ) { backStackEntry ->
                val characterId = backStackEntry.arguments?.getString("characterId") ?: ""
                CharacterDetailScreen(
                    characterId = characterId,
                    onNavigateBack = { navController.popBackStack() },
                    onNavigateToChat = {
                        navController.navigate(Screen.ChatDetail.createRoute(characterId))
                    },
                    onNavigateToMoments = {
                        navController.navigate(Screen.Moments.route)
                    }
                )
            }

            // TODO: 添加其他子页面路由
        }
    }
}
