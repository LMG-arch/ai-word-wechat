package com.ai.socialworld.data.model

/**
 * Neo4j 关系类型枚举
 */
enum class Neo4jRelationship {
    HAS_MEMORY,         // 拥有记忆
    REMEMBERS,          // 记得
    FORGETS,            // 遗忘
    CONNECTED_TO,       // 连接到
    LOCATED_AT,         // 位于
    PARTICIPATED_IN,    // 参与
    CREATED,            // 创建
    DESTROYED,          // 毁灭
    KNOWS_ABOUT,        // 知道
    BELIEVES_IN         // 相信
}
