package com.ai.socialworld.presentation.map

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.ai.socialworld.domain.service.CharacterLocation
import com.ai.socialworld.domain.service.MapStats

/**
 * 地图页面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MapScreen(
    viewModel: MapViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    var selectedCharacterId by remember { mutableStateOf<String?>(null) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // 顶部栏
        TopAppBar(
            title = { Text("世界地图") },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer
            ),
            actions = {
                IconButton(onClick = { viewModel.refreshLocations() }) {
                    Icon(Icons.Default.Refresh, contentDescription = "刷新")
                }
            }
        )
        
        // 地图区域
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
        ) {
            if (uiState.isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.align(Alignment.Center)
                )
            } else {
                // 简化的2D地图视图
                SimpleMapView(
                    locations = uiState.locations,
                    characterLocations = uiState.characterLocations,
                    onCharacterClick = { characterId ->
                        selectedCharacterId = characterId
                    }
                )
            }
        }
        
        // 底部信息面板
        BottomInfoPanel(
            stats = uiState.stats,
            selectedCharacterId = selectedCharacterId,
            characterName = selectedCharacterId?.let { 
                uiState.characterLocations[it]?.let { loc ->
                    uiState.characterNames[loc.characterId]
                }
            },
            onDismiss = { selectedCharacterId = null }
        )
    }
}

/**
 * 简化的2D地图视图
 */
@Composable
fun SimpleMapView(
    locations: List<com.ai.socialworld.data.model.Location>,
    characterLocations: Map<String, CharacterLocation>,
    onCharacterClick: (String) -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFE8F5E9)) // 浅绿色背景
    ) {
        // 绘制位置点
        locations.forEach { location ->
            LocationMarker(
                location = location,
                modifier = Modifier.offset(
                    x = (location.latitude / 10).dp,
                    y = (location.longitude / 10).dp
                )
            )
        }
        
        // 绘制角色位置
        characterLocations.forEach { (characterId, location) ->
            CharacterMarker(
                characterId = characterId,
                latitude = location.latitude,
                longitude = location.longitude,
                onClick = { onCharacterClick(characterId) }
            )
        }
    }
}

/**
 * 位置标记
 */
@Composable
fun LocationMarker(
    location: com.ai.socialworld.data.model.Location,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            imageVector = when (location.type) {
                com.ai.socialworld.data.model.LocationType.HOME -> Icons.Default.Home
                com.ai.socialworld.data.model.LocationType.OFFICE -> Icons.Default.Business
                com.ai.socialworld.data.model.LocationType.RESTAURANT -> Icons.Default.Restaurant
                com.ai.socialworld.data.model.LocationType.CAFE -> Icons.Default.LocalCafe
                com.ai.socialworld.data.model.LocationType.BAR -> Icons.Default.LocalBar
                com.ai.socialworld.data.model.LocationType.PARK -> Icons.Default.Park
                com.ai.socialworld.data.model.LocationType.SHOPPING_MALL -> Icons.Default.ShoppingCart
                com.ai.socialworld.data.model.LocationType.SCHOOL -> Icons.Default.School
                com.ai.socialworld.data.model.LocationType.HOSPITAL -> Icons.Default.LocalHospital
                else -> Icons.Default.Place
            },
            contentDescription = location.name,
            tint = Color(0xFF4CAF50),
            modifier = Modifier.size(24.dp)
        )
        Text(
            text = location.name,
            style = MaterialTheme.typography.labelSmall,
            color = Color.DarkGray
        )
    }
}

/**
 * 角色标记
 */
@Composable
fun CharacterMarker(
    characterId: String,
    latitude: Double,
    longitude: Double,
    onClick: () -> Unit
) {
    IconButton(
        onClick = onClick,
        modifier = Modifier
            .offset(
                x = (latitude / 10).dp,
                y = (longitude / 10).dp
            )
            .size(32.dp)
    ) {
        Box(
            modifier = Modifier
                .size(28.dp)
                .clip(CircleShape)
                .background(Color(0xFF2196F3)),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = characterId.take(1),
                style = MaterialTheme.typography.labelMedium,
                color = Color.White,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

/**
 * 底部信息面板
 */
@Composable
fun BottomInfoPanel(
    stats: MapStats,
    selectedCharacterId: String?,
    characterName: String?,
    onDismiss: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            if (selectedCharacterId != null && characterName != null) {
                // 显示选中角色信息
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "角色: $characterName",
                        style = MaterialTheme.typography.titleMedium
                    )
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "关闭")
                    }
                }
                
                Text(
                    text = "ID: $selectedCharacterId",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            } else {
                // 显示统计信息
                Text(
                    text = "世界统计",
                    style = MaterialTheme.typography.titleMedium
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    StatItem("位置点", stats.totalLocations.toString())
                    StatItem("角色", stats.totalCharacters.toString())
                    StatItem("在线", stats.activeCharacters.toString())
                    StatItem("相遇", stats.activeEncounters.toString())
                }
            }
        }
    }
}

/**
 * 统计项
 */
@Composable
fun StatItem(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = value,
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary
        )
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
