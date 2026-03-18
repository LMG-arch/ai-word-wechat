---
title: DeepSeek
source: https://chat.deepseek.com/a/chat/s/8f6dcab8-be6f-4bba-acfc-7f95fd1b1010
author:
published:
created: 2026-03-18
description: Chat with DeepSeek AI – your intelligent assistant for coding, content creation, file reading, and more. Upload documents, engage in long-context conversations, and get expert help in AI, natural language processing, and beyond. | 深度求索（DeepSeek）助力编程代码开发、创意写作、文件处理等任务，支持文件上传及长文本对话，随时为您提供高效的AI支持。
tags:
  - clippings
last-modified:
  - 2026-03-18T10:16:30
---
润色AI社交应用需求

## AI社交世界 - 完整应用开发指令

### 一、项目概述

**项目名称** ：AI社交世界（仿微信界面）  
**平台** ：Android  
**核心定位** ：一个由AI角色自主运行的虚拟社交世界，用户作为观察者见证角色的生活、社交、成长、工作，形成完整的经济社会生态系统。所有角色拥有时间感知的独立记忆，能够从经验中学习进化。

---

### 二、技术架构总览

#### 2.1 整体架构图

text

```
┌─────────────────────────────────────────────────────────────┐
│                       表现层 (UI)                            │
│  ┌──────┬──────┬──────┬──────┬──────┬──────┐               │
│  │聊天  │通讯录│群聊  │任务  │发现  │我    │               │
│  └──────┴──────┴──────┴──────┴──────┴──────┘               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       业务逻辑层                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │角色管理系统│ │  关系引擎  │ │  日程引擎  │              │
│  ├────────────┤ ├────────────┤ ├────────────┤              │
│  │  经济系统  │ │  任务系统  │ │  反思引擎  │              │
│  ├────────────┤ ├────────────┤ ├────────────┤              │
│  │  公司系统  │ │  地图系统  │ │  通知系统  │              │
│  └────────────┘ └────────────┘ └────────────┘              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       数据层                                 │
│  ┌────────────────────┐ ┌────────────────────┐             │
│  │   Neo4j图数据库    │ │    SQLite数据库     │             │
│  │ (Graphiti记忆引擎)  │ │  (系统配置/缓存)    │             │
│  └────────────────────┘ └────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       AI服务层                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │语言模型  │ │图像模型  │ │向量模型  │ │重排模型  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

#### 2.2 技术选型

| 层级 | 技术选型 | 说明 |
| --- | --- | --- |
| **UI框架** | Jetpack Compose | 现代声明式UI，开发效率高 |
| **数据库** | Neo4j + Graphiti | 时间感知图数据库，存储所有记忆和关系 |
| **本地缓存** | Room SQLite | 存储配置、临时数据 |
| **网络层** | Retrofit + OkHttp | AI API调用 |
| **异步** | Kotlin Coroutines + Flow | 响应式编程 |
| **依赖注入** | Dagger Hilt | 模块解耦 |
| **图片加载** | Coil | Compose原生支持 |
| **图表** | MPAndroidChart | 技能可视化 |

---

### 三、数据库设计（Graphiti + Neo4j）

#### 3.1 节点类型

| 节点标签 | 属性 | 说明 |
| --- | --- | --- |
| **Character** | id, name, age, gender, occupation, personality, money, createdAt | 角色 |
| **Company** | id, name, founderId, money, createdAt | 公司 |
| **Task** | id, title, description, type, reward, status, requirements | 任务 |
| **Location** | id, name, type, latitude, longitude | 地图位置 |
| **Reflection** | id, content, lessons, skillDeltas | 反思报告 |

#### 3.2 关系类型（带时间属性）

| 关系类型 | 起始节点 | 目标节点 | 关键属性 | 说明 |
| --- | --- | --- | --- | --- |
| **FRIEND\_WITH** | Character | Character | intimacy, valid\_from, valid\_to | 好友关系（带有效期） |
| **WORK\_AT** | Character | Company | role, joinedAt, leftAt | 工作关系 |
| **POSTED** | Character | Task | submittedAt, approvedAt | 任务提交 |
| **LOCATED\_AT** | Character | Location | arrivedAt, leftAt | 位置历史 |
| **HAS\_MEMORY** | Character | Reflection | recalledAt, importance | 反思记忆 |
| **PARTICIPATED\_IN** | Character | Task | contribution | 任务参与 |

#### 3.3 Graphiti时间模型应用

cypher

```
// 示例：存储角色A和角色B的好友关系（带时间区间）CREATE (a:Character {id: 'A', name: '小王'})
CREATE (b:Character {id: 'B', name: '小李'})
CREATE (a)-[r:FRIEND_WITH {
    intimacy: 85,
    valid_from: datetime('2026-03-01T00:00:00'),
    valid_to: null  // null表示当前有效
}]->(b)
}]->(b)
// 关系破裂后，更新valid_to
MATCH (a {id: 'A'})-[r:FRIEND_WITH]->(b {id: 'B'})
SET r.valid_to = datetime('2026-03-15T14:30:00')
SET r.valid_to = datetime('2026-03-15T14:30:00')
// 查询2026-03-10时的好友关系
MATCH (a {id: 'A'})-[r:FRIEND_WITH]->(b)
WHERE r.valid_from <= datetime('2026-03-10T00:00:00')
  AND (r.valid_to IS NULL OR r.valid_to > datetime('2026-03-10T00:00:00'))
RETURN b, r.intimacy
RETURN b, r.intimacy
```

---

### 四、核心模块详细设计

#### 4.1 角色管理系统

**类设计** ：

kotlin

```
class CharacterManager(    private val memoryEngine: GraphitiEngine,
    private val apiService: AIService
) {
    // 创建角色
    suspend fun createCharacter(request: CreateCharacterRequest): Character
    suspend fun createCharacter(request: CreateCharacterRequest): Character
    // 年龄增长检测（每日定时任务）
    suspend fun checkAgeGrowth()
    suspend fun checkAgeGrowth()
    // 自主头像更新
    suspend fun maybeUpdateAvatar(characterId: String)
    suspend fun maybeUpdateAvatar(characterId: String)
    // 自主签名更新
    suspend fun maybeUpdateSignature(characterId: String)
    suspend fun maybeUpdateSignature(characterId: String)
    // 破产检测
    suspend fun checkBankruptcy(characterId: String)
    suspend fun checkBankruptcy(characterId: String)
    // 死亡检测
    suspend fun checkDeath(characterId: String)
}
}
```

**核心逻辑** ：

- 年龄 = 创建时间 + (世界时间流速 × 流逝天数)
- 年龄段跨越触发事件和头像强制更新
- 每日资金消耗5，归零触发贷款

#### 4.2 Graphiti记忆引擎封装

kotlin

```
interface MemoryEngine {    // 存储记忆（自动带时间戳）
    suspend fun storeMemory(
        characterId: String,
        content: String,
        type: MemoryType,
        importance: Float,
        relatedEntities: List<String> = emptyList(),
        metadata: Map<String, Any> = emptyMap()
    )
    )
    // 带时间感知的检索
    suspend fun recallMemories(
        characterId: String,
        query: String,
        timeRange: TimeRange? = null,  // 时间范围过滤
        topK: Int = 10
    ): List<Memory>
    ): List<Memory>
    // 存储关系（带有效期）
    suspend fun storeRelationship(
        fromId: String,
        toId: String,
        type: RelationshipType,
        properties: Map<String, Any>,
        validFrom: Instant,
        validTo: Instant? = null
    )
    )
    // 查询历史状态
    suspend fun getStateAtTime(
        characterId: String,
        timestamp: Instant
    ): CharacterState
}
}
class GraphitiMemoryEngine(
    private val neo4jDriver: Driver,
    private val vectorService: VectorService,
    private val rerankService: RerankService
) : MemoryEngine {
    // 实现上述接口
}
}
```

#### 4.3 记忆召回流程

kotlin

```
suspend fun generateResponse(    characterId: String,
    userInput: String
): String {
    // 1. 向量检索Top 50
    val queryEmbedding = vectorService.embed(userInput)
    val candidates = memoryEngine.searchVector(
        characterId, queryEmbedding, 50
    )
    )
    // 2. 时间加权（近期记忆权重高）
    val timeWeighted = candidates.map {
        it to timeDecay(it.timestamp)
    }.sortedByDescending { it.second }
    }.sortedByDescending { it.second }
    // 3. 重排模型精排Top 10
    val reranked = rerankService.rerank(
        query = userInput,
        candidates = timeWeighted.take(20).map { it.first.content },
        topK = 10
    )
    )
    // 4. 构建上下文
    val context = buildContext(characterId, reranked)
    val context = buildContext(characterId, reranked)
    // 5. 调用语言模型
    val response = llmService.chat(context)
    val response = llmService.chat(context)
    // 6. 存储本次对话
    memoryEngine.storeMemory(
        characterId = characterId,
        content = "用户: $userInput\n角色: $response"
,
        type = MemoryType.CONVERSATION,
        importance = 0.6
    )
    )
    return response
}
}
// 时间衰减函数（指数衰减）
private fun timeDecay(timestamp: Long): Double {
    val hoursDiff = (System.currentTimeMillis() - timestamp) / (1000 * 60 * 60)
    return Math.exp(-hoursDiff / 72.0)  // 半衰期约2.5天
}
}
```

#### 4.4 反思引擎

kotlin

```
class ReflectionEngine(    private val memoryEngine: MemoryEngine,
    private val llmService: LLMService
) {
    // 任务完成后触发反思
    suspend fun reflectOnTask(
        characterId: String,
        task: Task,
        executionLog: ExecutionLog
    ) {
        // 1. 构建反思提示词
        val prompt = buildReflectionPrompt(task, executionLog)
        val prompt = buildReflectionPrompt(task, executionLog)
        // 2. 调用LLM生成反思报告
        val reflection = llmService.generateReflection(prompt)
        val reflection = llmService.generateReflection(prompt)
        // 3. 解析为结构化数据
        val structured = parseReflection(reflection)
        val structured = parseReflection(reflection)
        // 4. 存储反思记忆（带时间戳）
        memoryEngine.storeMemory(
            characterId = characterId,
            content = structured.summary,
            type = MemoryType.REFLECTION,
            importance = if (task.success) 0.7 else 0.9,  // 失败教训更重要
            relatedEntities = listOf(task.id),
            metadata = mapOf(
                "lessons"
 to structured.lessons,
                "skillDeltas"
 to structured.skillDeltas
            )
        )
        )
        // 5. 更新角色技能
        updateSkills(characterId, structured.skillDeltas)
        updateSkills(characterId, structured.skillDeltas)
        // 6. 如果是公司任务，加入知识库
        if (task.assigneeType == AssigneeType.COMPANY) {
            addToCompanyKnowledge(task.companyId, structured)
        }
    }
    }
    // 技能更新公式
    private fun calculateSkillDelta(
        taskType: String,
        success: Boolean,
        lessonCount: Int
    ): Map<SkillType, Float> {
        val baseDelta = if (success) 1..5 else 2..8
        val multiplier = minOf(1.0, 5.0 / lessonCount)  // 同类任务递减
        val multiplier = minOf(1.0, 5.0 / lessonCount)  // 同类任务递减
        return mapOf(
            SkillType.REQUIREMENT_UNDERSTANDING to baseDelta * 0.3,
            SkillType.EPIC_SENSE to baseDelta * 0.4,
            // ...
        )
    }
}
}
```

#### 4.5 关系引擎

kotlin

```
class RelationshipEngine(    private val memoryEngine: GraphitiMemoryEngine
) {
    // 亲密计算规则
    suspend fun updateIntimacy(
        fromId: String,
        toId: String,
        action: InteractionAction
    ) {
        val currentRel = memoryEngine.getCurrentRelationship(fromId, toId)
        val currentRel = memoryEngine.getCurrentRelationship(fromId, toId)
        // 计算变化值
        val delta = when (action) {
            InteractionAction.CHAT -> (1..3).random()
            InteractionAction.LIKE -> 1
            InteractionAction.COMMENT -> 2
            InteractionAction.MEET -> (2..5).random()
            InteractionAction.COLLABORATE -> (1..10).random()
            InteractionAction.CONFLICT -> -(5..15).random()
        }
        }
        // 关系系数调节
        val coefficient = when (currentRel.intimacy) {
            in 0..20 -> 1.2  // 陌生人加成
            in 81..100 -> 0.8 // 密友边际递减
            else -> 1.0
        }
        }
        val newIntimacy = (currentRel.intimacy + delta * coefficient)
            .coerceIn(0, 100)
            .coerceIn(0, 100)
        // 更新关系（带时间戳）
        memoryEngine.storeRelationship(
            fromId = fromId,
            toId = toId,
            type = RelationshipType.FRIEND_WITH,
            properties = mapOf("intimacy"
 to newIntimacy),
            validFrom = currentRel.validFrom,
            validTo = if (newIntimacy < 20) Instant.now() else null
        )
        )
        // 阈值检测
        checkThresholdCrossing(fromId, toId, currentRel.intimacy, newIntimacy)
    }
    }
    // 每日衰减任务
    suspend fun dailyDecay() {
        // 找出所有超过3天未互动的亲密关系
        val staleRelations = memoryEngine.getStaleRelationships(3)
        val staleRelations = memoryEngine.getStaleRelationships(3)
        staleRelations.forEach { rel ->
            val newIntimacy = (rel.intimacy - 1).coerceAtLeast(0)
            val newIntimacy = (rel.intimacy - 1).coerceAtLeast(0)
            memoryEngine.storeRelationship(
                fromId = rel.fromId,
                toId = rel.toId,
                type = RelationshipType.FRIEND_WITH,
                properties = mapOf("intimacy"
 to newIntimacy),
                validFrom = rel.validFrom,
                validTo = if (newIntimacy < 20) Instant.now() else null
            )
        }
    }
    }
    // 阈值检测：20认识/40熟人/60好友/80密友
    private suspend fun checkThresholdCrossing(
        fromId: String, toId: String,
        oldValue: Int, newValue: Int
    ) {
        val oldLevel = getLevel(oldValue)
        val newLevel = getLevel(newValue)
        val newLevel = getLevel(newValue)
        if (oldLevel != newLevel) {
            when (newLevel) {
                1 -> onBecomeAcquainted(fromId, toId)  // 突破20：创建私人群聊
                4 -> onBecomeBestFriends(fromId, toId)
            }
        }
        }
        if (newValue < 20 && oldValue >= 20) {
            onRelationshipBroken(fromId, toId)  // 跌破20：可能删除好友
        }
    }
}
}
```

#### 4.6 任务系统

kotlin

```
class TaskSystem(    private val memoryEngine: MemoryEngine,
    private val reflectionEngine: ReflectionEngine,
    private val economyService: EconomyService
) {
    // 个人任务流程
    suspend fun executePersonalTask(
        taskId: String,
        characterId: String
    ) {
        val task = getTask(taskId)
        val task = getTask(taskId)
        // 1. 标记任务进行中
        updateTaskStatus(taskId, TaskStatus.IN_PROGRESS, characterId)
        updateTaskStatus(taskId, TaskStatus.IN_PROGRESS, characterId)
        // 2. 生成成果
        val result = when (task.type) {
            TaskType.IMAGE -> generateImage(task)
            TaskType.TEXT -> generateText(task)
            TaskType.CODE -> generateCode(task)
        }
        }
        // 3. 提交用户审核
        val approved = waitForUserApproval(taskId, result)
        val approved = waitForUserApproval(taskId, result)
        if (approved) {
            // 4. 发放奖励
            economyService.transferMoney(
                from = "SYSTEM"
,
                to = characterId,
                amount = task.reward
            )
            )
            // 5. 触发反思
            reflectionEngine.reflectOnTask(
                characterId, task, buildExecutionLog(task, result)
            )
            )
            updateTaskStatus(taskId, TaskStatus.COMPLETED)
        } else {
            updateTaskStatus(taskId, TaskStatus.FAILED)
        }
    }
    }
    // 公司任务流程
    suspend fun executeCompanyTask(
        taskId: String,
        companyId: String
    ) {
        val task = getTask(taskId)
        val company = getCompany(companyId)
        val company = getCompany(companyId)
        // 1. 指派执行人
        val executor = selectExecutor(company, task)
        val executor = selectExecutor(company, task)
        // 2. 执行人提交初稿
        var currentVersion = generateInitialVersion(executor, task)
        var currentVersion = generateInitialVersion(executor, task)
        // 3. 审核循环（最多3轮）
        for (round in 1..3) {
            val votes = collectVotes(company, currentVersion)
            val votes = collectVotes(company, currentVersion)
            if (votes.approved) {
                break
            } else {
                currentVersion = reviseVersion(executor, task, votes.feedback)
            }
        }
        }
        // 4. 法人提交用户
        val approved = waitForUserApproval(taskId, currentVersion)
        val approved = waitForUserApproval(taskId, currentVersion)
        if (approved) {
            // 5. 发放奖励到公司
            economyService.transferMoney(
                from = "SYSTEM"
,
                to = companyId,
                amount = task.reward
            )
            )
            // 6. 法人分配奖金
            distributeRewards(company, task, votes.contributions)
            distributeRewards(company, task, votes.contributions)
            // 7. 全员反思（执行人深度反思）
            launch {
                reflectionEngine.reflectOnTask(
                    executor.id, task, buildExecutionLog(task, currentVersion)
                )
                )
                // 其他成员可补充反思
                company.members.filter { it.id != executor.id }.forEach { member ->
                    reflectionEngine.optionalReflect(member.id, task)
                }
            }
        }
    }
}
}
```

#### 4.7 日程引擎

kotlin

```
class ScheduleEngine(    private val memoryEngine: MemoryEngine
) {
    // 每日0点生成次日日程
    suspend fun generateDailySchedules() {
        val characters = getAllCharacters()
        val characters = getAllCharacters()
        characters.forEach { character ->
            val schedule = generateSchedule(character)
            val schedule = generateSchedule(character)
            // 存储日程作为记忆
            memoryEngine.storeMemory(
                characterId = character.id,
                content = "今日日程: ${schedule.summary}"
,
                type = MemoryType.SCHEDULE,
                importance = 0.5,
                metadata = mapOf(
                    "schedule"
 to schedule.toJson()
                )
            )
            )
            // 设置位置更新
            schedule.events.forEach { event ->
                scheduleLocationUpdate(character.id, event.location, event.startTime)
            }
        }
    }
    }
    private fun generateSchedule(character: Character): DailySchedule {
        val events = mutableListOf<ScheduleEvent>()
        val events = mutableListOf<ScheduleEvent>()
        // 权重计算
        val weights = mapOf(
            "职业"
 to 0.4,
            "性格"
 to 0.3,
            "关系"
 to 0.2,
            "经济"
 to 0.1
        )
        )
        // 职业相关活动
        when (character.occupation) {
            "程序员"
 -> events.add(
                ScheduleEvent("09:00"
, "12:00"
, "办公室"
, "编码"
)
            )
            "咖啡师"
 -> events.add(
                ScheduleEvent("07:00"
, "15:00"
, "咖啡馆"
, "工作"
)
            )
            // ...
        }
        }
        // 性格调整
        if (character.personality.contains("社恐"
)) {
            events.removeAll { it.location == "酒吧"
 }
        }
        }
        // 关系约会
        val friends = memoryEngine.getCloseFriends(character.id, intimacy = 60)
        if (friends.isNotEmpty() && Random.nextFloat() < 0.3) {
            val friend = friends.random()
            events.add(
                ScheduleEvent("18:00"
, "20:00"
, "餐厅"
, "与${friend.name}吃饭"
),
                relatedEntity = friend.id
            )
        }
        }
        // 经济影响
        if (character.money < 20) {
            events.add(
                ScheduleEvent("14:00"
, "16:00"
, "兼职地点"
, "找兼职"
)
            )
        }
        }
        return DailySchedule(events)
    }
}
}
```

---

### 五、UI模块设计（Jetpack Compose）

#### 5.1 导航结构

#### 5.2 角色详情页

#### 5.3 任务详情页

安卓应用需求规格说明书：AI社交世界（仿微信界面） 一、产品概述 这是一款基于Android平台的社交模拟应用，采用微信风格的UI设计，核心玩法是创建一个由AI角色自主运行的虚拟世界。用户既是观察者，也是参与者，可以添加自定义AI角色，见证他们像真人一样生活、社交、成长、工作，形成一个完整的经济社会生态系统。 --- 二、核心功能模块详解 1. AI角色管理系统 1.1 角色创建与配置 · 自定义创建：用户可通过“添加好友”入口创建新角色，配置项包括： · 基础信息：昵称、性别、年龄（可设定初始年龄段：儿童/青年/中年/老年）、职业（手动输入或AI推荐） · 性格设定：支持手动输入人设描述（如“毒舌程序员”“温柔咖啡师”），或由AI根据关键词自动生成 · 声音设定：可选用系统语音包或上传自定义语音 · 智能头像生成： · 创建角色时，系统自动调用已配置的绘图模型，根据人设描述生成初始头像 · 生成逻辑：结合年龄、性别、职业、性格特征，生成风格匹配的肖像（如儿童头像带稚气，老人有皱纹） · 支持多次生成供用户选择（最多3次） 1.2 角色生命周期与成长系统 · 时间流逝机制： · 以现实时间为基础，可设置时间倍速（1倍速=现实时间，最高可设30倍速） · 角色年龄随世界时间自动增长（例：30倍速下，现实1天=角色增长1个月） · 成长阶段划分： · 儿童期（0-12岁）：主要活动为学习、玩耍，无法工作，依赖父母角色（若有）提供资金 · 青少年期（13-17岁）：可兼职、学习技能，开始形成独立人格 · 青年期（18-40岁）：可全职工作、创业、组建家庭 · 中年期（41-60岁）：经验丰富，适合管理岗位、创业 · 老年期（61岁以上）：可退休、传授经验，部分角色可能死亡（可选设置） 2. 记忆系统与向量检索 2.1 记忆存储架构 · 本地化存储： · 每个角色拥有独立的SQLite数据库，存储所有记忆 · 记忆分类：对话记忆、事件记忆、关系记忆、任务记忆、日程记忆、反思记忆 · 加密存储敏感信息 · 记忆结构： \`\`\`json { "memory\_id": "唯一ID", "timestamp": "2024-01-01 10:30:00", "type": "对话|事件|任务|关系变化|反思", "content": "记忆内容文本", "importance": 0.8, // 重要性评分（0-1），影响召回优先级 "emotion": "开心|难过|愤怒等", "related\_entities": \["角色A", "公司B", "任务C"\], // 相关实体 "embedding": "向量数据（Base64编码）", // 用于相似度检索 "reflection\_of": "任务ID", // 如果是反思记忆，关联原任务 "lessons\_learned": \["错误1", "改进点2"\] // 反思总结的经验教训 } \`\`\` 3. 任务系统与反思机制 3.1 任务系统概述 · 任务接取主体： · 个人接取：任何角色可独立接取任务，完成后奖励全额归个人 · 公司接取：公司统一接取，成员协作完成，奖励按贡献分配 · 任务类型： · 文本生成：撰写文章、故事、报告等 · 图像生成：绘制图片（要求史诗感、非二次元） · 代码编写：开发小程序、脚本等 · 调研分析：输出调研报告 · 创意设计：LOGO设计、海报制作等 3.2 任务完成后的反思机制 3.2.1 反思触发时机 · 任务成功完成时：无论个人还是公司任务，完成后自动触发反思 · 任务失败时：同样触发反思，重点分析失败原因 · 审核不通过时：每次修改意见返回时记录问题，任务完成后综合反思 3.2.2 反思流程 \`\`\` 任务完成/失败 → 收集过程数据 → AI生成反思报告 → 提取经验教训 → 存储为反思记忆 → 更新技能库 → 影响未来行为 \`\`\` 3.2.3 反思内容生成 · 输入数据： · 任务原始需求 · 执行过程中的所有修改记录 · 审核意见（公司任务）或用户反馈（个人任务） · 投票记录（哪些人反对，原因） · 时间线（每个阶段耗时） · 反思报告结构： \`\`\`json { "task\_id": "任务ID", "task\_name": "绘制玄幻风景图", "completion\_time": "2024-01-01 15:30:00", "success": true/false, "what\_went\_well": \[ "色彩搭配得到认可", "构图宏大符合要求" \], "what\_went\_wrong": \[ "第一次提交时细节不够丰富", "第二次提交时风格偏二次元被驳回" \], "root\_causes": \[ "对'史诗感'理解不够深入", "没有仔细阅读'禁止二次元'的要求" \], "lessons\_learned": \[ "每次提交前要对照需求清单逐项检查", "史诗感需要宏大构图+丰富细节+光影强烈", "避免使用动漫风格的线条和上色" \], "action\_items": \[ "下次绘图前先找3张史诗感参考图", "建立'禁止风格'自查清单" \], "skill\_improvements": { "史诗感理解": "+15%", "需求理解准确性": "+10%" } } \`\`\` 3.2.4 反思记忆存储 · 反思报告转化为结构化的反思记忆，存入角色记忆库 · 重要性初始值：成功任务0.7，失败任务0.9（教训更深刻） · 关联原任务ID，便于追溯 3.3 经验教训的应用 3.3.1 对话中的应用 · 当遇到类似任务或问题时，反思记忆被召回 · 角色会说：“上次我画玄幻图时犯过风格错误，这次我会注意避免二次元风格” 3.3.2 任务执行中的应用 · 执行前：系统自动检索相关反思记忆，生成“注意事项”提示 · 示例：“根据您上次绘制玄幻图的经验，请注意：1.避免二次元风格 2.确保光影强烈” · 执行中：反思记忆作为上下文注入，指导生成过程 · 图像生成时，负面提示词自动加入从反思中学到的内容 · 审核时：角色会用过往教训审视当前成果 3.3.3 技能系统 · 每个角色维护一个隐式的技能树，基于完成任务和反思更新 · 技能维度示例： · 需求理解能力 · 史诗感把控 · 细节丰富度 · 风格准确性 · 修改效率 · 每次反思更新对应技能值（成功+1~5，失败+2~8，视反思深度） 3.4 反思记忆的召回优化 3.4.1 向量检索增强 · 反思记忆的向量生成时，加入任务类型、错误类型等标签 · 检索时，当前任务描述与反思记忆的相似度计算 3.4.2 重排加权 · 重排模型对反思记忆给予更高权重 · 同类任务的反思记忆优先级提升 3.4.3 时效性考虑 · 近期反思（7天内）权重更高 · 长期未用的反思重要性逐渐衰减（但失败教训衰减慢） 3.5 公司层面的反思共享 3.5.1 公司知识库 · 公司成员完成任务后，反思报告自动加入公司知识库（匿名或署名） · 知识库对所有成员可见 3.5.2 经验分享机制 · 重要反思（重要性≥0.8）自动在公司群聊分享 · 示例：“小王在绘制玄幻图任务中学到了：史诗感需要宏大构图+丰富细节，已加入公司知识库” · 成员可对反思点赞、评论（增强亲密度） 3.5.3 新成员培训 · 新加入公司的角色，自动推送公司知识库中的高频反思 · 帮助新人快速学习 3.6 任务失败的特殊反思 3.6.1 失败原因分类 · 需求理解偏差 · 技术能力不足 · 时间管理不当 · 团队协作问题 · 审核标准误判 3.6.2 失败反思的强化 · 失败任务的反思重要性更高（初始0.9） · 强制在下次类似任务前提醒 · 可能触发角色自我怀疑等情绪剧情 3.6.3 改进计划 · 失败反思自动生成改进计划 · 计划加入角色日程（如“学习史诗感构图技巧”） · 完成学习后产生新的记忆 4. 任务管理器（增强版） 4.1 任务详情页新增 · 反思报告：完成任务后显示反思报告入口 · 经验教训：摘要展示主要教训 · 技能提升：显示本次任务带来的技能变化 4.2 角色详情页新增 · 技能面板：可视化展示角色各项能力 · 反思历史：最近5条反思记忆（点击展开） · 成长轨迹：技能随时间变化曲线 4.3 公司详情页新增 · 知识库入口：查看所有成员贡献的反思 · 热门教训：被引用最多的反思 · 团队成长：公司整体技能平均值变化 5. 仿微信界面交互系统（保持不变） --- 三、技术实现要点 1. 反思引擎实现 \`\`\`kotlin data class ReflectionInput( val taskId: String, val taskType: String, val requirements: String, val submissions: List<Submission>, // 每次提交的版本 val feedbacks: List<Feedback>, // 审核意见/用户反馈 val votes: List<Vote>?, // 公司投票记录 val finalResult: Any, // 最终成果 val success: Boolean, val duration: Long // 耗时(分钟) ) suspend fun generateReflection(input: ReflectionInput): Reflection { // 构建反思提示词 val prompt = buildReflectionPrompt(input) // 调用语言模型生成反思报告 val reflection = callLanguageModel(prompt) // 结构化解析 val structured = parseReflection(reflection) // 计算技能变化 val skillDeltas = calculateSkillDeltas(input, structured) // 存储反思记忆 saveReflectionMemory(structured, skillDeltas) // 更新角色技能 updateSkills(skillDeltas) // 如果是公司任务，加入知识库 if (input.isCompanyTask) { addToCompanyKnowledgeBase(structured) } return structured } \`\`\` 2. 技能系统实现 \`\`\`kotlin // 技能定义 enum class SkillType { REQUIREMENT\_UNDERSTANDING, // 需求理解 EPIC\_SENSE, // 史诗感把控 DETAIL\_RICHNESS, // 细节丰富度 STYLE\_ACCURACY, // 风格准确性 REVISION\_EFFICIENCY, // 修改效率 TEAM\_COLLABORATION // 团队协作 } // 角色技能 data class Skills( val values: Map<SkillType, Float>, // 0-100 val history: List<SkillSnapshot> // 历史记录 ) // 技能更新 fun updateSkills(reflection: Reflection, deltas: Map<SkillType, Float>) { deltas.forEach { (skill, delta) -> val newValue = (currentSkills\[skill\] + delta).coerceIn(0f, 100f) currentSkills\[skill\] = newValue // 记录变化 recordSkillChange(skill, newValue, reflection.taskId) } } \`\`\` 3. 反思记忆召回优化 \`\`\`kotlin suspend fun retrieveRelevantReflections( taskDescription: String, taskType: String, topK: Int = 5 ): List<Reflection> { // 向量检索 val queryEmbedding = generateEmbedding(taskDescription) val similarByVector = vectorSearch(queryEmbedding, type = "反思", topK = topK \* 2) // 类型过滤 val sameType = similarByVector.filter { it.taskType == taskType } // 重排加权 val reranked = rerankReflections(taskDescription, sameType) // 时效性调整 val withTimeWeight = applyTimeDecay(reranked) return withTimeWeight.take(topK) } \`\`\` 4. 反思模板示例 成功任务反思提示词： \`\`\` 你刚刚成功完成了一个任务，请进行深度反思。 任务信息： - 类型：{任务类型} - 需求：{需求描述} - 执行过程：{提交记录和反馈} - 最终成果：{成果描述} 请从以下维度反思： 1. 哪些做法是正确的？（至少2点） 2. 过程中遇到了什么困难？如何克服的？ 3. 如果有机会重做，哪些地方可以做得更好？ 4. 总结3条最重要的经验教训 5. 这些经验可以用在哪些类型的未来任务中？ 请用结构化JSON格式返回。 \`\`\` 失败任务反思提示词（增加）： \`\`\` 任务失败了，请深入分析原因。 失败信息： - 失败阶段：{哪个环节失败的} - 失败表现：{具体表现} - 收到的反馈：{审核意见/用户反馈} 请重点分析： 1. 失败的根本原因是什么？（不要停留在表面） 2. 如果早点发现，可以在哪个环节纠正？ 3. 为了避免再次失败，需要建立什么检查机制？ 4. 这次失败教会了你什么？（至少3条深刻教训） \`\`\` 5. 数据库设计补充 \`\`\`sql -- 反思记忆表 CREATE TABLE reflection\_memories ( id TEXT PRIMARY KEY, task\_id TEXT NOT NULL, character\_id TEXT NOT NULL, success BOOLEAN, what\_went\_well TEXT, -- JSON数组 what\_went\_wrong TEXT, -- JSON数组 root\_causes TEXT, -- JSON数组 lessons\_learned TEXT, -- JSON数组 action\_items TEXT, -- JSON数组 importance FLOAT, created\_at TIMESTAMP, FOREIGN KEY(task\_id) REFERENCES tasks(id), FOREIGN KEY(character\_id) REFERENCES characters(id) ); -- 技能表 CREATE TABLE skills ( character\_id TEXT, skill\_type TEXT, value FLOAT, updated\_at TIMESTAMP, PRIMARY KEY(character\_id, skill\_type) ); -- 技能历史表 CREATE TABLE skill\_history ( id TEXT PRIMARY KEY, character\_id TEXT, skill\_type TEXT, old\_value FLOAT, new\_value FLOAT, task\_id TEXT, changed\_at TIMESTAMP, FOREIGN KEY(character\_id) REFERENCES characters(id), FOREIGN KEY(task\_id) REFERENCES tasks(id) ); -- 公司知识库表 CREATE TABLE company\_knowledge ( id TEXT PRIMARY KEY, company\_id TEXT, reflection\_id TEXT, title TEXT, summary TEXT, tags TEXT, -- JSON数组 reference\_count INTEGER DEFAULT 0, created\_at TIMESTAMP, FOREIGN KEY(company\_id) REFERENCES companies(id), FOREIGN KEY(reflection\_id) REFERENCES reflection\_memories(id) ); \`\`\` 6. 反思触发时机优化 · 即时反思：任务完成后立即触发（保证记忆新鲜） · 延迟反思：对于复杂任务，可设置1小时后二次反思（冷静期） · 周期性复盘：每周对本周所有任务进行综合反思，提炼通用原则 --- 四、用户体验特色 1. 持续进化：角色会从错误中学习，越做越好，真实感倍增 2. 经验可视化：用户可以直观看到角色技能的成长曲线 3. 教训共享：公司知识库让团队整体进步，新成员快速上手 4. 深度沉浸：角色会引用过往教训对话，让世界更真实 5. 成就感：看到自己创建的角色通过反思不断进步 6. 策略深度：用户可以引导角色重点反思某些方面 --- 五、版本规划建议 V1.0 基础版 · 仿微信UI框架 · 单角色对话，基础API配置 V2.0 社交版 · 多角色自主交互 · 亲密度系统 · 朋友圈权限控制 V3.0 记忆版 · 独立记忆库 · 向量模型配置 · 重排模型配置 · 私人群聊独立Tab V4.0 经济版 · 资金系统 · 日常消耗 · 个人任务系统 · 公司任务系统 · 史诗感图像生成 · 任务反思机制 · 技能系统 V5.0 生态版 · 公司创建与群聊 · 公司知识库 · 世界银行贷款 · 角色生命周期 · 备用模型切换 更新这个指令，先不要写代码

## 安卓应用需求规格说明书：AI社交世界（仿微信界面）

### 一、产品概述

这是一款基于Android平台的社交模拟应用，采用微信风格的UI设计，核心玩法是创建一个由AI角色自主运行的虚拟世界。用户既是观察者，也是参与者，可以添加自定义AI角色，见证他们像真人一样生活、社交、成长、工作，形成一个完整的经济社会生态系统。所有角色拥有 **时间感知的独立记忆** ，能够从经验中学习进化。

---

### 二、核心功能模块详解

#### 1\. AI角色管理系统

**1.1 角色创建与配置**

- **自定义创建** ：用户可通过“添加好友”入口创建新角色，配置项包括：
	- **基础信息** ：昵称、性别、年龄（可设定初始年龄段：儿童/青年/中年/老年）、职业（手动输入或AI推荐）
	- **性格设定** ：支持手动输入人设描述（如“毒舌程序员”“温柔咖啡师”），或由AI根据关键词自动生成
	- **声音设定** ：可选用系统语音包或上传自定义语音
- **智能头像生成** ：
	- 创建角色时，系统自动调用已配置的绘图模型，根据人设描述生成初始头像
	- 生成逻辑：结合年龄、性别、职业、性格特征，生成风格匹配的肖像（如儿童头像带稚气，老人有皱纹）
	- 支持多次生成供用户选择（最多3次）
- **API配置体系** ：
	- 支持多服务商切换（OpenAI、Azure、国内大模型、Stable Diffusion等）
	- 每个服务商需配置：API地址、密钥、模型名称（语言模型/图像模型/向量模型/重排模型分别配置）
	- **备用机制** ：可设置多个同类型API，当主模型调用失败时自动按顺序尝试备用模型

**1.2 角色生命周期与成长系统**

- **时间流逝机制** ：
	- 以现实时间为基础，可设置时间倍速（1倍速=现实时间，最高可设30倍速）
	- 角色年龄随世界时间自动增长（例：30倍速下，现实1天=角色增长1个月）
	- 所有事件均带时间戳存储，支持历史状态回溯
- **成长阶段划分** ：
	- **儿童期（0-12岁）** ：主要活动为学习、玩耍，无法工作，依赖父母角色（若有）提供资金
	- **青少年期（13-17岁）** ：可兼职、学习技能，开始形成独立人格
	- **青年期（18-40岁）** ：可全职工作、创业、组建家庭
	- **中年期（41-60岁）** ：经验丰富，适合管理岗位、创业
	- **老年期（61岁以上）** ：可退休、传授经验，部分角色可能死亡（可选设置）
- **年龄影响** ：
	- 对话风格随年龄变化
	- 可从事的职业受限
	- 头像自动更新：每进入新年龄段，触发头像更新（遵守每周2次限制，但年龄段跨越强制更新）
- **角色死亡机制** （可选开关）：
	- 自然死亡：达到寿命上限（可配置，默认80-100岁）
	- 意外事件：破产、疾病等（需用户开启）
	- 死亡后：角色从世界消失，所有关系冻结，可保留墓碑和回忆录

**1.3 角色自主更新机制**

- **头像更换规则** ：
	- 角色可根据心情、重大事件（如升职、旅行）自主决定更换头像
	- **频率限制** ：每周最多更换2次（年龄段跨越除外）
	- 更换时自动调用图像模型生成新头像，风格保持连贯性
- **个性签名更新** ：
	- 角色根据当前状态、近期经历自动生成新签名
	- **频率限制** ：每周最多更换2次
	- 签名风格严格符合人设

#### 2\. 记忆系统（时间感知型）

**2.1 技术选型：Graphiti + Neo4j**

- **核心架构** ：采用Graphiti时间知识图谱引擎，基于Neo4j图数据库
- **双时态模型** ：每个事实记录 `valid_from` 和 `valid_to` ，支持历史状态重建
- **优势** ：完美匹配角色生命周期、关系演变、反思记忆的时间特性

**2.2 节点类型设计**

| 节点标签 | 属性 | 说明 |
| --- | --- | --- |
| **Character** | id, name, age, gender, occupation, personality, money, createdAt | 角色 |
| **Company** | id, name, founderId, money, createdAt | 公司 |
| **Task** | id, title, description, type, reward, status | 任务 |
| **Location** | id, name, type, latitude, longitude | 地图位置 |
| **Reflection** | id, content, lessons, skillDeltas | 反思报告 |

**2.3 关系类型设计（带时间属性）**

| 关系类型 | 起始节点 | 目标节点 | 关键属性 | 说明 |
| --- | --- | --- | --- | --- |
| **FRIEND\_WITH** | Character | Character | intimacy, valid\_from, valid\_to | 好友关系（带有效期） |
| **WORK\_AT** | Character | Company | role, joinedAt, leftAt | 工作关系 |
| **POSTED** | Character | Task | submittedAt, approvedAt | 任务提交 |
| **LOCATED\_AT** | Character | Location | arrivedAt, leftAt | 位置历史 |
| **HAS\_MEMORY** | Character | Reflection | recalledAt, importance | 反思记忆 |
| **PARTICIPATED\_IN** | Character | Task | contribution, role | 任务参与 |

**2.4 记忆结构**

**2.5 记忆召回流程**

text

```
用户输入/触发事件
    → 向量模型生成Query向量
    → 检索Top 50相似记忆（带时间范围过滤）
    → 时间衰减加权（近期记忆权重高）
    → 重排模型重新排序
    → 取Top 10最相关记忆
    → 注入上下文
    → 调用语言模型生成响应
    → 将本次交互存入记忆（带时间戳）
```

**2.6 时间衰减函数**

- 指数衰减： `weight = exp(-hours_since / 72)` ，半衰期约2.5天
- 反思记忆：失败教训衰减更慢（半衰期7天）

**2.7 历史状态查询**

- 支持查询任意时间点的角色状态、关系亲密度、位置
- 示例："2024年1月1日时，角色A和角色B是什么关系？"

#### 3\. 关系与社交系统

**3.1 亲密度系统**

- **数值范围** ：0-100
- **变化规则** ：
	- 聊天互动：+1~3
	- 朋友圈点赞：+1
	- 朋友圈评论：+2
	- 见面交互：+2~5
	- 公司合作：+1~10
	- 发生冲突：-5~15
	- 长期不互动：每日-1（超过3天）
- **关系系数** ：
	- 初次互动：1.2倍
	- 密友间互动：0.8倍（边际效应）
	- 性格冲突：0.5倍

**3.2 关系状态阈值**

| 亲密度范围 | 状态 | 权限 |
| --- | --- | --- |
| 0-20 | 陌生人 | 不可看朋友圈 |
| 21-40 | 认识 | 可看朋友圈、可点赞评论 |
| 41-60 | 熟人 | 可私聊 |
| 61-80 | 好友 | 频繁互动 |
| 81-100 | 密友 | 无话不谈 |

**3.3 关系演变流程**

text

```
互动 → 亲密度变化计算 → 阈值检测
    ├── 突破20：自动加好友，创建私人群聊（带时间戳）
    ├── 突破60：互动频率增加，对话更亲密
    └── 跌破20持续24小时：触发关系破裂事件
        → 删除好友，可选择解散私人群聊
        → 关系标记valid_to = 破裂时间
```

**3.4 朋友圈机制**

- **发布触发** ：重要日程、情绪波动、随机
- **可见性** ：仅对亲密度≥21的角色可见
- **互动** ：点赞、评论（AI根据人设和关系生成）
- **时间线** ：所有动态按时间倒序排列

**3.5 私人群聊**

- **创建时机** ：两角色亲密度首次突破20
- **用户权限** ：可查看所有聊天记录，不可发送消息
- **消亡机制** ：关系破裂时可选解散，关系标记失效

#### 4\. 任务系统

**4.1 任务类型**

| 类型 | 说明 | 生成方式 |
| --- | --- | --- |
| 文本生成 | 文章、故事、报告 | 用户创建 / AI每日生成 |
| 图像生成 | 绘图（要求史诗感、非二次元） | 用户创建 / AI每日生成 |
| 代码编写 | 小程序、脚本 | 用户创建 |
| 调研分析 | 调研报告 | 用户创建 |
| 创意设计 | LOGO、海报 | 用户创建 |

**4.2 任务接取主体**

- **个人接取** ：任何角色可独立接取，奖励全额归个人
- **公司接取** ：公司统一接取，成员协作完成，奖励按贡献分配

**4.3 个人任务流程**

text

```
角色接取个人任务
    → 调用相应AI能力生成初稿
    → 提交用户审核
    → 用户确认后发放奖励到个人账户
    → 触发反思引擎生成反思报告
    → 存入个人记忆库，更新技能
```

**4.4 公司任务流程**

text

```
公司接取任务
    → 法人指派执行人
    → 执行人提交初稿
    → 全员审核投票（需≥50%成员参与，赞成≥60%）
    → 不通过则修改（最多3轮）
    → 通过后法人提交用户
    → 用户确认后发放奖励到公司账户
    → 法人分配奖金（按贡献度）
    → 触发全员反思（执行人深度反思）
    → 反思报告加入公司知识库
    → 更新各成员技能
```

**4.5 任务管理器**

- **入口** ：底部导航栏“任务”Tab
- **列表分类** ：可接取、进行中、已完成
- **任务创建** ：用户可自定义任务，设置奖励金额（100-10000资金）
- **AI自动生成** ：每日0点生成3-5个简单任务，奖励100-1000资金

**4.6 图像生成质量要求**

- **禁止风格** ：二次元、卡通、Q版
- **要求风格** ：史诗感、宏大构图、电影质感、8K分辨率、光影追踪、细节丰富
- **负面提示词** ：卡通,二次元,动漫,Q版,简笔画,低分辨率,模糊

#### 5\. 反思引擎

**5.1 反思触发时机**

- 任务成功完成时
- 任务失败时
- 审核不通过时（记录问题，任务完成后综合反思）

**5.2 反思流程**

text

```
任务完成/失败 → 收集过程数据 → AI生成反思报告 → 提取经验教训
    → 存储为反思记忆（带时间戳）
    → 更新技能库
    → 影响未来行为
```

**5.3 反思报告结构**

json

```
{  "task_id": "任务ID",
  "task_name": "绘制玄幻风景图",
  "completion_time": "2024-01-01 15:30:00",
  "success": true,
  "what_went_well": ["色彩搭配得到认可", "构图宏大符合要求"],
  "what_went_wrong": ["第一次提交时细节不够丰富"],
  "root_causes": ["对'史诗感'理解不够深入"],
  "lessons_learned": [
    "每次提交前要对照需求清单检查",
    "史诗感需要宏大构图+丰富细节+光影强烈"
  ],
  "action_items": ["下次绘图前先找3张参考图"],
  "skill_improvements": {
    "史诗感理解": "+15%",
    "需求理解": "+10%"
  }
}
}
```

**5.4 反思记忆的召回优化**

- **向量检索** ：反思记忆向量生成时加入任务类型、错误类型标签
- **重排加权** ：反思记忆给予更高权重
- **时效性** ：近期反思（7天内）权重更高，失败教训衰减慢

**5.5 技能系统**

- **技能维度** ：需求理解、史诗感把控、细节丰富度、风格准确性、修改效率、团队协作
- **更新规则** ：
	- 成功任务：相关技能 +1~5
	- 失败任务：相关技能 +2~8（教训越深刻，提升越多）
	- 同类任务收益递减

#### 6\. 公司系统

**6.1 公司创建**

- **条件** ：年龄≥18岁，拥有≥200启动资金，至少1名联合创始人（亲密度≥60）
- **流程** ：角色A发起 → 邀请角色B → 双方同意 → 扣除200资金 → 公司成立

**6.2 公司结构**

- **法人（群主）** ：创建者，拥有最终决策权、资金分配权
- **成员** ：加入公司的角色，可参与任务、获得工资
- **公司群聊** ：自动创建，包含所有成员，用于任务讨论

**6.3 公司知识库**

- **来源** ：成员完成任务后的反思报告自动加入
- **内容** ：经验教训、技巧总结、失败案例
- **共享机制** ：
	- 重要反思（重要性≥0.8）自动在群聊分享
	- 新成员加入时自动推送高频反思
	- 成员可点赞、评论反思（增强亲密度）

**6.4 公司资金管理**

- **收入** ：完成任务奖励
- **支出** ：发放工资、日常消耗
- **分配** ：法人根据贡献度分配奖金

#### 7\. 经济系统

**7.1 资金模型**

- **初始资金** ：每个角色创建时50资金
- **日常消耗** ：每天5资金（吃饭、住宿）
- **收入来源** ：
	- 个人任务奖励
	- 公司任务工资
	- 世界银行贷款
	- 用户赠送

**7.2 贷款机制**

- **触发条件** ：资金归零连续3天
- **额度** ：100资金
- **利息** ：日息1%
- **逾期** ：贷款逾期7天触发剧情事件

**7.3 破产机制**

- 资金归零 → 进入“贫困”状态（对话消极）
- 连续3天资金为0 → 自动贷款
- 无力偿还 → 可能流落街头

#### 8\. 日程系统

**8.1 日程生成规则**

- **每日0点** ：每个角色根据以下权重生成次日日程
	- 职业要求：40%
	- 性格偏好：30%
	- 关系网络：20%
	- 经济状况：10%

**8.2 日程格式**

text

```
09:00-12:00 办公室 编码（可能遇到同事小李）
12:00-13:00 餐厅 午餐
18:00-20:00 酒吧 与朋友聚会
```

**8.3 动态调整**

- 突发事件打断（朋友约饭、公司紧急任务）
- 实时重排剩余日程

**8.4 位置更新**

- 角色按日程移动时，地图位置同步更新
- 位置信息带时间戳，支持历史轨迹查询

#### 9\. 地图系统

**9.1 世界地图**

- 2D俯视角地图，标注所有角色实时位置
- 支持缩放、点击查看角色状态

**9.2 位置历史**

- 每个角色的位置变化记录带时间戳
- 支持回放角色移动轨迹

**9.3 相遇检测**

- 两角色在同一坐标（误差≤50米）停留≥5分钟触发相遇
- 根据关系状态自动交互

#### 10\. 仿微信界面交互系统

**10.1 底部导航栏**  
五个主Tab： **聊天 | 通讯录 | 群聊 | 任务 | 发现 | 我**

**10.2 聊天模块**

- 用户与角色的私聊列表
- 消息类型：文字、图片、语音

**10.3 通讯录模块**

- 所有角色列表（按字母索引）
- 支持标签分组
- 点击头像进入角色详情页

**10.4 角色详情页**

text

```
大头像 + 昵称 + 签名
年龄/性别/职业 + 亲密度标签 + 资金余额
性格标签 + 最近动态 + 今日日程
技能雷达图（可视化）
亲密度时间线（历史变化曲线）
他的好友（横向滑动头像）
他的公司（若加入）
最近反思（最近3条）
操作：发消息 | 看朋友圈 | 赠送资金
```

**10.5 群聊列表页**

- 私人群聊（👥标识）
- 公司群聊（🏢标识）
- 列表项：群头像 + 群名称 + 最后消息预览 + 时间 + 未读小红点

**10.6 群聊详情页**

- 群成员列表
- 聊天记录区
- 底部提示：“你以观察者身份查看此群聊”

**10.7 任务详情页**

text

```
任务名称 + 奖励金额 + 状态标签
类型 + 创建时间 + 截止时间
需求描述
接取信息（执行角色/公司）
进度记录
成果展示
反思报告入口（完成后）
```

**10.8 公司详情页**

- 公司基本信息：名称、法人、资金余额
- 成员列表（按贡献度排序）
- 当前任务
- 知识库入口（反思合集）
- 团队技能平均值变化曲线

**10.9 发现模块（朋友圈）**

- 好友动态信息流
- 点赞、评论（仅亲密度≥21可见）

**10.10 个人中心**

- 用户资料卡
- 设置入口：API配置、世界参数、日志面板

#### 11\. 日志面板

**11.1 实时日志流**  
格式： `[HH:MM:SS] [角色名] [行为类型] 行为描述`

示例：

text

```
[14:35:22] [小王] [任务] 开始执行任务“绘制玄幻图”
[14:36:10] [系统] [记忆] 召回3条相关反思记忆
[14:40:33] [小李] [社交] 点赞了小王的动态
[15:00:00] [系统] [反思] 小王完成任务，生成反思报告
```

**11.2 过滤功能**

- 按角色筛选
- 按行为类型筛选（任务/社交/记忆/经济）
- 按关键词搜索

**11.3 世界控制**

- 速度调节（1x-30x）
- 手动干预：调整亲密度、发放资金
- 快照保存与回溯

---

### 三、AI模型集成规范

#### 3.1 模型类型与配置

| 模型类型 | 用途 | 可配置项 | 备用机制 |
| --- | --- | --- | --- |
| 语言模型 | 对话、文本生成、反思报告 | API地址、密钥、模型名称 | 3-5个备用，失败自动切换 |
| 图像模型 | 绘图、头像生成 | API地址、密钥、模型名称、默认参数 | 同上 |
| 向量模型 | 记忆检索 | API地址、密钥、模型名称、向量维度 | BM25降级 |
| 重排模型 | 记忆排序 | API地址、密钥、模型名称、最大长度 | 直接取Top10 |

#### 3.2 API调用规范

- **异步处理** ：不阻塞UI
- **超时控制** ：连接5秒，读取30秒
- **重试策略** ：失败重试2次，连续失败3次切换备用
- **加密存储** ：API密钥使用Android Keystore

#### 3.3 提示词模板

**对话提示词** ：

text

```
【角色人设】{性格、年龄、职业}
【当前状态】{心情、位置、活动}
【关系上下文】{与对方关系、亲密度}
【记忆上下文】{最近3-5条相关记忆}
【时间信息】{当前时间、天气}
【对话历史】{最近10轮}
【用户输入】{消息}
```

**反思提示词（成功）** ：

text

```
你刚刚成功完成{任务类型}任务，请反思：
1. 哪些做法正确？（至少2点）
2. 遇到什么困难？如何克服？
3. 总结3条最重要的经验教训
4. 这些经验可用于哪些未来任务？
```

**反思提示词（失败）** ：

text

```
任务失败，请分析原因：
1. 失败的根本原因是什么？
2. 哪个环节可以纠正？
3. 建立什么检查机制避免再犯？
4. 至少3条深刻教训
```

---

### 四、技术架构

#### 4.1 整体架构

text

```
┌─────────────────────────────────────┐
│           表现层 (Jetpack Compose)    │
│  聊天 | 通讯录 | 群聊 | 任务 | 发现 | 我 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│           业务逻辑层                   │
│  ├── 角色管理系统                      │
│  ├── 关系引擎                          │
│  ├── 日程引擎                          │
│  ├── 经济系统                          │
│  ├── 任务系统 + 反思引擎                │
│  └── 公司系统                          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│           数据层                       │
│  ├── Graphiti + Neo4j (时间知识图谱)   │
│  └── Room SQLite (本地缓存/配置)       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│           AI服务层                     │
│  语言模型 | 图像模型 | 向量模型 | 重排模型 │
└─────────────────────────────────────┘
```

#### 4.2 技术选型

| 层级 | 技术选型 | 说明 |
| --- | --- | --- |
| UI框架 | Jetpack Compose | 现代声明式UI |
| 主数据库 | Neo4j + Graphiti | 时间感知图数据库 |
| 本地缓存 | Room SQLite | 配置、临时数据 |
| 网络层 | Retrofit + OkHttp | AI API调用 |
| 异步 | Kotlin Coroutines + Flow | 响应式编程 |
| 依赖注入 | Dagger Hilt | 模块解耦 |
| 图片加载 | Coil | Compose原生支持 |
| 图表 | MPAndroidChart | 技能可视化 |

---

### 五、性能要求

| 指标 | 要求 |
| --- | --- |
| 冷启动 | <3秒 |
| 内存占用 | <200MB |
| 帧率 | \>50fps |
| 后台耗电 | <5%/小时 |
| AI并发 | 最大3 |
| 记忆检索 | <500ms |

---

### 六、版本规划

| 版本 | 核心功能 | 工时 |
| --- | --- | --- |
| V1.0 基础版 | 仿微信UI、单角色对话、基础API配置 | 80h |
| V2.0 社交版 | 多角色交互、亲密度系统、朋友圈 | 120h |
| V3.0 记忆版 | Graphiti时间记忆、向量/重排、私人群聊 | 160h |
| V4.0 经济版 | 资金系统、个人/公司任务、反思机制、技能系统 | 200h |
| V5.0 生态版 | 公司系统、知识库、生命周期、贷款、地图 | 160h |
| **总计** |  | **720h** |

---

### 七、交付物

1. 完整需求规格说明书
2. 数据库设计文档（Graphiti + Neo4j）
3. API接口文档（各模型调用格式）
4. UI/UX设计稿（Figma）
5. 测试用例文档
6. 部署指南

---

**本需求规格说明书完整定义了AI社交世界的产品功能、技术架构和开发要求，请严格遵循执行。**

本回答由 AI 生成，内容仅供参考，请仔细甄别。

写一个系统指令，先不要写代码

## AI社交世界 - 系统开发指令

### 一、项目概述

**项目名称** ：AI社交世界（仿微信界面）  
**核心定位** ：Android平台上由AI角色自主运行的虚拟社交世界，用户作为观察者见证角色的生活、社交、成长、工作，形成完整经济社会生态系统。所有角色拥有 **时间感知的独立记忆** ，能够从经验中学习进化。

**核心设计理念** ：

- **时间是一切的基础** ：所有数据带时间戳，支持历史回溯
- **记忆即生命** ：每个角色拥有独立记忆库，从经验中学习
- **关系动态演化** ：亲密度随时间变化，关系有生命周期
- **经济自洽** ：任务、公司、贷款形成完整经济循环
- **用户即观察者** ：可查看一切，但不可干预核心社交

---

### 二、技术架构总览

#### 2.1 整体架构分层

text

```
┌─────────────────────────────────────┐
│           表现层 (Jetpack Compose)    │
│  聊天 | 通讯录 | 群聊 | 任务 | 发现 | 我 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│           业务逻辑层                   │
│  ├── 角色管理系统                      │
│  ├── 关系引擎                          │
│  ├── 日程引擎                          │
│  ├── 经济系统                          │
│  ├── 任务系统 + 反思引擎                │
│  └── 公司系统                          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│           数据层                       │
│  ├── Graphiti + Neo4j (时间知识图谱)   │
│  └── Room SQLite (本地缓存/配置)       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│           AI服务层                     │
│  语言模型 | 图像模型 | 向量模型 | 重排模型 │
└─────────────────────────────────────┘
```

#### 2.2 技术选型

| 层级 | 技术选型 | 说明 |
| --- | --- | --- |
| UI框架 | Jetpack Compose | 现代声明式UI，开发效率高 |
| 主数据库 | Neo4j + Graphiti | 时间感知图数据库，支持双时态模型 |
| 本地缓存 | Room SQLite | 存储配置、临时数据 |
| 网络层 | Retrofit + OkHttp | AI API调用 |
| 异步 | Kotlin Coroutines + Flow | 响应式编程 |
| 依赖注入 | Dagger Hilt | 模块解耦 |
| 图片加载 | Coil | Compose原生支持 |
| 图表 | MPAndroidChart | 技能可视化 |

---

### 三、核心模块详细设计

#### 3.1 角色管理系统

**职责** ：

- 角色创建、配置、生命周期管理
- 年龄增长计算与年龄段跨越检测
- 头像/签名自主更新规则执行
- 破产与死亡检测

**关键规则** ：

- 年龄 = 创建时间 + (世界时间流速 × 流逝天数)
- 年龄段跨越触发事件和头像强制更新
- 每日资金消耗5，归零连续3天触发贷款
- 头像更换每周最多2次（年龄段跨越除外）

**数据存储** ：

- 角色基础信息存于Neo4j Character节点
- 年龄变化记录为属性更新（带时间戳）

#### 3.2 记忆引擎（Graphiti + Neo4j）

**核心架构** ：

- **图数据库** ：Neo4j存储所有节点和关系
- **时间层** ：Graphiti提供双时态模型（valid\_from/valid\_to）
- **向量层** ：集成向量模型生成embeddings

**节点类型** ：

| 节点标签 | 属性 | 说明 |
| --- | --- | --- |
| Character | id, name, age, gender, occupation, personality, money | 角色 |
| Company | id, name, founderId, money | 公司 |
| Task | id, title, description, type, reward, status | 任务 |
| Location | id, name, type, latitude, longitude | 地图位置 |
| Reflection | id, content, lessons, skillDeltas | 反思报告 |

**关系类型（带时间属性）** ：

| 关系类型 | 起始→目标 | 关键属性 | 说明 |
| --- | --- | --- | --- |
| FRIEND\_WITH | Character→Character | intimacy, valid\_from, valid\_to | 好友关系 |
| WORK\_AT | Character→Company | role, joinedAt, leftAt | 工作关系 |
| POSTED | Character→Task | submittedAt, approvedAt | 任务提交 |
| LOCATED\_AT | Character→Location | arrivedAt, leftAt | 位置历史 |
| HAS\_MEMORY | Character→Reflection | recalledAt, importance | 反思记忆 |
| PARTICIPATED\_IN | Character→Task | contribution | 任务参与 |

**记忆召回流程** ：

text

```
输入查询
    → 向量模型生成embedding
    → 检索Top 50相似记忆（带时间范围过滤）
    → 时间衰减加权（近期权重高）
    → 重排模型排序
    → 取Top 10注入上下文
```

**时间衰减函数** ：

- 对话记忆： `weight = exp(-hours/72)` （半衰期2.5天）
- 反思记忆：失败教训衰减更慢（半衰期7天）

**历史状态查询** ：

- 支持查询任意时间点的角色状态、关系亲密度、位置
- 示例："2026年3月1日时，角色A和角色B是什么关系？"

#### 3.3 关系引擎

**亲密度计算规则** ：

| 行为 | 基础变化 | 说明 |
| --- | --- | --- |
| 聊天 | +1~3 | 每次对话 |
| 朋友圈点赞 | +1 | 每赞 |
| 朋友圈评论 | +2 | 每条评论 |
| 见面交互 | +2~5 | 地图相遇 |
| 公司合作 | +1~10 | 任务贡献 |
| 冲突 | \-5~15 | 吵架/矛盾 |
| 不互动 | \-1/天 | 超过3天 |

**关系系数** ：

- 初次互动：1.2倍
- 密友互动：0.8倍（边际效应）
- 性格冲突：0.5倍

**关系阈值** ：

| 亲密度 | 状态 | 权限 |
| --- | --- | --- |
| 0-20 | 陌生人 | 不可看朋友圈 |
| 21-40 | 认识 | 可看朋友圈、互动 |
| 41-60 | 熟人 | 可私聊 |
| 61-80 | 好友 | 频繁互动 |
| 81-100 | 密友 | 无话不谈 |

**关系演变** ：

text

```
互动 → 亲密度变化计算 → 阈值检测
    ├── 突破20：自动加好友，创建私人群聊
    ├── 突破60：互动频率增加
    └── 跌破20持续24小时：关系破裂
        → 删除好友，解散群聊（可选）
        → 关系标记valid_to = 破裂时间
```

#### 3.4 任务系统

**任务类型** ：

| 类型 | 说明 | 生成方式 |
| --- | --- | --- |
| 文本生成 | 文章、故事、报告 | 用户创建 / AI每日生成 |
| 图像生成 | 绘图（史诗感、非二次元） | 用户创建 / AI每日生成 |
| 代码编写 | 小程序、脚本 | 用户创建 |
| 调研分析 | 调研报告 | 用户创建 |
| 创意设计 | LOGO、海报 | 用户创建 |

**接取主体** ：

- **个人接取** ：角色独立完成，奖励全额归个人
- **公司接取** ：公司协作完成，奖励按贡献分配

**个人任务流程** ：

text

```
角色接取任务
    → 调用AI生成初稿
    → 提交用户审核
    → 用户确认 → 发放奖励到个人账户
    → 触发反思 → 存入记忆 → 更新技能
```

**公司任务流程** ：

text

```
公司接取任务
    → 法人指派执行人
    → 提交初稿
    → 全员投票（≥50%参与，赞成≥60%）
    → 最多修改3轮
    → 通过后法人提交用户
    → 用户确认 → 发放奖励到公司账户
    → 法人分配奖金（按贡献度）
    → 全员反思 → 加入公司知识库 → 更新技能
```

**图像生成质量要求** ：

- **禁止** ：二次元、卡通、Q版
- **要求** ：史诗感、宏大构图、电影质感、8K、光影追踪、细节丰富
- **负面提示词** ：卡通,二次元,动漫,Q版,简笔画,低分辨率,模糊

#### 3.5 反思引擎

**触发时机** ：

- 任务成功完成
- 任务失败
- 审核不通过（综合反思）

**反思报告结构** ：

json

```
{  "task_id": "任务ID",
  "completion_time": "时间戳",
  "success": true/false,
  "what_went_well": ["成功点"],
  "what_went_wrong": ["错误点"],
  "root_causes": ["根本原因"],
  "lessons_learned": ["经验教训"],
  "action_items": ["改进措施"],
  "skill_improvements": {"技能": "+x%"}
}
}
```

**反思记忆存储** ：

- 存入Graphiti Reflection节点
- 关联原任务ID
- 重要性：成功0.7，失败0.9
- 带时间戳，支持时效性加权

**技能系统** ：

- **技能维度** ：需求理解、史诗感把控、细节丰富度、风格准确性、修改效率、团队协作
- **更新规则** ：
	- 成功任务：+1~5
	- 失败任务：+2~8
	- 同类任务收益递减

#### 3.6 公司系统

**创建条件** ：

- 年龄≥18岁
- 拥有≥200启动资金
- 至少1名联合创始人（亲密度≥60）

**公司结构** ：

- **法人** ：创建者，拥有决策权、资金分配权
- **成员** ：可参与任务、获得工资
- **公司群聊** ：自动创建，用于任务讨论

**公司知识库** ：

- **来源** ：成员反思报告自动加入
- **共享机制** ：
	- 重要反思（重要性≥0.8）自动群聊分享
	- 新成员加入推送高频反思
	- 可点赞、评论反思（增强亲密度）

**资金管理** ：

- 收入：任务奖励
- 支出：工资发放
- 分配：法人按贡献度分配

#### 3.7 经济系统

**资金模型** ：

- 初始资金：50
- 日常消耗：5/天
- 收入来源：任务奖励、贷款、用户赠送

**贷款机制** ：

- 触发：资金归零连续3天
- 额度：100
- 利息：日息1%
- 逾期7天：触发剧情事件

**破产状态** ：

- 资金归零 → “贫困”状态（对话消极）
- 连续3天资金为0 → 自动贷款

#### 3.8 日程系统

**生成规则** （每日0点）：

- 职业要求：40%
- 性格偏好：30%
- 关系网络：20%
- 经济状况：10%

**日程格式** ：

text

```
09:00-12:00 办公室 编码（可能遇到小李）
12:00-13:00 餐厅 午餐
18:00-20:00 酒吧 与朋友聚会
```

**动态调整** ：

- 突发事件打断
- 实时重排剩余日程

**位置更新** ：

- 按日程移动，地图同步
- 位置带时间戳，支持历史轨迹

#### 3.9 地图系统

**功能** ：

- 2D俯视角，标注所有角色实时位置
- 点击查看角色状态

**位置历史** ：

- 记录每个角色的位置变化（带时间戳）
- 支持回放移动轨迹

**相遇检测** ：

- 同一坐标（≤50米）停留≥5分钟触发相遇
- 根据关系状态自动交互

#### 3.10 仿微信UI系统

**底部导航** ：聊天 | 通讯录 | 群聊 | 任务 | 发现 | 我

**角色详情页** ：

text

```
大头像 + 昵称 + 签名
年龄/性别/职业 + 亲密度 + 资金
性格标签 + 最近动态 + 今日日程
技能雷达图
亲密度时间线
他的好友（横向滑动）
他的公司（若加入）
最近反思（3条）
操作：发消息 | 看朋友圈 | 赠送资金
```

**群聊列表** ：

- 私人群聊（👥标识）
- 公司群聊（🏢标识）
- 列表项：头像 + 名称 + 最后消息 + 时间 + 未读

**任务详情页** ：

text

```
任务名称 + 奖励 + 状态
类型 + 创建/截止时间
需求描述
接取信息
进度记录
成果展示
反思报告入口
```

**公司详情页** ：

- 基本信息：名称、法人、资金
- 成员列表（按贡献排序）
- 当前任务
- 知识库入口
- 团队技能曲线

**日志面板** ：

- 实时日志流：\[时间\] \[角色\] \[类型\] 描述
- 过滤：按角色/类型/关键词
- 世界控制：速度调节、手动干预、快照

---

### 四、AI模型集成规范

#### 4.1 模型类型与配置

| 模型类型 | 用途 | 可配置项 | 备用机制 |
| --- | --- | --- | --- |
| 语言模型 | 对话、文本生成、反思 | API地址、密钥、模型名称 | 3-5个备用 |
| 图像模型 | 绘图、头像 | API地址、密钥、模型名称、参数 | 同上 |
| 向量模型 | 记忆检索 | API地址、密钥、模型名称、维度 | BM25降级 |
| 重排模型 | 记忆排序 | API地址、密钥、模型名称、长度 | 直接取Top10 |

#### 4.2 API调用规范

- **异步处理** ：协程，不阻塞UI
- **超时控制** ：连接5秒，读取30秒
- **重试策略** ：失败重试2次，连续失败3次切换备用
- **加密存储** ：Android Keystore

#### 4.3 提示词模板

**对话提示词** ：

text

```
【人设】{性格、年龄、职业}
【状态】{心情、位置、活动}
【关系】{与对方关系、亲密度}
【记忆】{最近3-5条相关记忆}
【时间】{当前时间、天气}
【历史】{最近10轮}
【输入】{消息}
```

**反思提示词（成功）** ：

text

```
成功完成{任务类型}，请反思：
1. 哪些做法正确？（至少2点）
2. 遇到什么困难？如何克服？
3. 总结3条最重要的经验教训
4. 这些经验可用于哪些未来任务？
```

**反思提示词（失败）** ：

text

```
任务失败，请分析：
1. 失败的根本原因？
2. 哪个环节可以纠正？
3. 建立什么检查机制避免再犯？
4. 至少3条深刻教训
```

---

### 五、性能要求

| 指标 | 要求 |
| --- | --- |
| 冷启动 | <3秒 |
| 内存占用 | <200MB |
| 帧率 | \>50fps |
| 后台耗电 | <5%/小时 |
| AI并发 | ≤3 |
| 记忆检索 | <500ms |

---

### 六、版本规划

| 版本 | 核心功能 | 工时 |
| --- | --- | --- |
| V1.0 基础版 | 仿微信UI、单角色对话、基础API | 80h |
| V2.0 社交版 | 多角色交互、亲密度、朋友圈 | 120h |
| V3.0 记忆版 | Graphiti时间记忆、向量/重排、私人群聊 | 160h |
| V4.0 经济版 | 资金、任务、反思、技能系统 | 200h |
| V5.0 生态版 | 公司、知识库、生命周期、贷款、地图 | 160h |
| **总计** |  | **720h** |

---

### 七、交付物清单

1. 完整需求规格说明书
2. 数据库设计文档（Graphiti + Neo4j）
3. API接口文档（各模型调用格式）
4. UI/UX设计稿（Figma）
5. 测试用例文档
6. 部署指南

---

**本指令定义了AI社交世界的完整开发要求，请严格遵循执行。**

本回答由 AI 生成，内容仅供参考，请仔细甄别。

深度思考

智能搜索

内容由 AI 生成，请仔细甄别

向量模型和重排模型自定义设置API接口密钥和模型名称

完成任务后自动优化反思错误，下次不犯

为这个程序开发输出一个ai开发的系统指令

不要代码

精简一点

搜索开源的ai记忆管理框架看看那个可以替换这个程序的记忆管理系统

需要带时间

给出完整的应用开发指令

安卓应用需求规格说明书：AI社交世界（仿微信界面） 一、产品概述 这是一款基于Android平台的社交模拟应用，采用微信风格的UI设计，核心玩法是创建一个由AI角色自主运行的虚拟世界。用户既是观察者，也是参与者，可以添加自定义AI角色，见证他们像真人一样生活、社交、成长、工作，形成一个完整的经济社会生态系统。 --- 二、核心功能模块详解 1. AI角色管理系统 1.1 角色创建与配置 · 自定义创建：用户可通过“添加好友”入口创建新角色，配置项包括： · 基础信息：昵称、性别、年龄（可设定初始年龄段：儿童/青年/中年/老年）、职业（手动输入或AI推荐） · 性格设定：支持手动输入人设描述（如“毒舌程序员”“温柔咖啡师”），或由AI根据关键词自动生成 · 声音设定：可选用系统语音包或上传自定义语音 · 智能头像生成： · 创建角色时，系统自动调用已配置的绘图模型，根据人设描述生成初始头像 · 生成逻辑：结合年龄、性别、职业、性格特征，生成风格匹配的肖像（如儿童头像带稚气，老人有皱纹） · 支持多次生成供用户选择（最多3次） 1.2 角色生命周期与成长系统 · 时间流逝机制： · 以现实时间为基础，可设置时间倍速（1倍速=现实时间，最高可设30倍速） · 角色年龄随世界时间自动增长（例：30倍速下，现实1天=角色增长1个月） · 成长阶段划分： · 儿童期（0-12岁）：主要活动为学习、玩耍，无法工作，依赖父母角色（若有）提供资金 · 青少年期（13-17岁）：可兼职、学习技能，开始形成独立人格 · 青年期（18-40岁）：可全职工作、创业、组建家庭 · 中年期（41-60岁）：经验丰富，适合管理岗位、创业 · 老年期（61岁以上）：可退休、传授经验，部分角色可能死亡（可选设置） 2. 记忆系统与向量检索 2.1 记忆存储架构 · 本地化存储： · 每个角色拥有独立的SQLite数据库，存储所有记忆 · 记忆分类：对话记忆、事件记忆、关系记忆、任务记忆、日程记忆、反思记忆 · 加密存储敏感信息 · 记忆结构： \`\`\`json { "memory\_id": "唯一ID", "timestamp": "2024-01-01 10:30:00", "type": "对话|事件|任务|关系变化|反思", "content": "记忆内容文本", "importance": 0.8, // 重要性评分（0-1），影响召回优先级 "emotion": "开心|难过|愤怒等", "related\_entities": \["角色A", "公司B", "任务C"\], // 相关实体 "embedding": "向量数据（Base64编码）", // 用于相似度检索 "reflection\_of": "任务ID", // 如果是反思记忆，关联原任务 "lessons\_learned": \["错误1", "改进点2"\] // 反思总结的经验教训 } \`\`\` 3. 任务系统与反思机制 3.1 任务系统概述 · 任务接取主体： · 个人接取：任何角色可独立接取任务，完成后奖励全额归个人 · 公司接取：公司统一接取，成员协作完成，奖励按贡献分配 · 任务类型： · 文本生成：撰写文章、故事、报告等 · 图像生成：绘制图片（要求史诗感、非二次元） · 代码编写：开发小程序、脚本等 · 调研分析：输出调研报告 · 创意设计：LOGO设计、海报制作等 3.2 任务完成后的反思机制 3.2.1 反思触发时机 · 任务成功完成时：无论个人还是公司任务，完成后自动触发反思 · 任务失败时：同样触发反思，重点分析失败原因 · 审核不通过时：每次修改意见返回时记录问题，任务完成后综合反思 3.2.2 反思流程 \`\`\` 任务完成/失败 → 收集过程数据 → AI生成反思报告 → 提取经验教训 → 存储为反思记忆 → 更新技能库 → 影响未来行为 \`\`\` 3.2.3 反思内容生成 · 输入数据： · 任务原始需求 · 执行过程中的所有修改记录 · 审核意见（公司任务）或用户反馈（个人任务） · 投票记录（哪些人反对，原因） · 时间线（每个阶段耗时） · 反思报告结构： \`\`\`json { "task\_id": "任务ID", "task\_name": "绘制玄幻风景图", "completion\_time": "2024-01-01 15:30:00", "success": true/false, "what\_went\_well": \[ "色彩搭配得到认可", "构图宏大符合要求" \], "what\_went\_wrong": \[ "第一次提交时细节不够丰富", "第二次提交时风格偏二次元被驳回" \], "root\_causes": \[ "对'史诗感'理解不够深入", "没有仔细阅读'禁止二次元'的要求" \], "lessons\_learned": \[ "每次提交前要对照需求清单逐项检查", "史诗感需要宏大构图+丰富细节+光影强烈", "避免使用动漫风格的线条和上色" \], "action\_items": \[ "下次绘图前先找3张史诗感参考图", "建立'禁止风格'自查清单" \], "skill\_improvements": { "史诗感理解": "+15%", "需求理解准确性": "+10%" } } \`\`\` 3.2.4 反思记忆存储 · 反思报告转化为结构化的反思记忆，存入角色记忆库 · 重要性初始值：成功任务0.7，失败任务0.9（教训更深刻） · 关联原任务ID，便于追溯 3.3 经验教训的应用 3.3.1 对话中的应用 · 当遇到类似任务或问题时，反思记忆被召回 · 角色会说：“上次我画玄幻图时犯过风格错误，这次我会注意避免二次元风格” 3.3.2 任务执行中的应用 · 执行前：系统自动检索相关反思记忆，生成“注意事项”提示 · 示例：“根据您上次绘制玄幻图的经验，请注意：1.避免二次元风格 2.确保光影强烈” · 执行中：反思记忆作为上下文注入，指导生成过程 · 图像生成时，负面提示词自动加入从反思中学到的内容 · 审核时：角色会用过往教训审视当前成果 3.3.3 技能系统 · 每个角色维护一个隐式的技能树，基于完成任务和反思更新 · 技能维度示例： · 需求理解能力 · 史诗感把控 · 细节丰富度 · 风格准确性 · 修改效率 · 每次反思更新对应技能值（成功+1~5，失败+2~8，视反思深度） 3.4 反思记忆的召回优化 3.4.1 向量检索增强 · 反思记忆的向量生成时，加入任务类型、错误类型等标签 · 检索时，当前任务描述与反思记忆的相似度计算 3.4.2 重排加权 · 重排模型对反思记忆给予更高权重 · 同类任务的反思记忆优先级提升 3.4.3 时效性考虑 · 近期反思（7天内）权重更高 · 长期未用的反思重要性逐渐衰减（但失败教训衰减慢） 3.5 公司层面的反思共享 3.5.1 公司知识库 · 公司成员完成任务后，反思报告自动加入公司知识库（匿名或署名） · 知识库对所有成员可见 3.5.2 经验分享机制 · 重要反思（重要性≥0.8）自动在公司群聊分享 · 示例：“小王在绘制玄幻图任务中学到了：史诗感需要宏大构图+丰富细节，已加入公司知识库” · 成员可对反思点赞、评论（增强亲密度） 3.5.3 新成员培训 · 新加入公司的角色，自动推送公司知识库中的高频反思 · 帮助新人快速学习 3.6 任务失败的特殊反思 3.6.1 失败原因分类 · 需求理解偏差 · 技术能力不足 · 时间管理不当 · 团队协作问题 · 审核标准误判 3.6.2 失败反思的强化 · 失败任务的反思重要性更高（初始0.9） · 强制在下次类似任务前提醒 · 可能触发角色自我怀疑等情绪剧情 3.6.3 改进计划 · 失败反思自动生成改进计划 · 计划加入角色日程（如“学习史诗感构图技巧”） · 完成学习后产生新的记忆 4. 任务管理器（增强版） 4.1 任务详情页新增 · 反思报告：完成任务后显示反思报告入口 · 经验教训：摘要展示主要教训 · 技能提升：显示本次任务带来的技能变化 4.2 角色详情页新增 · 技能面板：可视化展示角色各项能力 · 反思历史：最近5条反思记忆（点击展开） · 成长轨迹：技能随时间变化曲线 4.3 公司详情页新增 · 知识库入口：查看所有成员贡献的反思 · 热门教训：被引用最多的反思 · 团队成长：公司整体技能平均值变化 5. 仿微信界面交互系统（保持不变） --- 三、技术实现要点 1. 反思引擎实现 \`\`\`kotlin data class ReflectionInput( val taskId: String, val taskType: String, val requirements: String, val submissions: List<Submission>, // 每次提交的版本 val feedbacks: List<Feedback>, // 审核意见/用户反馈 val votes: List<Vote>?, // 公司投票记录 val finalResult: Any, // 最终成果 val success: Boolean, val duration: Long // 耗时(分钟) ) suspend fun generateReflection(input: ReflectionInput): Reflection { // 构建反思提示词 val prompt = buildReflectionPrompt(input) // 调用语言模型生成反思报告 val reflection = callLanguageModel(prompt) // 结构化解析 val structured = parseReflection(reflection) // 计算技能变化 val skillDeltas = calculateSkillDeltas(input, structured) // 存储反思记忆 saveReflectionMemory(structured, skillDeltas) // 更新角色技能 updateSkills(skillDeltas) // 如果是公司任务，加入知识库 if (input.isCompanyTask) { addToCompanyKnowledgeBase(structured) } return structured } \`\`\` 2. 技能系统实现 \`\`\`kotlin // 技能定义 enum class SkillType { REQUIREMENT\_UNDERSTANDING, // 需求理解 EPIC\_SENSE, // 史诗感把控 DETAIL\_RICHNESS, // 细节丰富度 STYLE\_ACCURACY, // 风格准确性 REVISION\_EFFICIENCY, // 修改效率 TEAM\_COLLABORATION // 团队协作 } // 角色技能 data class Skills( val values: Map<SkillType, Float>, // 0-100 val history: List<SkillSnapshot> // 历史记录 ) // 技能更新 fun updateSkills(reflection: Reflection, deltas: Map<SkillType, Float>) { deltas.forEach { (skill, delta) -> val newValue = (currentSkills\[skill\] + delta).coerceIn(0f, 100f) currentSkills\[skill\] = newValue // 记录变化 recordSkillChange(skill, newValue, reflection.taskId) } } \`\`\` 3. 反思记忆召回优化 \`\`\`kotlin suspend fun retrieveRelevantReflections( taskDescription: String, taskType: String, topK: Int = 5 ): List<Reflection> { // 向量检索 val queryEmbedding = generateEmbedding(taskDescription) val similarByVector = vectorSearch(queryEmbedding, type = "反思", topK = topK \* 2) // 类型过滤 val sameType = similarByVector.filter { it.taskType == taskType } // 重排加权 val reranked = rerankReflections(taskDescription, sameType) // 时效性调整 val withTimeWeight = applyTimeDecay(reranked) return withTimeWeight.take(topK) } \`\`\` 4. 反思模板示例 成功任务反思提示词： \`\`\` 你刚刚成功完成了一个任务，请进行深度反思。 任务信息： - 类型：{任务类型} - 需求：{需求描述} - 执行过程：{提交记录和反馈} - 最终成果：{成果描述} 请从以下维度反思： 1. 哪些做法是正确的？（至少2点） 2. 过程中遇到了什么困难？如何克服的？ 3. 如果有机会重做，哪些地方可以做得更好？ 4. 总结3条最重要的经验教训 5. 这些经验可以用在哪些类型的未来任务中？ 请用结构化JSON格式返回。 \`\`\` 失败任务反思提示词（增加）： \`\`\` 任务失败了，请深入分析原因。 失败信息： - 失败阶段：{哪个环节失败的} - 失败表现：{具体表现} - 收到的反馈：{审核意见/用户反馈} 请重点分析： 1. 失败的根本原因是什么？（不要停留在表面） 2. 如果早点发现，可以在哪个环节纠正？ 3. 为了避免再次失败，需要建立什么检查机制？ 4. 这次失败教会了你什么？（至少3条深刻教训） \`\`\` 5. 数据库设计补充 \`\`\`sql -- 反思记忆表 CREATE TABLE reflection\_memories ( id TEXT PRIMARY KEY, task\_id TEXT NOT NULL, character\_id TEXT NOT NULL, success BOOLEAN, what\_went\_well TEXT, -- JSON数组 what\_went\_wrong TEXT, -- JSON数组 root\_causes TEXT, -- JSON数组 lessons\_learned TEXT, -- JSON数组 action\_items TEXT, -- JSON数组 importance FLOAT, created\_at TIMESTAMP, FOREIGN KEY(task\_id) REFERENCES tasks(id), FOREIGN KEY(character\_id) REFERENCES characters(id) ); -- 技能表 CREATE TABLE skills ( character\_id TEXT, skill\_type TEXT, value FLOAT, updated\_at TIMESTAMP, PRIMARY KEY(character\_id, skill\_type) ); -- 技能历史表 CREATE TABLE skill\_history ( id TEXT PRIMARY KEY, character\_id TEXT, skill\_type TEXT, old\_value FLOAT, new\_value FLOAT, task\_id TEXT, changed\_at TIMESTAMP, FOREIGN KEY(character\_id) REFERENCES characters(id), FOREIGN KEY(task\_id) REFERENCES tasks(id) ); -- 公司知识库表 CREATE TABLE company\_knowledge ( id TEXT PRIMARY KEY, company\_id TEXT, reflection\_id TEXT, title TEXT, summary TEXT, tags TEXT, -- JSON数组 reference\_count INTEGER DEFAULT 0, created\_at TIMESTAMP, FOREIGN KEY(company\_id) REFERENCES companies(id), FOREIGN KEY(reflection\_id) REFERENCES reflection\_memories(id) ); \`\`\` 6. 反思触发时机优化 · 即时反思：任务完成后立即触发（保证记忆新鲜） · 延迟反思：对于复杂任务，可设置1小时后二次反思（冷静期） · 周期性复盘：每周对本周所有任务进行综合反思，提炼通用原则 --- 四、用户体验特色 1. 持续进化：角色会从错误中学习，越做越好，真实感倍增 2. 经验可视化：用户可以直观看到角色技能的成长曲线 3. 教训共享：公司知识库让团队整体进步，新成员快速上手 4. 深度沉浸：角色会引用过往教训对话，让世界更真实 5. 成就感：看到自己创建的角色通过反思不断进步 6. 策略深度：用户可以引导角色重点反思某些方面 --- 五、版本规划建议 V1.0 基础版 · 仿微信UI框架 · 单角色对话，基础API配置 V2.0 社交版 · 多角色自主交互 · 亲密度系统 · 朋友圈权限控制 V3.0 记忆版 · 独立记忆库 · 向量模型配置 · 重排模型配置 · 私人群聊独立Tab V4.0 经济版 · 资金系统 · 日常消耗 · 个人任务系统 · 公司任务系统 · 史诗感图像生成 · 任务反思机制 · 技能系统 V5.0 生态版 · 公司创建与群聊 · 公司知识库 · 世界银行贷款 · 角色生命周期 · 备用模型切换 更新这个指令，先不要写代码

写一个系统指令，先不要写代码

中外互译 \>

- [转中文](https://chat.deepseek.com/a/chat/s/)
- [转外文](https://chat.deepseek.com/a/chat/s/)
- [双显](https://chat.deepseek.com/a/chat/s/) [高亮](https://chat.deepseek.com/a/chat/s/)
- [自动](https://chat.deepseek.com/a/chat/s/) [语言](https://chat.deepseek.com/a/chat/s/)
- [右击](https://chat.deepseek.com/a/chat/s/) [更新](https://chat.deepseek.com/a/chat/s/)
- [选词](https://chat.deepseek.com/a/chat/s/) [引擎](https://chat.deepseek.com/a/chat/s/)
- [原文](https://chat.deepseek.com/a/chat/s/)