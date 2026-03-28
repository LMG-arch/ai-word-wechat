package com.ai.wechat.ui.screens.mine

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun MineScreen() {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("我") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
        ) {
            Text(
                text = "设置",
                style = MaterialTheme.typography.titleLarge
            )

            Spacer(modifier = Modifier.height(16.dp))

            // API 配置
            Card(
                modifier = Modifier.fillMaxWidth(),
                onClick = { /* TODO: 打开 API 配置页面 */ }
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("AI 模型配置")
                    Text(">", style = MaterialTheme.typography.titleMedium)
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // 时间倍速
            Card(
                modifier = Modifier.fillMaxWidth(),
                onClick = { /* TODO: 打开时间倍速设置 */ }
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("时间倍速")
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("1x", style = MaterialTheme.typography.bodyMedium)
                        Text(">", style = MaterialTheme.typography.titleMedium)
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // 死亡机制开关
            Card(
                modifier = Modifier.fillMaxWidth(),
                onClick = { /* TODO: 切换死亡机制 */ }
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("死亡机制")
                    Switch(checked = false, onCheckedChange = { })
                }
            }
        }
    }
}
