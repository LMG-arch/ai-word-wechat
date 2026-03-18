package com.ai.socialworld.presentation.character

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.AsyncImage
import coil.request.ImageRequest

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CreateCharacterScreen(
    viewModel: CreateCharacterViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit,
    onCharacterCreated: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("创建角色") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = androidx.compose.material.icons.Icons.Default.ArrowBack,
                            contentDescription = "返回"
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            AvatarSection(
                avatarUrl = uiState.avatarUrl,
                isLoading = uiState.isLoading,
                canGenerateMore = uiState.canGenerateMoreAvatars,
                generationCount = uiState.avatarGenerationCount,
                onGenerateAvatar = { viewModel.generateAvatar() }
            )

            Divider()

            BasicInfoSection(
                name = uiState.name,
                age = uiState.age,
                gender = uiState.gender,
                occupation = uiState.occupation,
                onNameChange = { viewModel.updateName(it) },
                onAgeChange = { viewModel.updateAge(it) },
                onGenderChange = { viewModel.updateGender(it) },
                onOccupationChange = { viewModel.updateOccupation(it) }
            )

            Divider()

            PersonalitySection(
                personality = uiState.personality,
                onPersonalityChange = { viewModel.updatePersonality(it) }
            )

            Spacer(modifier = Modifier.height(16.dp))

            CreateButton(
                isEnabled = uiState.isCreateButtonEnabled,
                isLoading = uiState.isLoading,
                onCreateClick = { viewModel.createCharacter() }
            )

            uiState.error?.let { error ->
                ErrorMessage(
                    error = error,
                    onDismiss = { viewModel.clearError() }
                )
            }
        }
    }
}

@Composable
private fun AvatarSection(
    avatarUrl: String?,
    isLoading: Boolean,
    canGenerateMore: Boolean,
    generationCount: Int,
    onGenerateAvatar: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            text = "角色头像",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )

        Box(
            modifier = Modifier.size(200.dp),
            contentAlignment = Alignment.Center
        ) {
            if (avatarUrl != null) {
                AsyncImage(
                    model = ImageRequest.Builder(LocalContext.current)
                        .data(avatarUrl)
                        .crossfade(true)
                        .build(),
                    contentDescription = "角色头像",
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
            } else {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.surfaceVariant,
                    shape = MaterialTheme.shapes.medium
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = androidx.compose.material.icons.Icons.Default.Person,
                            contentDescription = null,
                            modifier = Modifier.size(80.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(48.dp),
                    strokeWidth = 3.dp
                )
            }
        }

        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "已生成 $generationCount/${CreateCharacterUiState.MAX_AVATAR_GENERATIONS} 次",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Button(
                onClick = onGenerateAvatar,
                enabled = canGenerateMore && !isLoading,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.secondary
                )
            ) {
                Icon(
                    imageVector = androidx.compose.material.icons.Icons.Default.Refresh,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(4.dp))
                Text("重新生成")
            }
        }
    }
}

@Composable
private fun BasicInfoSection(
    name: String,
    age: Int,
    gender: String,
    occupation: String,
    onNameChange: (String) -> Unit,
    onAgeChange: (Int) -> Unit,
    onGenderChange: (String) -> Unit,
    onOccupationChange: (String) -> Unit
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            text = "基础信息",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )

        OutlinedTextField(
            value = name,
            onValueChange = onNameChange,
            label = { Text("昵称") },
            placeholder = { Text("请输入角色昵称") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )

        Row(
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            OutlinedTextField(
                value = age.toString(),
                onValueChange = { 
                    it.toIntOrNull()?.let { ageValue -> onAgeChange(ageValue) }
                    if (it.isEmpty()) onAgeChange(0)
                },
                label = { Text("年龄") },
                modifier = Modifier.weight(1f),
                singleLine = true
            )

            GenderSelector(
                selectedGender = gender,
                onGenderSelected = onGenderChange,
                modifier = Modifier.weight(1f)
            )
        }

        OutlinedTextField(
            value = occupation,
            onValueChange = onOccupationChange,
            label = { Text("职业") },
            placeholder = { Text("请输入角色职业") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )
    }
}

@Composable
private fun GenderSelector(
    selectedGender: String,
    onGenderSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        Text(
            text = "性别",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(4.dp))
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            FilterChip(
                selected = selectedGender == "MALE",
                onClick = { onGenderSelected("MALE") },
                label = { Text("男") },
                modifier = Modifier.weight(1f)
            )
            FilterChip(
                selected = selectedGender == "FEMALE",
                onClick = { onGenderSelected("FEMALE") },
                label = { Text("女") },
                modifier = Modifier.weight(1f)
            )
        }
    }
}

@Composable
private fun PersonalitySection(
    personality: String,
    onPersonalityChange: (String) -> Unit
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            text = "性格设定",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )

        OutlinedTextField(
            value = personality,
            onValueChange = onPersonalityChange,
            label = { Text("性格描述") },
            placeholder = { Text("描述角色的性格特点，如开朗、内向、勇敢等") },
            modifier = Modifier
                .fillMaxWidth()
                .height(120.dp),
            maxLines = 5
        )
    }
}

@Composable
private fun CreateButton(
    isEnabled: Boolean,
    isLoading: Boolean,
    onCreateClick: () -> Unit
) {
    Button(
        onClick = onCreateClick,
        enabled = isEnabled && !isLoading,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        contentPadding = PaddingValues(vertical = 16.dp)
    ) {
        if (isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.size(24.dp),
                strokeWidth = 2.dp,
                color = MaterialTheme.colorScheme.onPrimary
            )
            Spacer(modifier = Modifier.width(12.dp))
            Text("创建中...")
        } else {
            Text(
                text = "创建角色",
                style = MaterialTheme.typography.titleMedium
            )
        }
    }
}

@Composable
private fun ErrorMessage(
    error: String,
    onDismiss: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.errorContainer
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = error,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onErrorContainer,
                modifier = Modifier.weight(1f)
            )
            Spacer(modifier = Modifier.width(16.dp))
            TextButton(onClick = onDismiss) {
                Text("关闭")
            }
        }
    }
}
