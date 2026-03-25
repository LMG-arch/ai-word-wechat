package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * 公司实体
 */
@Entity(tableName = "companies")
data class Company(
    @PrimaryKey
    val id: String,
    val name: String,                  // 公司名称
    val founderId: String,             // 创始人ID
    val money: Int = 0,                // 公司资金
    val createdAt: Long = System.currentTimeMillis(),
    val description: String = ""       // 公司描述
)

/**
 * 公司成员
 */
@Entity(
    tableName = "company_members",
    primaryKeys = ["companyId", "characterId"],
    foreignKeys = [
        ForeignKey(
            entity = Company::class,
            parentColumns = ["id"],
            childColumns = ["companyId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index(value = ["companyId"]), Index(value = ["characterId"])]
)
data class CompanyMember(
    val companyId: String,
    val characterId: String,
    val role: String = "MEMBER",        // 角色: FOUNDER, CO_FOUNDER, MEMBER
    val joinedAt: Long = System.currentTimeMillis(),
    val contribution: Int = 0          // 贡献度
)

/**
 * 公司角色
 */
enum class CompanyRole {
    FOUNDER,      // 法人（创始人）
    CO_FOUNDER,   // 联合创始人
    MEMBER        // 普通成员
}

/**
 * 公司知识库条目
 */
@Entity(
    tableName = "company_knowledge",
    foreignKeys = [
        ForeignKey(
            entity = Company::class,
            parentColumns = ["id"],
            childColumns = ["companyId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index(value = ["companyId"])]
)
data class CompanyKnowledge(
    @PrimaryKey
    val id: String,
    val companyId: String,
    val reflectionId: String,          // 关联的反思ID
    val title: String,                 // 标题
    val summary: String,               // 摘要
    val tags: String = "[]",           // 标签 JSON数组
    val referenceCount: Int = 0,       // 引用次数
    val createdAt: Long = System.currentTimeMillis()
)
