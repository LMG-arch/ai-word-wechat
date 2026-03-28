package com.ai.wechat.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.ai.wechat.ui.screens.chat.ChatListScreen
import com.ai.wechat.ui.screens.contacts.ContactsScreen
import com.ai.wechat.ui.screens.groups.GroupListScreen
import com.ai.wechat.ui.screens.tasks.TaskListScreen
import com.ai.wechat.ui.screens.discover.DiscoverScreen
import com.ai.wechat.ui.screens.mine.MineScreen
import com.ai.wechat.ui.screens.character.CharacterDetailScreen
import com.ai.wechat.ui.screens.chat.ChatDetailScreen

/**
 * 应用导航
 */
sealed class Screen(val route: String) {
    object ChatList : Screen("chat_list")
    object Contacts : Screen("contacts")
    object Groups : Screen("groups")
    object Tasks : Screen("tasks")
    object Discover : Screen("discover")
    object Mine : Screen("mine")
    object CharacterDetail : Screen("character_detail/{characterId}") {
        fun createRoute(characterId: String) = "character_detail/$characterId"
    }
    object ChatDetail : Screen("chat_detail/{characterId}") {
        fun createRoute(characterId: String) = "chat_detail/$characterId"
    }
}

@Composable
fun AppNavigation() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = "main"
    ) {
        composable("main") {
            MainScreen(navController = navController)
        }
        composable(Screen.CharacterDetail.route) { backStackEntry ->
            val characterId = backStackEntry.arguments?.getString("characterId") ?: return@composable
            CharacterDetailScreen(
                characterId = characterId,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        composable(Screen.ChatDetail.route) { backStackEntry ->
            val characterId = backStackEntry.arguments?.getString("characterId") ?: return@composable
            ChatDetailScreen(
                characterId = characterId,
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}
