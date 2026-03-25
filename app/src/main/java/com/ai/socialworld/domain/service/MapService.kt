package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.*
import com.ai.socialworld.domain.repository.ApiConfigRepository
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.domain.repository.ScheduleRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.abs
import kotlin.math.sqrt
import kotlin.random.Random

/**
 * 地图服务
 * 管理位置追踪和相遇检测
 */
@Singleton
class MapService @Inject constructor(
    private val characterRepository: CharacterRepository,
    private val scheduleRepository: ScheduleRepository,
    private val apiConfigRepository: ApiConfigRepository,
    private val relationshipEngine: RelationshipEngine,
    private val languageModelService: LanguageModelService
) {
    
    companion object {
        const val ENCOUNTER_RADIUS = 50.0         // 相遇半径（米）
        const val ENCOUNTER_MIN_DURATION = 5 * 60 * 1000L  // 5分钟
        const val WORLD_SIZE = 1000.0            // 世界大小（米）
    }
    
    // 位置存储
    private val characterLocations = mutableMapOf<String, CharacterLocation>()
    private val locations = mutableMapOf<String, Location>()
    private val encounters = mutableListOf<Encounter>()
    
    init {
        // 初始化一些默认位置
        initializeDefaultLocations()
    }
    
    /**
     * 初始化默认位置
     */
    private fun initializeDefaultLocations() {
        val defaultLocations = listOf(
            Location("home_1", "住宅区A", LocationType.HOME, 100.0, 100.0),
            Location("home_2", "住宅区B", LocationType.HOME, 200.0, 300.0),
            Location("office_1", "办公楼A", LocationType.OFFICE, 400.0, 200.0),
            Location("office_2", "办公楼B", LocationType.OFFICE, 500.0, 300.0),
            Location("restaurant_1", "美食街", LocationType.RESTAURANT, 300.0, 400.0),
            Location("cafe_1", "咖啡街", LocationType.CAFE, 350.0, 350.0),
            Location("bar_1", "酒吧街", LocationType.BAR, 450.0, 450.0),
            Location("park_1", "中心公园", LocationType.PARK, 250.0, 250.0),
            Location("mall_1", "购物中心", LocationType.SHOPPING_MALL, 600.0, 400.0)
        )
        
        defaultLocations.forEach { locations[it.id] = it }
    }
    
    /**
     * 更新角色位置
     */
    suspend fun updateCharacterLocation(
        characterId: String,
        latitude: Double,
        longitude: Double,
        locationId: String? = null
    ) = withContext(Dispatchers.IO) {
        
        val previousLocation = characterLocations[characterId]
        
        // 如果之前有位置，记录离开时间
        if (previousLocation != null && previousLocation.leftAt == null) {
            characterLocations[characterId] = previousLocation.copy(
                leftAt = System.currentTimeMillis()
            )
        }
        
        // 创建新位置记录
        val newLocation = CharacterLocation(
            id = UUID.randomUUID().toString(),
            characterId = characterId,
            locationId = locationId ?: findNearestLocation(latitude, longitude)?.id ?: "",
            latitude = latitude,
            longitude = longitude,
            timestamp = System.currentTimeMillis()
        )
        
        characterLocations[characterId] = newLocation
        
        // 检测相遇
        detectEncounters(characterId, latitude, longitude)
    }
    
    /**
     * 根据日程更新角色位置
     */
    suspend fun updateLocationBySchedule(characterId: String) = withContext(Dispatchers.IO) {
        val currentSchedule = scheduleRepository.getCurrentSchedule(characterId, System.currentTimeMillis())
        
        if (currentSchedule != null) {
            // 根据日程中的位置找到对应坐标
            val targetLocation = findLocationByName(currentSchedule.location)
            
            if (targetLocation != null) {
                // 添加一些随机偏移，让位置更自然
                val offsetLat = Random.nextDouble(-20.0, 20.0)
                val offsetLng = Random.nextDouble(-20.0, 20.0)
                
                updateCharacterLocation(
                    characterId = characterId,
                    latitude = targetLocation.latitude + offsetLat,
                    longitude = targetLocation.longitude + offsetLng,
                    locationId = targetLocation.id
                )
            }
        }
    }
    
    /**
     * 检测相遇
     */
    private suspend fun detectEncounters(
        characterId: String,
        latitude: Double,
        longitude: Double
    ) {
        val now = System.currentTimeMillis()
        
        characterLocations.forEach { (otherId, otherLocation) ->
            if (otherId == characterId) return@forEach
            if (otherLocation.leftAt != null) return@forEach
            
            // 计算距离
            val distance = calculateDistance(
                latitude, longitude,
                otherLocation.latitude, otherLocation.longitude
            )
            
            // 检查是否在相遇半径内
            if (distance <= ENCOUNTER_RADIUS) {
                // 检查是否已有相遇记录
                val existingEncounter = encounters.find {
                    (it.characterId1 == characterId && it.characterId2 == otherId ||
                     it.characterId1 == otherId && it.characterId2 == characterId) &&
                    it.endTime == null
                }
                
                if (existingEncounter == null) {
                    // 创建新的相遇记录
                    val encounter = Encounter(
                        id = UUID.randomUUID().toString(),
                        characterId1 = characterId,
                        characterId2 = otherId,
                        locationId = otherLocation.locationId,
                        latitude = (latitude + otherLocation.latitude) / 2,
                        longitude = (longitude + otherLocation.longitude) / 2,
                        startTime = now
                    )
                    
                    encounters.add(encounter)
                    
                    // 记录日志
                    apiConfigRepository.addLog(
                        characterId = characterId,
                        characterName = null,
                        logType = com.ai.socialworld.domain.repository.LogType.SOCIAL,
                        content = "与 $otherId 相遇"
                    )
                }
            } else {
                // 检查是否需要结束相遇
                val existingEncounter = encounters.find {
                    (it.characterId1 == characterId && it.characterId2 == otherId ||
                     it.characterId1 == otherId && it.characterId2 == characterId) &&
                    it.endTime == null
                }
                
                if (existingEncounter != null) {
                    val duration = now - existingEncounter.startTime
                    
                    // 只有超过最小持续时间才记录
                    if (duration >= ENCOUNTER_MIN_DURATION) {
                        // 确定相遇类型
                        val encounterType = determineEncounterType(duration)
                        
                        val index = encounters.indexOf(existingEncounter)
                        encounters[index] = existingEncounter.copy(
                            endTime = now,
                            interactionType = encounterType
                        )
                        
                        // 触发互动
                        handleEncounterInteraction(existingEncounter, duration)
                    } else {
                        // 短暂相遇，移除记录
                        encounters.remove(existingEncounter)
                    }
                }
            }
        }
    }
    
    /**
     * 确定相遇类型
     */
    private fun determineEncounterType(duration: Long): EncounterType {
        return when {
            duration < 2 * 60 * 1000 -> EncounterType.PASS_BY
            duration < 5 * 60 * 1000 -> EncounterType.BRIEF_CHAT
            duration < 15 * 60 * 1000 -> EncounterType.LONG_CONVERSATION
            duration < 30 * 60 * 1000 -> EncounterType.COFFEE
            duration < 60 * 60 * 1000 -> EncounterType.MEAL
            else -> EncounterType.WORK_TOGETHER
        }
    }
    
    /**
     * 处理相遇互动
     */
    private suspend fun handleEncounterInteraction(encounter: Encounter, duration: Long) {
        // 根据相遇类型增加亲密度
        val intimacyChange = when (encounter.interactionType) {
            EncounterType.PASS_BY -> 0
            EncounterType.BRIEF_CHAT -> 1
            EncounterType.LONG_CONVERSATION -> 2
            EncounterType.COFFEE -> 3
            EncounterType.MEAL -> 4
            EncounterType.WORK_TOGETHER -> 5
            null -> 0
        }
        
        if (intimacyChange > 0) {
            // 更新双方亲密度
            relationshipEngine.handleInteraction(
                fromCharacterId = encounter.characterId1,
                toCharacterId = encounter.characterId2,
                interactionType = InteractionType.MEET
            )
        }
    }
    
    /**
     * 计算两点距离（简化版欧几里得距离）
     */
    fun calculateDistance(
        lat1: Double, lng1: Double,
        lat2: Double, lng2: Double
    ): Double {
        return sqrt((lat2 - lat1) * (lat2 - lat1) + (lng2 - lng1) * (lng2 - lng1))
    }
    
    /**
     * 查找最近的位置
     */
    private fun findNearestLocation(latitude: Double, longitude: Double): Location? {
        return locations.values.minByOrNull { location ->
            calculateDistance(latitude, longitude, location.latitude, location.longitude)
        }
    }
    
    /**
     * 根据名称查找位置
     */
    private fun findLocationByName(name: String): Location? {
        return locations.values.find { 
            it.name.contains(name) || name.contains(it.name)
        }
    }
    
    /**
     * 获取角色当前位置
     */
    fun getCharacterLocation(characterId: String): CharacterLocation? {
        return characterLocations[characterId]
    }
    
    /**
     * 获取所有角色位置
     */
    fun getAllCharacterLocations(): Map<String, CharacterLocation> {
        return characterLocations.toMap()
    }
    
    /**
     * 获取所有位置点
     */
    fun getAllLocations(): List<Location> {
        return locations.values.toList()
    }
    
    /**
     * 获取角色的位置历史
     */
    fun getCharacterLocationHistory(characterId: String): List<CharacterLocation> {
        // 简化实现：返回当前位置
        return characterLocations[characterId]?.let { listOf(it) } ?: emptyList()
    }
    
    /**
     * 获取相遇记录
     */
    fun getEncounters(characterId: String? = null): List<Encounter> {
        return if (characterId != null) {
            encounters.filter { 
                it.characterId1 == characterId || it.characterId2 == characterId 
            }
        } else {
            encounters.toList()
        }
    }
    
    /**
     * 添加自定义位置
     */
    fun addLocation(location: Location) {
        locations[location.id] = location
    }
    
    /**
     * 获取地图统计
     */
    fun getMapStats(): MapStats {
        val activeCharacters = characterLocations.count { it.value.leftAt == null }
        val activeEncounters = encounters.count { it.endTime == null }
        
        return MapStats(
            totalLocations = locations.size,
            totalCharacters = characterLocations.size,
            activeCharacters = activeCharacters,
            activeEncounters = activeEncounters
        )
    }
}

/**
 * 地图统计
 */
data class MapStats(
    val totalLocations: Int,
    val totalCharacters: Int,
    val activeCharacters: Int,
    val activeEncounters: Int
)
