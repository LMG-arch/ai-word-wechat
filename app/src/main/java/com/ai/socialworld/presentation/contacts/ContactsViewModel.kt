package com.ai.socialworld.presentation.contacts

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.domain.repository.CharacterRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 通讯录ViewModel
 */
@HiltViewModel
class ContactsViewModel @Inject constructor(
    private val characterRepository: CharacterRepository
) : ViewModel() {

    private val _characters = MutableStateFlow<List<ContactCharacter>>(emptyList())
    val characters: StateFlow<List<ContactCharacter>> = _characters.asStateFlow()

    init {
        loadCharacters()
    }

    private fun loadCharacters() {
        viewModelScope.launch {
            characterRepository.getAllCharacters()
                .map { list ->
                    list.map { character ->
                        ContactCharacter(
                            id = character.id,
                            name = character.name,
                            avatarUrl = character.avatarUrl,
                            occupation = character.occupation,
                            gender = if (character.gender.name == "MALE") "男" else "女"
                        )
                    }
                }
                .collect { _characters.value = it }
        }
    }
}
