package com.ai.socialworld.presentation.contacts

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.PersonAdd
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.ai.socialworld.presentation.components.EmptyState
import com.ai.socialworld.presentation.components.TopAppBar

/**
 * 通讯录页面（仿微信）
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ContactsScreen(
    onNavigateToCharacterDetail: (String) -> Unit,
    onNavigateToCreateCharacter: () -> Unit,
    viewModel: ContactsViewModel = hiltViewModel()
) {
    val characters by viewModel.characters.collectAsState()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = "通讯录",
                actions = {
                    IconButton(onClick = onNavigateToCreateCharacter) {
                        Icon(
                            imageVector = Icons.Default.PersonAdd,
                            contentDescription = "添加角色"
                        )
                    }
                }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = onNavigateToCreateCharacter,
                containerColor = MaterialTheme.colorScheme.primary
            ) {
                Icon(
                    imageVector = Icons.Default.Add,
                    contentDescription = "添加角色"
                )
            }
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // 搜索栏
            SearchBar(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp)
            )
            
            // 角色列表
            if (characters.isEmpty()) {
                EmptyState(
                    icon = Icons.Default.PersonAdd,
                    message = "暂无角色\n点击右下角添加角色",
                    action = {
                        Button(onClick = onNavigateToCreateCharacter) {
                            Text("添加角色")
                        }
                    }
                )
            } else {
                LazyColumn {
                    items(characters) { character ->
                        ContactListItem(
                            character = character,
                            onClick = { onNavigateToCharacterDetail(character.id.toString()) }
                        )
                        Divider()
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SearchBar(
    modifier: Modifier = Modifier
) {
    OutlinedTextField(
        value = "",
        onValueChange = { /* TODO: 搜索 */ },
        placeholder = { Text("搜索") },
        leadingIcon = {
            Icon(
                imageVector = Icons.Default.Search,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
        },
        modifier = modifier,
        singleLine = true,
        colors = TextFieldDefaults.outlinedTextFieldColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    )
}

@Composable
private fun ContactListItem(
    character: ContactCharacter,
    onClick: () -> Unit
) {
    ListItem(
        headlineContent = {
            Text(
                text = character.name,
                fontWeight = FontWeight.Medium
            )
        },
        supportingContent = {
            Text(
                text = "${character.occupation} · ${character.gender}",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        },
        leadingContent = {
            // 头像
            Surface(
                modifier = Modifier.size(48.dp),
                shape = MaterialTheme.shapes.small,
                color = MaterialTheme.colorScheme.primaryContainer
            ) {
                if (character.avatarUrl != null) {
                    // TODO: 加载头像
                }
            }
        },
        modifier = Modifier.clickable { onClick() }
    )
}

// 数据类
data class ContactCharacter(
    val id: Long,
    val name: String,
    val avatarUrl: String? = null,
    val occupation: String = "",
    val gender: String = ""
)
