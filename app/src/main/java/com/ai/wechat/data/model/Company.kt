package com.ai.wechat.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 公司实体
 */
@Entity(tableName = "companies")
data class Company(
    @PrimaryKey
    val id: String,
    val name: String,
    val founderId: String,
    val money: Double = 0.0,
    val createdAt: Long,
    val updatedAt: Long = System.currentTimeMillis()
)

/**
 * 公司成员关系
 */
@Entity(tableName = "company_members")
data class CompanyMember(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val companyId: String,
    val characterId: String,
    val role: MemberRole,
    val joinedAt: Long,
    val contribution: Double = 0.0
)

/**
 * 成员角色
 */
enum class MemberRole {
    FOUNDER,    // 法人/群主
    CO_FOUNDER, // 联合创始人
    MEMBER      // 普通成员
}
