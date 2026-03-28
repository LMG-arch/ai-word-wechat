package com.ai.wechat.ui.screens.character

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.ai.wechat.data.model.Character

@Composable
fun CharacterDetailScreen(
    characterId: String,
    onNavigateBack: () -> Unit
) {
    // TODO: 从 ViewModel 获取实际数据
    val character = remember { mutableStateOf<Character?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("角色详情") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "返回")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { paddingValues ->
        character.value?.let { char ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .verticalScroll(rememberScrollState())
            ) {
                // 头像和签名
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    AsyncImage(
                        model = char.avatarUrl,
                        contentDescription = char.name,
                        modifier = Modifier
                            .size(100.dp)
                            .clip(MaterialTheme.shapes.large)
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    Text(
                        text = char.name,
                        style = MaterialTheme.typography.headlineMedium
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = char.signature ?: "暂无签名",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                Divider()

                // 基本信息
                CharacterInfoSection(character = char)

                Divider()

                // 技能雷达图（TODO）
                SkillsSection(character = char)

                Divider()

                // 今日日程
                ScheduleSection(character = char)

                Divider()

                // 他的好友（TODO）
                FriendsSection(character = char)

                Divider()

                // 最近反思
                ReflectionsSection(character = char)

                Spacer(modifier = Modifier.height(16.dp))

                // 操作按钮
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Button(
                        onClick = { /* TODO: 发消息 */ },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("发消息")
                    }

                    OutlinedButton(
                        onClick = { /* TODO: 看朋友圈 */ },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("看朋友圈")
                    }

                    OutlinedButton(
                        onClick = { /* TODO: 赠送资金 */ },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("赠送资金")
                    }
                }
            }
        } ?: run {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        }
    }
}

@Composable
fun CharacterInfoSection(character: Character) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Text(
            text = "基本信息",
            style = MaterialTheme.typography.titleMedium
        )

        Spacer(modifier = Modifier.height(12.dp))

        InfoRow("年龄", "${character.age}岁")
        InfoRow("性别", character.gender)
        InfoRow("职业", character.occupation)
        InfoRow("性格", character.personality)
        InfoRow("资金", "${character.money}")
    }
}

@Composable
fun InfoRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium
        )
    }
}

@Composable
fun SkillsSection(character: Character) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Text(
            text = "技能",
            style = MaterialTheme.typography.titleMedium
        )

        Spacer(modifier = Modifier.height(12.dp))

        // TODO: 绘制技能雷达图
        Text("技能雷达图开发中...", style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
fun ScheduleSection(character: Character) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Text(
            text = "今日日程",
            style = MaterialTheme.typography.titleMedium
        )

        Spacer(modifier = Modifier.height(12.dp))

        // TODO: 显示日程
        Text("暂无日程", style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
fun FriendsSection(character: Character) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Text(
            text = "他的好友",
            style = MaterialTheme.typography.titleMedium
        )

        Spacer(modifier = Modifier.height(12.dp))

        // TODO: 显示好友列表
        Text("暂无好友", style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
fun ReflectionsSection(character: Character) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Text(
            text = "最近反思",
            style = MaterialTheme.typography.titleMedium
        )

        Spacer(modifier = Modifier.height(12.dp))

        // TODO: 显示反思列表
        Text("暂无反思", style = MaterialTheme.typography.bodyMedium)
    }
}
