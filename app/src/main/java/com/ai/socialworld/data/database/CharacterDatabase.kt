package com.ai.socialworld.data.database

import androidx.room.Database
import androidx.room.RoomDatabase
import com.ai.socialworld.data.database.dao.CharacterDao
import com.ai.socialworld.data.model.Character

@Database(
    entities = [Character::class],
    version = 1,
    exportSchema = false
)
abstract class CharacterDatabase : RoomDatabase() {

    abstract fun characterDao(): CharacterDao

    companion object {
        @Volatile
        private var INSTANCE: CharacterDatabase? = null

        fun getDatabase(): CharacterDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = androidx.room.Room.databaseBuilder(
                    androidx.room.Room.getApplicationInstance(),
                    CharacterDatabase::class.java,
                    "character_database"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}

}
