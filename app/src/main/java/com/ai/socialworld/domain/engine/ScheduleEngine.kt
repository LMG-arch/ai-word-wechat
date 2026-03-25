package com.ai.socialworld.domain.engine

import com.ai.socialworld.data.model.*
import java.time.LocalDate
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 日程引擎
 * 处理日程生成、管理、位置更新等
 */
@Singleton
class ScheduleEngine @Inject constructor() {
    
    companion object {
        val WEIGHT_OCCUPATION = 0.4
        val WEIGHT_PERSONALITY = 0.3
        val WEIGHT_RELATIONSHIP = 0.2
        val WEIGHT_ECONOMY = 0.1
    }
    
    /**
     * 生成每日日程
     */
    fun generateDailySchedule(
        character: Character,
        date: LocalDate,
        friends: List<Character> = emptyList()
    ): Schedule {
        val events = mutableListOf<ScheduleEvent>()
        
        // 根据职业生成工作日程
        val workEvents = generateWorkEvents(character)
        events.addAll(workEvents)
        
        // 根据性格生成休闲活动
        val leisureEvents = generateLeisureEvents(character)
        events.addAll(leisureEvents)
        
        // 根据关系生成社交活动
        if (friends.isNotEmpty()) {
            val socialEvents = generateSocialEvents(character, friends)
            events.addAll(socialEvents)
        }
        
        // 根据经济状况调整活动
        val adjustedEvents = adjustEventsByEconomy(events, character.money)
        
        return Schedule(
            id = "schedule_${character.id}_${date}",
            characterId = character.id.toString(),
            date = date.toString(),
            events = adjustedEvents.sortedBy { it.startTime }
        )
    }
    
    /**
     * 生成工作日程
     */
    private fun generateWorkEvents(character: Character): List<ScheduleEvent> {
        if (!character.canWork()) return emptyList()
        
        return listOf(
            ScheduleEvent(
                id = "event_${System.currentTimeMillis()}_work",
                startTime = LocalTime.of(9, 0),
                endTime = LocalTime.of(12, 0),
                location = "办公室",
                activity = "工作",
                description = "${character.occupation}工作"
            ),
            ScheduleEvent(
                id = "event_${System.currentTimeMillis()}_lunch",
                startTime = LocalTime.of(12, 0),
                endTime = LocalTime.of(13, 0),
                location = "餐厅",
                activity = "午餐",
                description = "享用午餐"
            ),
            ScheduleEvent(
                id = "event_${System.currentTimeMillis()}_work2",
                startTime = LocalTime.of(13, 0),
                endTime = LocalTime.of(18, 0),
                location = "办公室",
                activity = "工作",
                description = "${character.occupation}工作"
            )
        )
    }
    
    /**
     * 生成休闲活动
     */
    private fun generateLeisureEvents(character: Character): List<ScheduleEvent> {
        val activities = when {
            character.personality.contains("运动") -> listOf("健身房", "公园跑步", "游泳")
            character.personality.contains("阅读") -> listOf("图书馆", "书店", "咖啡厅")
            character.personality.contains("社交") -> listOf("酒吧", "咖啡厅", "餐厅")
            else -> listOf("公园", "咖啡厅", "商场")
        }
        
        return listOf(
            ScheduleEvent(
                id = "event_${System.currentTimeMillis()}_evening",
                startTime = LocalTime.of(19, 0),
                endTime = LocalTime.of(22, 0),
                location = activities.random(),
                activity = "休闲",
                description = "休闲活动"
            )
        )
    }
    
    /**
     * 生成社交活动
     */
    private fun generateSocialEvents(
        character: Character,
        friends: List<Character>
    ): List<ScheduleEvent> {
        return listOf(
            ScheduleEvent(
                id = "event_${System.currentTimeMillis()}_social",
                startTime = LocalTime.of(20, 0),
                endTime = LocalTime.of(22, 0),
                location = "咖啡厅",
                activity = "社交",
                description = "与朋友聚会",
                possibleCharacters = friends.take(3).map { it.id.toString() }
            )
        )
    }
    
    /**
     * 根据经济状况调整活动
     */
    private fun adjustEventsByEconomy(
        events: List<ScheduleEvent>,
        money: Int
    ): List<ScheduleEvent> {
        if (money < 20) {
            // 资金紧张时减少消费活动
            return events.map { event ->
                if (event.location in listOf("餐厅", "酒吧", "咖啡厅")) {
                    event.copy(location = "公园", description = "散步")
                } else {
                    event
                }
            }
        }
        return events
    }
    
    /**
     * 检查相遇事件
     */
    fun checkMeeting(
        character1: Character,
        character2: Character,
        schedule1: Schedule,
        schedule2: Schedule
    ): Boolean {
        val currentTime = LocalTime.now()
        
        val event1 = schedule1.getCurrentEvent(currentTime)
        val event2 = schedule2.getCurrentEvent(currentTime)
        
        // 检查是否在同一地点
        return event1?.location == event2?.location
    }
}
