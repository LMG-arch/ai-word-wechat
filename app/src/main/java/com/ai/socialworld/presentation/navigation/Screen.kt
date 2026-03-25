package com.ai.socialworld.presentation.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.ui.graphics.vector.ImageVector

/**
 * 导航路由定义
 */
sealed class Screen(val route: String, val title: String, val icon: ImageVector? = null) {
    // 底部导航栏页面
    object Chat : Screen("chat", "聊天", Icons.Default.Chat)
    object Contacts : Screen("contacts", "通讯录", Icons.Default.Contacts)
    object Groups : Screen("groups", "群聊", Icons.Default.Groups)
    object Tasks : Screen("tasks", "任务", Icons.Default.Task)
    object Discover : Screen("discover", "发现", Icons.Default.Discover)
    object Me : Screen("me", "我", Icons.Default.Person)
    
    // 子页面
    object CreateCharacter : Screen("create_character", "创建角色")
    object CharacterDetail : Screen("character_detail/{characterId}", "角色详情") {
        fun createRoute(characterId: String) = "character_detail/$characterId"
    }
    object ChatDetail : Screen("chat_detail/{characterId}", "聊天详情") {
        fun createRoute(characterId: String) = "chat_detail/$characterId"
    }
    object GroupDetail : Screen("group_detail/{groupId}", "群聊详情") {
        fun createRoute(groupId: String) = "group_detail/$groupId"
    }
    object TaskDetail : Screen("task_detail/{taskId}", "任务详情") {
        fun createRoute(taskId: String) = "task_detail/$taskId"
    }
    object Moments : Screen("moments", "朋友圈")
    object Settings : Screen("settings", "设置")
    object ApiConfig : Screen("api_config", "API配置")
    object WorldSettings : Screen("world_settings", "世界设置")
    object LogPanel : Screen("log_panel", "日志面板")
    object Map : Screen("map", "地图", Icons.Default.Map)
    object CompanyDetail : Screen("company_detail/{companyId}", "公司详情") {
        fun createRoute(companyId: String) = "company_detail/$companyId"
    }
    
    companion object {
        val bottomNavItems = listOf(Chat, Contacts, Groups, Tasks, Discover, Me)
    }
}
