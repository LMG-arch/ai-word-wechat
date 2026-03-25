# AI 社交世界 - Android 项目结构

## 项目概述
一个仿微信界面的AI角色扮演与社交应用，支持：
- 创建和管理AI角色
- 与AI角色聊天
- 任务系统（发布、接取、完成）
- 朋友圈功能
- 群组聊天

## 技术栈
- **语言**: Kotlin
- **UI框架**: Jetpack Compose
- **架构**: MVVM + Clean Architecture
- **依赖注入**: Hilt
- **本地存储**: Room
- **网络**: Retrofit + OkHttp
- **图片加载**: Coil
- **图表**: MPAndroidChart

## 项目结构

```
app/src/main/java/com/ai/socialworld/
├── data/
│   ├── local/           # 本地数据源
│   │   ├── AppDatabase.kt
│   │   ├── CharacterDao.kt
│   │   ├── TaskDao.kt
│   │   └── Converters.kt
│   ├── model/           # 数据模型
│   │   ├── Character.kt
│   │   ├── Task.kt
│   │   └── Message.kt
│   └── remote/          # 远程数据源
│       └── (API接口)
├── domain/
│   ├── repository/      # 仓库接口实现
│   │   ├── CharacterRepository.kt
│   │   └── TaskRepository.kt
│   └── usecase/         # 用例（可选）
├── di/                  # 依赖注入模块
│   ├── DatabaseModule.kt
│   └── RepositoryModule.kt
├── presentation/        # UI层
│   ├── main/
│   │   └── MainApp.kt
│   ├── navigation/
│   │   └── Screen.kt
│   ├── components/
│   │   ├── BottomNavigationBar.kt
│   │   └── CommonComponents.kt
│   ├── chat/
│   │   ├── ChatScreen.kt
│   │   ├── ChatListViewModel.kt
│   │   └── ChatDetailScreen.kt
│   ├── contacts/
│   │   ├── ContactsScreen.kt
│   │   └── ContactsViewModel.kt
│   ├── character/
│   │   ├── CreateCharacterScreen.kt
│   │   ├── CreateCharacterViewModel.kt
│   │   ├── CharacterDetailScreen.kt
│   │   └── CharacterDetailViewModel.kt
│   ├── groups/
│   │   ├── GroupsScreen.kt
│   │   └── GroupsViewModel.kt
│   ├── tasks/
│   │   ├── TasksScreen.kt
│   │   └── TasksViewModel.kt
│   ├── discover/
│   │   ├── DiscoverScreen.kt
│   │   ├── MomentsScreen.kt
│   │   └── MomentsViewModel.kt
│   ├── profile/
│   │   └── ProfileScreen.kt
│   └── settings/
│       ├── ApiConfigScreen.kt
│       └── ApiConfigViewModel.kt
└── MainActivity.kt
```

## 核心功能模块

### 1. 聊天模块 (Chat)
- **ChatScreen**: 聊天列表（仿微信首页）
- **ChatDetailScreen**: 聊天详情页
- **ChatListViewModel**: 聊天列表逻辑

### 2. 通讯录模块 (Contacts)
- **ContactsScreen**: 角色列表
- **CreateCharacterScreen**: 创建新角色
- **CharacterDetailScreen**: 角色详情页

### 3. 群组模块 (Groups)
- **GroupsScreen**: 群组列表
- 支持创建群组、群聊功能

### 4. 任务模块 (Tasks)
- **TasksScreen**: 任务中心
- 任务状态：待接取、进行中、已完成
- 任务难度：简单、中等、困难、史诗
- 任务奖励系统

### 5. 发现模块 (Discover)
- **DiscoverScreen**: 发现页
- **MomentsScreen**: 朋友圈
- 支持发布动态、点赞、评论

### 6. 个人中心 (Profile)
- **ProfileScreen**: 个人中心
- **ApiConfigScreen**: API配置
- 支持配置AI模型和API密钥

## 数据模型

### Character (角色)
```kotlin
data class Character(
    val id: Long,
    val name: String,
    val age: Int,
    val gender: Gender,
    val occupation: String,
    val personality: String,
    val growthStage: GrowthStage,
    val money: Int,
    val avatarUrl: String?
)
```

### Task (任务)
```kotlin
data class Task(
    val id: Long,
    val title: String,
    val description: String,
    val type: TaskType,
    val difficulty: TaskDifficulty,
    val reward: Int,
    val status: TaskStatus,
    val assigneeId: Long?
)
```

## 导航结构

底部导航栏有6个主要页面：
1. **聊天** - 聊天列表
2. **通讯录** - 角色列表
3. **群聊** - 群组列表
4. **任务** - 任务中心
5. **发现** - 朋友圈等
6. **我** - 个人中心

## 待实现功能

1. **AI对话集成**
   - 接入OpenAI/Claude API
   - 实现角色记忆功能
   - 支持多轮对话

2. **任务系统完善**
   - 任务自动分配算法
   - 任务完成评估
   - 奖励发放机制

3. **社交功能**
   - 朋友圈发布图片
   - 群聊功能
   - 角色关系系统

4. **成长系统**
   - 技能升级
   - 经验值系统
   - 成长阶段进阶

5. **数据持久化**
   - 聊天记录存储
   - 朋友圈数据
   - 用户偏好设置

## 构建和运行

1. 确保已安装 Android Studio Hedgehog 或更新版本
2. 同步 Gradle 文件
3. 运行应用

```bash
./gradlew assembleDebug
```

## 注意事项

1. 部分功能使用模拟数据，需要连接真实数据库
2. API配置需要有效的API密钥
3. 图片加载需要网络权限
