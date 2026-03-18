package com.ai.socialworld.data.model

import java.time.Instant

/**
 * 双时态基类
 * 支持系统时间和业务时间
 */
abstract class TemporalEntity {
    /**
     * 系统创建时间（数据库自动生成）
     */
    var systemCreatedAt: Instant = Instant.now()
        protected set

    /**
     * 系统更新时间（数据库自动生成）
     */
    var systemUpdatedAt: Instant = Instant.now()
        protected set

    /**
     * 业务创建时间（事件发生时间）
     */
    abstract var businessCreatedAt: Instant

    /**
     * 业务失效时间（可选）
     */
    abstract var businessExpiredAt: Instant?

    /**
     * 更新系统时间戳
     */
    fun updateSystemTimestamps() {
        systemUpdatedAt = Instant.now()
    }

    /**
     * 检查是否已过期
     */
    fun isExpired(): Boolean {
        return businessExpiredAt?.let { Instant.now().isAfter(it) } ?: false
    }
}
