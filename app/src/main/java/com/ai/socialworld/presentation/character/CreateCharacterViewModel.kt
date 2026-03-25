package com.ai.socialworld.presentation.character

import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.model.Character
import com.ai.socialworld.data.model.Gender
import com.ai.socialworld.data.model.GrowthStage
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.domain.service.ImageGenerationResult
import com.ai.socialworld.domain.service.ImageGenerationService
import com.ai.socialworld.presentation.base.BaseViewModel
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CreateCharacterViewModel @Inject constructor(
    private val characterRepository: CharacterRepository,
    private val imageGenerationService: ImageGenerationService
) : BaseViewModel<CreateCharacterUiState>() {

    override fun createInitialState(): CreateCharacterUiState = CreateCharacterUiState()

    val uiState: StateFlow<CreateCharacterUiState> = stateFlow

    fun updateName(name: String) {
        updateState { copy(name = name) }
    }

    fun updateAge(age: Int) {
        updateState { 
            copy(
                age = age.coerceIn(1, 150),
                growthStage = GrowthStage.fromAge(age)
            ) 
        }
    }

    fun updateGender(gender: String) {
        updateState { copy(gender = gender) }
    }

    fun updateOccupation(occupation: String) {
        updateState { copy(occupation = occupation) }
    }

    fun updatePersonality(personality: String) {
        updateState { copy(personality = personality) }
    }

    /**
     * 生成角色头像
     */
    fun generateAvatar() {
        if (!currentState.canGenerateMoreAvatars) return

        viewModelScope.launch {
            updateState { copy(isLoading = true, error = null) }
            
            try {
                // 构建角色描述
                val description = buildString {
                    append("A ${currentState.age} year old ${currentState.gender.lowercase()}")
                    append(" working as ${currentState.occupation}")
                    if (currentState.personality.isNotBlank()) {
                        append(" with ${currentState.personality} personality")
                    }
                }
                
                // 调用图像生成服务
                val result = imageGenerationService.generateCharacterAvatar(
                    characterDescription = description,
                    age = currentState.age,
                    gender = currentState.gender,
                    occupation = currentState.occupation,
                    personality = currentState.personality
                )
                
                when (result) {
                    is ImageGenerationResult.Success -> {
                        val avatarUrl = result.imageUrl 
                            ?: result.base64Image?.let { "data:image/png;base64,$it" }
                            ?: ""
                        
                        if (avatarUrl.isNotEmpty()) {
                            updateState { 
                                copy(
                                    avatarUrl = avatarUrl,
                                    avatarGenerationCount = avatarGenerationCount + 1,
                                    isLoading = false
                                ) 
                            }
                        } else {
                            updateState { 
                                copy(
                                    isLoading = false,
                                    error = "头像生成失败：未获取到图像"
                                ) 
                            }
                        }
                    }
                    is ImageGenerationResult.Error -> {
                        updateState { 
                            copy(
                                isLoading = false,
                                error = "头像生成失败：${result.message}"
                            ) 
                        }
                    }
                }
            } catch (e: Exception) {
                updateState { 
                    copy(
                        isLoading = false,
                        error = "头像生成失败：${e.message}"
                    ) 
                }
            }
        }
    }

    fun createCharacter() {
        if (!currentState.isCreateButtonEnabled) return

        viewModelScope.launch {
            updateState { copy(isLoading = true, error = null) }
            
            try {
                val gender = when (currentState.gender) {
                    "MALE" -> Gender.MALE
                    "FEMALE" -> Gender.FEMALE
                    else -> Gender.MALE
                }
                
                val character = Character(
                    name = currentState.name,
                    age = currentState.age,
                    gender = gender,
                    occupation = currentState.occupation,
                    personality = currentState.personality,
                    avatarUrl = currentState.avatarUrl,
                    growthStage = currentState.growthStage,
                    money = 50 // 初始资金50
                )
                
                characterRepository.insertCharacter(character)
                
                updateState { copy(isLoading = false) }
                onCharacterCreatedSuccess()
            } catch (e: Exception) {
                updateState { 
                    copy(
                        isLoading = false,
                        error = "角色创建失败：${e.message}"
                    ) 
                }
            }
        }
    }

    fun clearError() {
        updateState { copy(error = null) }
    }

    private fun onCharacterCreatedSuccess() {
        updateState { CreateCharacterUiState() }
    }
}
