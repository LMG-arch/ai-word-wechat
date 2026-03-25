package com.ai.socialworld.util

/**
 * 应用常量定义
 */
object Constants {
    
    // ==================== 数据库相关 ====================
    const val DATABASE_NAME = "ai_social_world.db"
    const val DATABASE_VERSION = 1
    
    // ==================== 经济系统 ====================
    object Economy {
        const val INITIAL_MONEY = 50                    // 初始资金
        const val DAILY_CONSUMPTION = 5                 // 每日消耗
        const val LOAN_AMOUNT = 100                     // 贷款额度
        const val LOAN_INTEREST_RATE = 0.01f            // 日息1%
        const val LOAN_TRIGGER_DAYS = 3                 // 贫困触发天数
        const val MAX_OVERDUE_DAYS = 7                  // 逾期天数
        
        // 奖励范围
        const val MIN_TASK_REWARD = 100
        const val MAX_TASK_REWARD = 10000
        const val MIN_DAILY_TASK_REWARD = 100
        const val MAX_DAILY_TASK_REWARD = 1000
    }
    
    // ==================== 关系系统 ====================
    object Relationship {
        const val STRANGER_THRESHOLD = 20               // 陌生人阈值
        const val ACQUAINTANCE_THRESHOLD = 40            // 认识阈值
        const val FAMILIAR_THRESHOLD = 60                // 熟人阈值
        const val FRIEND_THRESHOLD = 80                  // 好友阈值
        // 81-100: 密友
        
        // 亲密度变化
        const val CHAT_CHANGE_MIN = 1
        const val CHAT_CHANGE_MAX = 3
        const val LIKE_CHANGE = 1
        const val COMMENT_CHANGE = 2
        const val MEET_CHANGE_MIN = 2
        const val MEET_CHANGE_MAX = 5
        const val COOPERATE_CHANGE_MIN = 1
        const val COOPERATE_CHANGE_MAX = 10
        const val CONFLICT_CHANGE_MIN = -15
        const val CONFLICT_CHANGE_MAX = -5
        const val DECAY_AMOUNT = 1
        const val DECAY_THRESHOLD_DAYS = 3
        
        // 关系系数
        const val FIRST_INTERACTION_MULTIPLIER = 1.2f   // 初次互动
        const val CLOSE_FRIEND_MULTIPLIER = 0.8f        // 密友互动
    }
    
    // ==================== 公司系统 ====================
    object Company {
        const val MIN_AGE_TO_CREATE = 18                 // 创建公司最小年龄
        const val MIN_MONEY_TO_CREATE = 200               // 创建公司最小资金
        const val MIN_INTIMACY_FOR_CO_FOUNDER = 60       // 联合创始人亲密度要求
    }
    
    // ==================== 任务系统 ====================
    object Task {
        const val MIN_DAILY_TASKS = 3
        const val MAX_DAILY_TASKS = 5
        const val MAX_REVISION_ROUNDS = 3               // 最多修改次数
        const val VOTE_PARTICIPATION_THRESHOLD = 0.5f    // 投票参与率阈值
        const val VOTE_APPROVAL_THRESHOLD = 0.6f         // 投票赞成率阈值
    }
    
    // ==================== 记忆系统 ====================
    object Memory {
        const val HALF_LIFE_HOURS = 72.0                 // 半衰期（小时）
        const val REFLECTION_HALF_LIFE_HOURS = 168.0     // 反思记忆半衰期（7天）
        const val TOP_K_RETRIEVAL = 10                   // 召回记忆数量
        const val MAX_CANDIDATES = 50                    // 最大候选数量
    }
    
    // ==================== 日程系统 ====================
    object Schedule {
        // 权重
        const val OCCUPATION_WEIGHT = 0.4f
        const val PERSONALITY_WEIGHT = 0.3f
        const val RELATIONSHIP_WEIGHT = 0.2f
        const val ECONOMY_WEIGHT = 0.1f
        
        // 时间段
        const val MORNING_START = 6
        const val WORK_START = 9
        const val LUNCH_START = 12
        const val AFTERNOON_START = 14
        const val EVENING_START = 18
        const val NIGHT_START = 21
    }
    
    // ==================== 地图系统 ====================
    object Map {
        const val ENCOUNTER_RADIUS = 50.0                 // 相遇半径（米）
        const val ENCOUNTER_MIN_DURATION = 5 * 60 * 1000L // 5分钟（毫秒）
        const val WORLD_SIZE = 1000.0                    // 世界大小（米）
    }
    
    // ==================== 世界时间 ====================
    object WorldTime {
        const val MIN_MULTIPLIER = 1
        const val MAX_MULTIPLIER = 30
        const val DAY_IN_MILLIS = 24 * 60 * 60 * 1000L
    }
    
    // ==================== 角色自主更新 ====================
    object Autonomy {
        const val MAX_AVATAR_CHANGES_PER_WEEK = 2
        const val MAX_SIGNATURE_CHANGES_PER_WEEK = 2
        const val WEEK_IN_MILLIS = 7 * 24 * 60 * 60 * 1000L
    }
    
    // ==================== 成长阶段 ====================
    object Growth {
        const val CHILD_MAX_AGE = 12
        const val TEENAGER_MAX_AGE = 17
        const val YOUNG_ADULT_MAX_AGE = 40
        const val MIDDLE_AGED_MAX_AGE = 60
        // 61+ : ELDERLY
    }
    
    // ==================== AI服务 ====================
    object AI {
        const val MAX_RETRIES = 2                         // 最大重试次数
        const val SWITCH_THRESHOLD = 3                    // 切换备用API阈值
        const val CONNECT_TIMEOUT = 5L                    // 连接超时（秒）
        const val READ_TIMEOUT = 30L                      // 读取超时（秒）
        const val MAX_CONCURRENT_REQUESTS = 3             // 最大并发请求数
    }
    
    // ==================== UI相关 ====================
    object UI {
        const val WECHAT_GREEN = 0xFF07C160
        const val MAX_LOG_ENTRIES = 200
        const val PAGE_SIZE = 20
    }
}
