package com.ai.socialworld.data.local

import androidx.room.TypeConverter
import com.ai.socialworld.data.model.*

/**
 * Room类型转换器 - 简化版，使用Long代替Instant
 */
class Converters {
    
    // Gender <-> String
    @TypeConverter
    fun fromGender(gender: Gender?): String? {
        return gender?.name
    }
    
    @TypeConverter
    fun toGender(value: String?): Gender? {
        return value?.let { Gender.valueOf(it) }
    }
    
    // GrowthStage <-> String
    @TypeConverter
    fun fromGrowthStage(stage: GrowthStage?): String? {
        return stage?.name
    }
    
    @TypeConverter
    fun toGrowthStage(value: String?): GrowthStage? {
        return value?.let { GrowthStage.valueOf(it) }
    }
    
    // TaskStatus <-> String
    @TypeConverter
    fun fromTaskStatus(status: TaskStatus?): String? {
        return status?.name
    }
    
    @TypeConverter
    fun toTaskStatus(value: String?): TaskStatus? {
        return value?.let { TaskStatus.valueOf(it) }
    }
    
    // TaskDifficulty <-> String
    @TypeConverter
    fun fromTaskDifficulty(difficulty: TaskDifficulty?): String? {
        return difficulty?.name
    }
    
    @TypeConverter
    fun toTaskDifficulty(value: String?): TaskDifficulty? {
        return value?.let { TaskDifficulty.valueOf(it) }
    }
    
    // TaskType <-> String
    @TypeConverter
    fun fromTaskType(type: TaskType?): String? {
        return type?.name
    }
    
    @TypeConverter
    fun toTaskType(value: String?): TaskType? {
        return value?.let { TaskType.valueOf(it) }
    }
    
    // MemoryType <-> String
    @TypeConverter
    fun fromMemoryType(type: MemoryType?): String? {
        return type?.name
    }
    
    @TypeConverter
    fun toMemoryType(value: String?): MemoryType? {
        return value?.let { MemoryType.valueOf(it) }
    }
    
    // SkillType <-> String
    @TypeConverter
    fun fromSkillType(type: SkillType?): String? {
        return type?.name
    }
    
    @TypeConverter
    fun toSkillType(value: String?): SkillType? {
        return value?.let { SkillType.valueOf(it) }
    }
    
    // RelationshipType <-> String
    @TypeConverter
    fun fromRelationshipType(type: RelationshipType?): String? {
        return type?.name
    }
    
    @TypeConverter
    fun toRelationshipType(value: String?): RelationshipType? {
        return value?.let { RelationshipType.valueOf(it) }
    }
    
    // InteractionAction <-> String
    @TypeConverter
    fun fromInteractionAction(action: InteractionAction?): String? {
        return action?.name
    }
    
    @TypeConverter
    fun toInteractionAction(value: String?): InteractionAction? {
        return value?.let { InteractionAction.valueOf(it) }
    }
    
    // CompanyRole <-> String
    @TypeConverter
    fun fromCompanyRole(role: CompanyRole?): String? {
        return role?.name
    }
    
    @TypeConverter
    fun toCompanyRole(value: String?): CompanyRole? {
        return value?.let { CompanyRole.valueOf(it) }
    }
    
    // LocationType <-> String
    @TypeConverter
    fun fromLocationType(type: LocationType?): String? {
        return type?.name
    }
    
    @TypeConverter
    fun toLocationType(value: String?): LocationType? {
        return value?.let { LocationType.valueOf(it) }
    }
    
    // ApiType <-> String
    @TypeConverter
    fun fromApiType(type: ApiType?): String? {
        return type?.name
    }
    
    @TypeConverter
    fun toApiType(value: String?): ApiType? {
        return value?.let { ApiType.valueOf(it) }
    }
    
    // LogType <-> String
    @TypeConverter
    fun fromLogType(type: LogType?): String? {
        return type?.name
    }
    
    @TypeConverter
    fun toLogType(value: String?): LogType? {
        return value?.let { LogType.valueOf(it) }
    }
}
