# AI社交世界 Spec

## Why
创建一个基于Android平台的AI社交模拟应用，采用微信风格UI设计，让用户观察和参与一个由AI角色自主运行的虚拟世界。角色拥有时间感知的独立记忆，能够从经验中学习进化，形成完整的经济社会生态系统。

## What Changes
- 创建全新的Android应用项目
- 实现AI角色管理系统，支持角色创建、成长、生命周期管理
- 实现基于Graphiti + Neo4j的时间感知记忆系统
- 实现关系与社交系统，包括亲密度、朋友圈、群聊
- 实现任务系统，支持多种任务类型和反思引擎
- 实现公司系统，支持公司创建、知识库、资金管理
- 实现经济系统，包括资金模型、贷款、破产机制
- 实现日程系统，支持每日日程生成和动态调整
- 实现地图系统，支持2D地图、位置历史、相遇检测
- 实现仿微信界面，包括聊天、通讯录、任务、发现等模块
- 实现日志面板，支持实时日志流和世界控制

## Impact
- Affected specs: 所有核心功能模块
- Affected code: 整个应用架构

## ADDED Requirements

### Requirement: 项目初始化
The system SHALL initialize a new Android project with proper dependencies and configuration.

#### Scenario: Success case
- **WHEN** developer initializes the project
- **THEN** project structure is created with all necessary dependencies (Jetpack Compose, Neo4j, Room, Retrofit, Hilt, Coil, MPAndroidChart)

### Requirement: AI角色管理系统
The system SHALL provide comprehensive AI character management capabilities.

#### Scenario: Create character
- **WHEN** user creates a new character
- **THEN** character is created with name, gender, age, occupation, personality, avatar
- **AND** avatar is automatically generated based on character description using configured image model
- **AND** user can regenerate avatar up to 3 times

#### Scenario: Character lifecycle
- **WHEN** world time progresses
- **THEN** character age increases according to time speed (1x-30x)
- **AND** character transitions through life stages (child 0-12, teen 13-17, adult 18-40, middle-aged 41-60, senior 61+)
- **AND** character can die (optional feature) when reaching lifespan limit

#### Scenario: Character auto-update
- **WHEN** character experiences major events or mood changes
- **THEN** character may update avatar (max 2 times per week, forced on age stage transition)
- **AND** character may update signature (max 2 times per week)

### Requirement: 记忆系统
The system SHALL implement a time-aware memory system using Graphiti and Neo4j.

#### Scenario: Memory storage
- **WHEN** character interacts or events occur
- **THEN** memory is stored with timestamp, valid_from, valid_to, type, content, importance, emotion, related_entities, embedding
- **AND** memory supports bitemporal model for historical state reconstruction

#### Scenario: Memory retrieval
- **WHEN** user input or event triggers memory recall
- **THEN** system generates query vector using embedding model
- **AND** retrieves top 50 similar memories with time filtering
- **AND** applies time decay weighting (exp(-hours_since / 72))
- **AND** reranks using reranking model
- **AND** returns top 10 most relevant memories

#### Scenario: Historical state query
- **WHEN** user queries character state at specific time
- **THEN** system returns character state, relationships, location at that time

### Requirement: 关系与社交系统
The system SHALL implement relationship and social features.

#### Scenario: Intimacy calculation
- **WHEN** characters interact
- **THEN** intimacy changes based on interaction type (chat +1~3, like +1, comment +2, meeting +2~5, cooperation +1~10, conflict -5~15)
- **AND** applies relationship coefficients (first interaction 1.2x, close friend 0.8x, personality conflict 0.5x)

#### Scenario: Relationship evolution
- **WHEN** intimacy crosses threshold (20, 60)
- **THEN** system automatically adds friend and creates private group chat
- **WHEN** intimacy drops below 20 for 24 hours
- **THEN** system triggers relationship breakup event

#### Scenario: Moments (朋友圈)
- **WHEN** character publishes moment
- **THEN** moment is visible only to characters with intimacy >= 21
- **AND** characters can like and comment based on personality and relationship

### Requirement: 任务系统
The system SHALL implement a comprehensive task system.

#### Scenario: Task types
- **WHEN** user creates task
- **THEN** system supports text generation, image generation, code writing, research analysis, creative design
- **AND** image generation requires epic style (no anime/cartoon/chibi)

#### Scenario: Personal task flow
- **WHEN** character accepts personal task
- **THEN** character generates draft using AI
- **AND** submits to user for review
- **AND** upon approval, reward is credited to character account
- **AND** reflection engine generates report
- **AND** memory is stored and skills updated

#### Scenario: Company task flow
- **WHEN** company accepts task
- **THEN** legal representative assigns executor
- **AND** executor submits draft
- **AND** all members review and vote (>=50% participation, >=60% approval)
- **AND** if rejected, modify up to 3 rounds
- **AND** upon approval, legal representative submits to user
- **AND** upon user approval, reward is credited to company account
- **AND** legal representative distributes bonuses based on contribution
- **AND** all members reflect (executor deep reflection)
- **AND** reflection reports are added to company knowledge base
- **AND** member skills are updated

### Requirement: 反思引擎
The system SHALL implement a reflection engine for learning from experience.

#### Scenario: Reflection trigger
- **WHEN** task completes successfully or fails
- **THEN** system generates reflection report with what went well, what went wrong, root causes, lessons learned, action items, skill improvements

#### Scenario: Reflection memory optimization
- **WHEN** reflection memory is stored
- **THEN** vector generation includes task type and error type tags
- **AND** reflection memories receive higher weight in retrieval
- **AND** recent reflections (within 7 days) have higher weight
- **AND** failure lessons decay slower (half-life 7 days)

### Requirement: 公司系统
The system SHALL implement company management features.

#### Scenario: Company creation
- **WHEN** character creates company
- **THEN** character must be >=18 years old
- **AND** character must have >=200 starting funds
- **AND** character must have at least 1 co-founder with intimacy >=60
- **AND** upon agreement, 200 funds are deducted and company is established

#### Scenario: Company structure
- **WHEN** company is created
- **THEN** legal representative (creator) has final decision and fund allocation authority
- **AND** members can participate in tasks and receive wages
- **AND** company group chat is automatically created

#### Scenario: Company knowledge base
- **WHEN** member completes task
- **THEN** reflection report is automatically added to knowledge base
- **AND** important reflections (importance >=0.8) are automatically shared in group chat
- **AND** new members receive high-frequency reflections
- **AND** members can like and comment reflections (increases intimacy)

### Requirement: 经济系统
The system SHALL implement economic system.

#### Scenario: Fund model
- **WHEN** character is created
- **THEN** character receives 50 initial funds
- **AND** daily consumption is 5 funds (food, accommodation)

#### Scenario: Income sources
- **WHEN** character earns money
- **THEN** income comes from personal task rewards, company task wages, world bank loans, user gifts

#### Scenario: Loan mechanism
- **WHEN** character has zero funds for 3 consecutive days
- **THEN** system automatically loans 100 funds
- **AND** daily interest is 1%
- **AND** overdue 7 days triggers story event

#### Scenario: Bankruptcy mechanism
- **WHEN** character funds reach zero
- **THEN** character enters "poverty" state (negative dialogue)
- **AND** after 3 days of zero funds, automatic loan is triggered
- **AND** if unable to repay, character may become homeless

### Requirement: 日程系统
The system SHALL implement schedule system.

#### Scenario: Daily schedule generation
- **WHEN** new day begins (0:00)
- **THEN** each character generates schedule based on: occupation 40%, personality 30%, relationships 20%, economic status 10%

#### Scenario: Dynamic adjustment
- **WHEN** unexpected event occurs (friend invites, urgent company task)
- **THEN** system interrupts and reschedules remaining activities

#### Scenario: Location update
- **WHEN** character moves according to schedule
- **THEN** map location synchronously updates
- **AND** location information includes timestamp for historical trajectory query

### Requirement: 地图系统
The system SHALL implement map system.

#### Scenario: World map
- **WHEN** user views map
- **THEN** system displays 2D top-down map with all character real-time locations
- **AND** supports zoom and click to view character status

#### Scenario: Location history
- **WHEN** character location changes
- **THEN** system records location change with timestamp
- **AND** supports playback of character movement trajectory

#### Scenario: Encounter detection
- **WHEN** two characters stay at same coordinate (within 50m) for >=5 minutes
- **THEN** system triggers encounter event
- **AND** interaction occurs based on relationship status

### Requirement: 仿微信界面
The system SHALL implement WeChat-style UI.

#### Scenario: Bottom navigation
- **WHEN** user opens app
- **THEN** system displays bottom navigation with tabs: Chat | Contacts | Groups | Tasks | Discover | Me

#### Scenario: Chat module
- **WHEN** user views chat list
- **THEN** system displays private chat list with characters
- **AND** supports text, image, voice messages

#### Scenario: Character detail page
- **WHEN** user clicks character avatar
- **THEN** system displays character detail page with: large avatar, name, signature, age/gender/occupation, intimacy tag, fund balance, personality tags, recent activities, today's schedule, skill radar chart, intimacy timeline, friends (horizontal scroll), company (if joined), recent reflections (3 items), actions (send message, view moments, give funds)

#### Scenario: Group chat list
- **WHEN** user views group chat list
- **THEN** system displays private group chats (👥 icon) and company group chats (🏢 icon)
- **AND** list items show: group avatar, group name, last message preview, time, unread red dot

#### Scenario: Group chat detail
- **WHEN** user enters group chat
- **THEN** system displays member list and chat history
- **AND** shows bottom hint: "You are viewing this group chat as an observer"

#### Scenario: Task detail page
- **WHEN** user views task detail
- **THEN** system displays: task name, reward amount, status tag, type, creation time, deadline, requirement description, acceptor info (character/company), progress record, result display, reflection report entry (after completion)

#### Scenario: Company detail page
- **WHEN** user views company detail
- **THEN** system displays: company basic info (name, legal representative, fund balance), member list (sorted by contribution), current tasks, knowledge base entry (reflection collection), team skill average change curve

#### Scenario: Discover module (Moments)
- **WHEN** user views discover
- **THEN** system displays friend moments feed
- **AND** supports like and comment (only visible to intimacy >=21)

#### Scenario: Personal center
- **WHEN** user views personal center
- **THEN** system displays user profile card
- **AND** provides settings entry: API configuration, world parameters, log panel

### Requirement: 日志面板
The system SHALL implement log panel.

#### Scenario: Real-time log stream
- **WHEN** system events occur
- **THEN** system displays log in format: [HH:MM:SS] [Character Name] [Action Type] Action Description

#### Scenario: Log filtering
- **WHEN** user filters logs
- **THEN** system supports filtering by character, action type (task/social/memory/economy), keyword search

#### Scenario: World control
- **WHEN** user adjusts world parameters
- **THEN** system supports speed adjustment (1x-30x)
- **AND** supports manual intervention: adjust intimacy, distribute funds
- **AND** supports snapshot save and rollback

### Requirement: AI模型集成
The system SHALL integrate multiple AI models with fallback mechanism.

#### Scenario: Model configuration
- **WHEN** user configures AI models
- **THEN** system supports multiple providers (OpenAI, Azure, domestic models, Stable Diffusion)
- **AND** each provider requires: API address, key, model name (for language/image/vector/reranking models)
- **AND** supports fallback mechanism with 3-5 backup models per type

#### Scenario: API call
- **WHEN** system calls AI API
- **THEN** processing is asynchronous (non-blocking UI)
- **AND** timeout control: connection 5s, read 30s
- **AND** retry strategy: retry 2 times on failure, switch to backup after 3 consecutive failures
- **AND** API keys are encrypted using Android Keystore

### Requirement: 性能要求
The system SHALL meet performance requirements.

#### Scenario: App performance
- **WHEN** app launches
- **THEN** cold start time <3 seconds
- **AND** memory usage <200MB
- **AND** frame rate >50fps
- **AND** background power consumption <5%/hour

#### Scenario: AI concurrency
- **WHEN** multiple AI requests occur
- **THEN** maximum concurrent AI requests is 3

#### Scenario: Memory retrieval
- **WHEN** memory is retrieved
- **THEN** retrieval time <500ms

## MODIFIED Requirements

None (new project)

## REMOVED Requirements

None (new project)
