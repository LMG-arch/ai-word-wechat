package com.ai.wechat

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.ai.wechat.ui.screens.chat.ChatListScreen
import com.ai.wechat.ui.theme.AIWeChatTheme
import org.junit.Rule
import org.junit.Test

/**
 * UI 测试示例
 */
class ChatListScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun chatList_emptyState_showsPlaceholder() {
        composeTestRule.setContent {
            AIWeChatTheme {
                ChatListScreen(
                    onCharacterClick = { },
                    onChatClick = { }
                )
            }
        }

        // 测试空状态显示占位符
        composeTestRule.onNodeWithText("暂无消息").assertExists()
    }
}
