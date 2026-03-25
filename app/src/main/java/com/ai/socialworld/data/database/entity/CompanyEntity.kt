package com.ai.socialworld.data.database.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.ai.socialworld.data.database.Converters
import java.time.Instant

/**
 * 公司实体（Room数据库）
 */
@Entity(tableName = "companies")
@TypeConverters(Converters::class)
data class CompanyEntity(
    @PrimaryKey
    val id: String,
    val name: String,
    val founderId: String,
    val money: Int = 0,
    val createdAt: Long = System.currentTimeMillis(),
    val memberIds: String = "", // 逗号分隔的ID列表
    val currentTaskId: String? = null,
    val isDeleted: Boolean = false
)

/**
 * 公司成员实体
 */
@Entity(tableName = "company_members", primaryKeys = ["companyId", "characterId"])
data class CompanyMemberEntity(
    val companyId: String,
    val characterId: String,
    val role: String, // FOUNDER or MEMBER
    val joinedAt: Long = System.currentTimeMillis(),
    val contribution: Int = 0
)
