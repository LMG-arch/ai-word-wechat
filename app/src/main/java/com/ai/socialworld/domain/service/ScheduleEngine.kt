package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.*
import com.ai.socialworld.domain.repository.ApiConfigRepository
import com.ai.socialworld.domain.repository.CharacterRepository
import com.ai.socialworld.domain.repository.RelationshipRepository
import com.ai.socialworld.domain.repository.ScheduleRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.random.Random

/**
 * 日程引擎
 * 每日自动生成角色日程
 */
@Singleton
class ScheduleEngine @Inject constructor(
    private val scheduleRepository: ScheduleRepository,
    private val characterRepository: CharacterRepository,
    private val relationshipRepository: RelationshipRepository,
    private val apiConfigRepository: ApiConfigRepository
) {
    
    // 权重配置
    companion object {
        const val OCCUPATION_WEIGHT = 0.4f   // 职业 40%
        const val PERSONALITY_WEIGHT = 0.3f  // 性格 30%
        const val RELATIONSHIP_WEIGHT = 0.2f // 关系 20%
        const val ECONOMY_WEIGHT = 0.1f      // 经济 10%
        
        // 时间段
        const val MORNING_START = 6
        const val WORK_START = 9
        const val LUNCH_START = 12
        const val AFTERNOON_START = 14
        const val EVENING_START = 18
        const val NIGHT_START = 21
    }
    
    /**
     * 为角色生成今日日程
     */
    suspend fun generateDailySchedule(
        characterId: String
    ): List<Schedule> = withContext(Dispatchers.IO) {
        
        val character = characterRepository.getCharacterById(characterId.toLong())
            ?: return@withContext emptyList()
        
        val events = mutableListOf<ScheduleEvent>()
        
        // 1. 职业相关活动 (40%权重)
        generateOccupationEvents(character, events)
        
        // 2. 性格调整 (30%权重)
        applyPersonalityAdjustments(character, events)
        
        // 3. 关系约会 (20%权重)
        generateSocialEvents(character, events)
        
        // 4. 经济影响 (10%权重)
        generateEconomyEvents(character, events)
        
        // 5. 填充空闲时间
        fillFreeTime(events, character)
        
        // 排序并创建日程对象
        val today = System.currentTimeMillis()
        val startOfDay = today - (today % (24 * 60 * 60 * 1000))
        
        events.sortedBy { it.startHour }.map { event ->
            Schedule(
                characterId = characterId,
                date = today,
                startTime = startOfDay + (event.startHour * 60 * 60 * 1000),
                endTime = startOfDay + (event.endHour * 60 * 60 * 1000),
                location = event.location,
                activity = event.activity,
                relatedEntity = event.relatedCharacterId,
                status = ScheduleStatus.PLANNED,
                createdAt = System.currentTimeMillis()
            )
        }
    }
    
    /**
     * 生成职业相关活动
     */
    private fun generateOccupationEvents(character: Character, events: MutableList<ScheduleEvent>) {
        when {
            character.occupation.contains("程序员") || character.occupation.contains("开发") -> {
                events.add(ScheduleEvent(9, 12, "办公室", "编程开发"))
                events.add(ScheduleEvent(14, 18, "办公室", "编程开发"))
            }
            character.occupation.contains("咖啡师") -> {
                events.add(ScheduleEvent(7, 12, "咖啡馆", "工作"))
                events.add(ScheduleEvent(14, 18, "咖啡馆", "工作"))
            }
            character.occupation.contains("设计师") -> {
                events.add(ScheduleEvent(10, 12, "工作室", "设计创作"))
                events.add(ScheduleEvent(14, 18, "工作室", "设计创作"))
            }
            character.occupation.contains("学生") -> {
                events.add(ScheduleEvent(8, 12, "学校", "上课"))
                events.add(ScheduleEvent(14, 17, "学校", "自习"))
            }
            character.occupation.contains("医生") -> {
                events.add(ScheduleEvent(8, 12, "医院", "门诊"))
                events.add(ScheduleEvent(14, 17, "医院", "查房"))
            }
            else -> {
                // 默认工作
                events.add(ScheduleEvent(9, 12, "工作地点", "工作"))
                events.add(ScheduleEvent(14, 18, "工作地点", "工作"))
            }
        }
    }
    
    /**
     * 应用性格调整
     */
    private fun applyPersonalityAdjustments(character: Character, events: MutableList<ScheduleEvent>) {
        // 社恐 - 不去酒吧、派对等
        if (character.personality.contains("社恐") || character.personality.contains("内向")) {
            events.removeAll { event ->
                event.location == "酒吧" || event.activity.contains("聚会")
            }
            // 添加独处活动
            events.add(ScheduleEvent(19, 21, "家", "阅读/独处"))
        }
        
        // 外向 - 喜欢社交
        if (character.personality.contains("外向") || character.personality.contains("开朗")) {
            if (Random.nextFloat() < 0.4f) {
                events.add(ScheduleEvent(19, 22, "酒吧", "社交聚会"))
            }
        }
        
        // 勤奋 - 加班
        if (character.personality.contains("勤奋") || character.personality.contains("努力")) {
            events.removeAll { it.startHour == 18 }
            events.add(ScheduleEvent(18, 20, "办公室", "加班"))
        }
        
        // 懒惰 - 摸鱼
        if (character.personality.contains("懒惰") || character.personality.contains("摸鱼")) {
            events.removeAll { it.startHour == 14 }
            events.add(ScheduleEvent(14, 16, "咖啡厅", "休息"))
            events.add(ScheduleEvent(16, 18, "工作地点", "工作"))
        }
    }
    
    /**
     * 生成社交活动
     */
    private suspend fun generateSocialEvents(
        character: Character,
        events: MutableList<ScheduleEvent>
    ) = withContext(Dispatchers.IO) {
        // 获取好友
        val relationships = relationshipRepository.getHighIntimacyRelationships(
            characterId = character.id.toString(),
            minIntimacy = RelationshipEngine.FAMILIAR_THRESHOLD
        )
        
        if (relationships.isNotEmpty() && Random.nextFloat() < 0.3f) {
            val friend = relationships.random()
            
            // 随机选择社交时间
            val socialHour = when {
                Random.nextBoolean() -> 12 // 午餐
                else -> 19 // 晚餐
            }
            
            events.add(ScheduleEvent(
                startHour = socialHour,
                endHour = socialHour + 2,
                location = "餐厅",
                activity = "与朋友吃饭",
                relatedCharacterId = friend.targetCharacterId
            ))
        }
    }
    
    /**
     * 生成经济相关活动
     */
    private fun generateEconomyEvents(character: Character, events: MutableList<ScheduleEvent>) {
        // 贫困 - 找兼职
        if (character.money < 20) {
            events.removeAll { it.startHour == 18 }
            events.add(ScheduleEvent(18, 21, "兼职地点", "找兼职"))
        }
        
        // 富裕 - 消费
        if (character.money > 100 && Random.nextFloat() < 0.2f) {
            events.add(ScheduleEvent(19, 21, "商场", "购物"))
        }
    }
    
    /**
     * 填充空闲时间
     */
    private fun fillFreeTime(events: MutableList<ScheduleEvent>, character: Character) {
        // 添加基础活动
        if (!events.any { it.startHour in 7..8 }) {
            events.add(ScheduleEvent(7, 8, "家", "早餐"))
        }
        
        if (!events.any { it.startHour in 12..13 }) {
            events.add(ScheduleEvent(12, 13, "餐厅", "午餐"))
        }
        
        if (!events.any { it.startHour >= 21 }) {
            events.add(ScheduleEvent(21, 23, "家", "休息"))
        }
        
        // 周末活动（简化判断）
        if (Random.nextFloat() < 0.3f) {
            val freeSlots = findFreeSlots(events)
            if (freeSlots.isNotEmpty()) {
                val slot = freeSlots.random()
                events.add(ScheduleEvent(
                    startHour = slot.first,
                    endHour = slot.second,
                    location = "户外",
                    activity = "散步/运动"
                ))
            }
        }
    }
    
    /**
     * 查找空闲时间段
     */
    private fun findFreeSlots(events: List<ScheduleEvent>): List<Pair<Int, Int>> {
        val busyHours = events.flatMap { it.startHour until it.endHour }.toSet()
        val freeSlots = mutableListOf<Pair<Int, Int>>()
        
        var freeStart: Int? = null
        for (hour in 6..23) {
            if (hour !in busyHours && freeStart == null) {
                freeStart = hour
            } else if (hour in busyHours && freeStart != null) {
                if (hour - freeStart >= 2) {
                    freeSlots.add(freeStart to hour)
                }
                freeStart = null
            }
        }
        
        return freeSlots
    }
    
    /**
     * 为所有角色生成日程
     */
    suspend fun generateAllDailySchedules(): Int = withContext(Dispatchers.IO) {
        val characters = characterRepository.getAllCharactersSync()
        var count = 0
        
        characters.forEach { character ->
            val schedules = generateDailySchedule(character.id.toString())
            schedules.forEach { schedule ->
                scheduleRepository.insertSchedule(schedule)
            }
            count++
            
            // 记录日志
            apiConfigRepository.addLog(
                characterId = character.id.toString(),
                characterName = character.name,
                logType = com.ai.socialworld.domain.repository.LogType.SYSTEM,
                content = "生成今日日程: ${schedules.size}个活动"
            )
        }
        
        count
    }
    
    /**
     * 获取角色当前活动
     */
    suspend fun getCurrentActivity(characterId: String): Schedule? = withContext(Dispatchers.IO) {
        val now = System.currentTimeMillis()
        scheduleRepository.getCurrentSchedule(characterId, now)
    }
    
    // 内部数据类
    private data class ScheduleEvent(
        val startHour: Int,
        val endHour: Int,
        val location: String,
        val activity: String,
        val relatedCharacterId: String? = null
    )
}
