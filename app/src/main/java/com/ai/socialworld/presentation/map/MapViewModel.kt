package com.ai.socialworld.presentation.map

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ai.socialworld.data.model.Location
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.domain.service.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 地图ViewModel
 */
@HiltViewModel
class MapViewModel @Inject constructor(
    private val mapService: MapService,
    private val characterRepository: CharacterRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(MapUiState())
    val uiState: StateFlow<MapUiState> = _uiState.asStateFlow()
    
    init {
        loadMapData()
    }
    
    /**
     * 加载地图数据
     */
    private fun loadMapData() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            
            // 获取所有位置
            val locations = mapService.getAllLocations()
            
            // 获取角色位置
            val characterLocations = mapService.getAllCharacterLocations()
            
            // 获取角色名称
            val characterNames = mutableMapOf<String, String>()
            characterRepository.getAllCharactersSync().forEach { character ->
                characterNames[character.id.toString()] = character.name
            }
            
            // 获取统计
            val stats = mapService.getMapStats()
            
            _uiState.update {
                it.copy(
                    locations = locations,
                    characterLocations = characterLocations,
                    characterNames = characterNames,
                    stats = stats,
                    isLoading = false
                )
            }
        }
    }
    
    /**
     * 刷新位置
     */
    fun refreshLocations() {
        viewModelScope.launch {
            val characterLocations = mapService.getAllCharacterLocations()
            val stats = mapService.getMapStats()
            
            _uiState.update {
                it.copy(
                    characterLocations = characterLocations,
                    stats = stats
                )
            }
        }
    }
    
    /**
     * 获取角色位置历史
     */
    fun getCharacterHistory(characterId: String): List<CharacterLocation> {
        return mapService.getCharacterLocationHistory(characterId)
    }
    
    /**
     * 获取相遇记录
     */
    fun getEncounters(characterId: String? = null): List<Encounter> {
        return mapService.getEncounters(characterId)
    }
}

/**
 * 地图UI状态
 */
data class MapUiState(
    val locations: List<Location> = emptyList(),
    val characterLocations: Map<String, CharacterLocation> = emptyMap(),
    val characterNames: Map<String, String> = emptyMap(),
    val stats: MapStats = MapStats(0, 0, 0, 0),
    val isLoading: Boolean = false,
    val error: String? = null
)
