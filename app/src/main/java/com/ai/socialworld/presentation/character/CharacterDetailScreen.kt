package com.ai.socialworld.presentation.character

import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.rememberAsyncImagePainter
import com.ai.socialworld.presentation.components.TopAppBar

/**
 * 角色详情页面
 */
@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun CharacterDetailScreen(
    characterId: String,
    viewModel: CharacterDetailViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit,
    onNavigateToChat: () -> Unit,
    onNavigateToMoments: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    
    LaunchedEffect(characterId) {
        viewModel.loadCharacter(characterId)
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = "角色详情",
                onNavigateBack = onNavigateBack
            )
        }
    ) { paddingValues ->
        if (uiState.isLoading) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            uiState.character?.let { character ->
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                        .verticalScroll(rememberScrollState())
                ) {
                    // 头部信息卡片
                    CharacterHeaderCard(
                        character = character,
                        onSendMessage = onNavigateToChat,
                        onViewMoments = onNavigateToMoments
                    )
                    
                    HorizontalDivider()
                    
                    // 基本信息
                    BasicInfoSection(character = character)
                    
                    HorizontalDivider()
                    
                    // 性格标签
                    if (character.personality.isNotEmpty()) {
                        PersonalitySection(personality = character.personality)
                        HorizontalDivider()
                    }
                    
                    // 技能展示
                    SkillSection(skills = uiState.skills)
                    
                    HorizontalDivider()
                    
                    // 最近反思
                    if (uiState.recentReflections.isNotEmpty()) {
                        ReflectionsSection(reflections = uiState.recentReflections)
                        HorizontalDivider()
                    }
                    
                    // 今日日程
                    if (uiState.todaySchedule != null) {
                        ScheduleSection(schedule = uiState.todaySchedule)
                    }
                }
            }
        }
    }
}

@Composable
private fun CharacterHeaderCard(
    character: CharacterDetail,
    onSendMessage: () -> Unit,
    onViewMoments: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // 大头像
            if (character.avatarUrl != null) {
                Image(
                    painter = rememberAsyncImagePainter(character.avatarUrl),
                    contentDescription = null,
                    modifier = Modifier
                        .size(120.dp)
                        .padding(bottom = 16.dp),
                    contentScale = ContentScale.Crop
                )
            } else {
                Surface(
                    modifier = Modifier
                        .size(120.dp)
                        .padding(bottom = 16.dp),
                    shape = MaterialTheme.shapes.medium,
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Default.Person,
                            contentDescription = null,
                            modifier = Modifier.size(60.dp),
                            tint = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                }
            }
            
            // 昵称
            Text(
                text = character.name,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold
            )
            
            // 签名
            if (character.signature.isNotEmpty()) {
                Text(
                    text = character.signature,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 4.dp)
                )
            }
            
            // 操作按钮
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 16.dp),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                ActionButton(
                    icon = Icons.Default.Chat,
                    label = "发消息",
                    onClick = onSendMessage
                )
                ActionButton(
                    icon = Icons.Default.PhotoCamera,
                    label = "朋友圈",
                    onClick = onViewMoments
                )
                ActionButton(
                    icon = Icons.Default.AttachMoney,
                    label = "赠送资金",
                    onClick = { /* TODO */ }
                )
            }
        }
    }
}

@Composable
private fun ActionButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    onClick: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.clickable { onClick() }
    ) {
        Surface(
            shape = MaterialTheme.shapes.small,
            color = MaterialTheme.colorScheme.primaryContainer,
            modifier = Modifier.size(48.dp)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    imageVector = icon,
                    contentDescription = label,
                    tint = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }
        }
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.padding(top = 4.dp)
        )
    }
}

@Composable
private fun BasicInfoSection(character: CharacterDetail) {
    Column(
        modifier = Modifier.padding(16.dp)
    ) {
        Text(
            text = "基本信息",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 12.dp)
        )
        
        InfoRow(label = "年龄", value = "${character.age}岁")
        InfoRow(label = "性别", value = if (character.gender == "MALE") "男" else "女")
        InfoRow(label = "职业", value = character.occupation)
        InfoRow(label = "成长阶段", value = character.growthStage)
        InfoRow(label = "资金余额", value = "${character.money}资金")
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
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

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun PersonalitySection(personality: String) {
    Column(
        modifier = Modifier.padding(16.dp)
    ) {
        Text(
            text = "性格特点",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 12.dp)
        )
        
        // 将性格描述分割成标签
        val tags = personality.split("、", ",", "，", " ").filter { it.isNotBlank() }
        FlowRow(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            tags.forEach { tag ->
                AssistChip(
                    onClick = {},
                    label = { Text(tag.trim()) }
                )
            }
        }
    }
}

@Composable
private fun SkillSection(skills: Map<String, Int>) {
    Column(
        modifier = Modifier.padding(16.dp)
    ) {
        Text(
            text = "技能分布",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 12.dp)
        )
        
        skills.forEach { (skill, level) ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = skill,
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.weight(1f)
                )
                LinearProgressIndicator(
                    progress = { level / 100f },
                    modifier = Modifier.width(100.dp),
                )
                Text(
                    text = "$level",
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.width(40.dp)
                )
            }
        }
    }
}

@Composable
private fun ReflectionsSection(reflections: List<String>) {
    Column(
        modifier = Modifier.padding(16.dp)
    ) {
        Text(
            text = "最近反思",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 12.dp)
        )
        
        reflections.take(3).forEach { reflection ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp)
            ) {
                Text(
                    text = reflection,
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(12.dp),
                    maxLines = 3
                )
            }
        }
    }
}

@Composable
private fun ScheduleSection(schedule: String) {
    Column(
        modifier = Modifier.padding(16.dp)
    ) {
        Text(
            text = "今日日程",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 12.dp)
        )
        
        Text(
            text = schedule,
            style = MaterialTheme.typography.bodyMedium
        )
    }
}

// 数据类
data class CharacterDetail(
    val id: String,
    val name: String,
    val avatarUrl: String? = null,
    val signature: String = "",
    val age: Int = 18,
    val gender: String = "MALE",
    val occupation: String = "",
    val growthStage: String = "",
    val money: Int = 0,
    val personality: String = ""
)
