package com.ai.socialworld.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.ai.socialworld.data.model.*

/**
 * 应用数据库 - 包含所有实体
 */
@Database(
    entities = [
        Character::class,
        Task::class,
        TaskSubmission::class,
        Memory::class,
        Skill::class,
        SkillHistory::class,
        Reflection::class,
        Relationship::class,
        RelationshipChange::class,
        Company::class,
        CompanyMember::class,
        CompanyKnowledge::class,
        Schedule::class,
        Location::class,
        ApiConfig::class,
        WorldSettings::class,
        SystemLog::class
    ],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun characterDao(): CharacterDao
    abstract fun taskDao(): TaskDao
    abstract fun memoryDao(): MemoryDao
    abstract fun relationshipDao(): RelationshipDao
    abstract fun skillDao(): SkillDao
    abstract fun reflectionDao(): ReflectionDao
    abstract fun companyDao(): CompanyDao
    abstract fun scheduleDao(): ScheduleDao
    abstract fun apiConfigDao(): ApiConfigDao
}
