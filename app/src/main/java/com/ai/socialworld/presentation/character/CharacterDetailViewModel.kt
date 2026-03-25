package com.ai.socialworld.presentation.character

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.model.Character
import com.ai.socialworld.domain.repository.CharacterRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 角色详情ViewModel
 */
@HiltViewModel
class CharacterDetailViewModel @Inject constructor(
    private val characterRepository: CharacterRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(CharacterDetailUiState())
    val uiState: StateFlow<CharacterDetailUiState> = _uiState.asStateFlow()

    fun loadCharacter(characterId: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            
            val character = characterRepository.getCharacterById(characterId.toLong())
            character?.let {
                _uiState.update { state ->
                    state.copy(
                        character = CharacterDetail(
                            id = it.id.toString(),
                            name = it.name,
                            avatarUrl = it.avatarUrl,
                            signature = it.signature,
                            age = it.age,
                            gender = it.gender.name,
                            occupation = it.occupation,
                            growthStage = it.growthStage.description,
                            money = it.money,
                            personality = it.personality
                        ),
                        isLoading = false
                    )
                }
                
                // 加载技能数据（暂时用模拟数据）
                loadSkills()
                
                // 加载最近反思（暂时用模拟数据）
                loadRecentReflections()
                
                // 加载今日日程（暂时用模拟数据）
                loadTodaySchedule()
            }
        }
    }

    private fun loadSkills() {
        // TODO: 从数据库加载真实技能数据
        val skills = mapOf(
            "需求理解" to 65,
            "史诗感把控" to 50,
            "细节丰富度" to 70,
            "风格准确性" to 55,
            "修改效率" to 45,
            "团队协作" to 60
        )
        _uiState.update { it.copy(skills = skills) }
    }

    private fun loadRecentReflections() {
        // TODO: 从数据库加载真实反思数据
        val reflections = listOf(
            "在任务中学会了更仔细地检查需求",
            "通过这次失败，我认识到了细节的重要性",
            "团队合作需要更好的沟通"
        )
        _uiState.update { it.copy(recentReflections = reflections) }
    }

    private fun loadTodaySchedule() {
        // TODO: 从数据库加载真实日程数据
        val schedule = """
            09:00-12:00 办公室 工作
            12:00-13:00 餐厅 午餐
            14:00-18:00 办公室 工作
            19:00-21:00 咖啡厅 休闲
        """.trimIndent()
        _uiState.update { it.copy(todaySchedule = schedule) }
    }

    fun sendMoney(amount: Int) {
        // TODO: 实现赠送资金功能
    }
}

/**
 * 角色详情UI状态
 */
data class CharacterDetailUiState(
    val character: CharacterDetail? = null,
    val skills: Map<String, Int> = emptyMap(),
    val recentReflections: List<String> = emptyList(),
    val todaySchedule: String? = null,
    val isLoading: Boolean = false,
    val error: String? = null
)
