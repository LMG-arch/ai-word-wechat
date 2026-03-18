package com.ai.socialworld.presentation.character

data class CreateCharacterUiState(
    val name: String = "",
    val age: Int = 18,
    val gender: String = "MALE",
    val occupation: String = "",
    val personality: String = "",
    val avatarUrl: String? = null,
    val isLoading: Boolean = false,
    val error: String? = null,
    val avatarGenerationCount: Int = 0
) {
    companion object {
        const val MAX_AVATAR_GENERATIONS = 3
    }

    val canGenerateMoreAvatars: Boolean
        get() = avatarGenerationCount < MAX_AVATAR_GENERATIONS

    val isCreateButtonEnabled: Boolean
        get() = name.isNotBlank() && age in 1..150 && occupation.isNotBlank() && personality.isNotBlank() && avatarUrl != null
}
