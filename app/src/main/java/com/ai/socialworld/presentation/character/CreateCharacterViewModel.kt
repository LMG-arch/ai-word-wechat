package com.ai.socialworld.presentation.character

import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.model.Character
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.presentation.base.BaseViewModel
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CreateCharacterViewModel @Inject constructor(
    private val characterRepository: CharacterRepository
) : BaseViewModel<CreateCharacterUiState>() {

    override fun createInitialState(): CreateCharacterUiState = CreateCharacterUiState()

    val uiState: StateFlow<CreateCharacterUiState> = stateFlow

    fun updateName(name: String) {
        updateState { copy(name = name) }
    }

    fun updateAge(age: Int) {
        updateState { copy(age = age.coerceIn(1, 150)) }
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

    fun generateAvatar() {
        if (!currentState.canGenerateMoreAvatars) return

        viewModelScope.launch {
            updateState { copy(isLoading = true, error = null) }
            
            try {
                val avatarUrl = callImageModelAPI()
                updateState { 
                    copy(
                        avatarUrl = avatarUrl,
                        avatarGenerationCount = avatarGenerationCount + 1,
                        isLoading = false
                    ) 
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
                val character = Character(
                    name = currentState.name,
                    age = currentState.age,
                    gender = currentState.gender,
                    occupation = currentState.occupation,
                    personality = currentState.personality,
                    avatarUrl = currentState.avatarUrl!!
                )
                
                characterRepository.createCharacter(character)
                
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

    private suspend fun callImageModelAPI(): String {
        delay(1500)
        val prompts = listOf("anime_character_1", "anime_character_2", "anime_character_3")
        val randomPrompt = prompts.random()
        return "https://api.example.com/avatars/$randomPrompt_${System.currentTimeMillis()}.jpg"
    }

    private fun onCharacterCreatedSuccess() {
        updateState { CreateCharacterUiState() }
    }
}
