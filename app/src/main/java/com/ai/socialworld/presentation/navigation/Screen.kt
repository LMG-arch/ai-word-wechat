package com.ai.socialworld.presentation.navigation

sealed class Screen(val route: String) {
    object CreateCharacter : Screen("create_character")
    object CharacterList : Screen("character_list")
    object CharacterDetail : Screen("character_detail/{characterId}") {
        fun createRoute(characterId: String) = "character_detail/$characterId"
    }
}
