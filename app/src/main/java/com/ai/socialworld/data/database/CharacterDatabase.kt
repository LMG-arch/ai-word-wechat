package com.ai.socialworld.data.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverter
import androidx.room.TypeConverters
import com.ai.socialworld.data.database.dao.*
import com.ai.socialworld.data.database.entity.*
import com.ai.socialworld.data.model.*
import java.time.Instant

/**
 * Room 数据库
 */
@Database(
    entities = [
        Character::class,
        TaskEntity::class,
        CompanyEntity::class,
        CompanyMemberEntity::class,
        ScheduleEntity::class,
        LocationEntity::class,
        LocationHistoryEntity::class,
        MomentEntity::class,
        ChatGroupEntity::class,
        ChatMessageEntity::class
    ],
    version = 3,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class CharacterDatabase : RoomDatabase() {
    abstract fun characterDao(): CharacterDao
    abstract fun taskDao(): TaskDao
    abstract fun companyDao(): CompanyDao
    abstract fun scheduleDao(): ScheduleDao
    abstract fun socialDao(): SocialDao

    companion object {
        @Volatile
        private var INSTANCE: CharacterDatabase? = null

        fun getDatabase(context: Context): CharacterDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    CharacterDatabase::class.java,
                    "character_database"
                )
                    .fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}

/**
 * 类型转换器
 */
class Converters {
    @TypeConverter
    fun fromTimestamp(value: Long?): Instant? {
        return value?.let { Instant.ofEpochMilli(it) }
    }

    @TypeConverter
    fun instantToTimestamp(instant: Instant?): Long? {
        return instant?.toEpochMilli()
    }
    
    @TypeConverter
    fun fromGender(value: String): Gender {
        return Gender.valueOf(value)
    }
    
    @TypeConverter
    fun genderToString(gender: Gender): String {
        return gender.name
    }
    
    @TypeConverter
    fun fromGrowthStage(value: String): GrowthStage {
        return GrowthStage.valueOf(value)
    }
    
    @TypeConverter
    fun growthStageToString(stage: GrowthStage): String {
        return stage.name
    }
    
    // TaskType 转换器
    @TypeConverter
    fun fromTaskType(value: String): TaskType {
        return TaskType.valueOf(value)
    }
    
    @TypeConverter
    fun taskTypeToString(type: TaskType): String {
        return type.name
    }
    
    // TaskStatus 转换器
    @TypeConverter
    fun fromTaskStatus(value: String): TaskStatus {
        return TaskStatus.valueOf(value)
    }
    
    @TypeConverter
    fun taskStatusToString(status: TaskStatus): String {
        return status.name
    }
    
    // AssigneeType 转换器
    @TypeConverter
    fun fromAssigneeType(value: String): AssigneeType {
        return AssigneeType.valueOf(value)
    }
    
    @TypeConverter
    fun assigneeTypeToString(type: AssigneeType): String {
        return type.name
    }
}
