# AI 社交世界 (AIWeChat)

一款基于 Android 平台的社交模拟应用，采用微信风格的 UI 设计，核心玩法是创建一个由 AI 角色自主运行的虚拟世界。

## 项目结构

```
app/
├── src/main/java/com/ai/wechat/
│   ├── data/
│   │   ├── model/          # 数据模型
│   │   │   ├── Character.kt
│   │   │   ├── ApiConfig.kt
│   │   │   ├── ChatMessage.kt
│   │   │   ├── Company.kt
│   │   │   ├── Task.kt
│   │   │   ├── GroupChat.kt
│   │   │   └── MemoryCache.kt
│   │   └── memory/         # 记忆系统
│   │       ├── Memory.kt
│   │       ├── MemoryEngine.kt
│   │       └── impl/
│   │           └── GraphitiMemoryEngine.kt
│   ├── db/
│   │   ├── AppDatabase.kt
│   │   └── dao/            # 数据访问对象
│   ├── network/            # 网络层
│   │   ├── AiApiService.kt
│   │   └── NetworkConfig.kt
│   ├── service/            # 业务逻辑层
│   │   ├── AiWeChatService.kt
│   │   ├── CharacterManager.kt
│   │   ├── RelationshipEngine.kt
│   │   ├── EconomyService.kt
│   │   ├── TaskSystem.kt
│   │   └── ReflectionEngine.kt
│   ├── ui/
│   │   ├── screens/        # 页面
│   │   │   ├── chat/
│   │   │   ├── contacts/
│   │   │   ├── groups/
│   │   │   ├── tasks/
│   │   │   ├── discover/
│   │   │   ├── mine/
│   │   │   ├── character/
│   │   │   ├── map/
│   │   │   ├── log/
│   │   │   └── settings/
│   │   ├── navigation/     # 导航
│   │   ├── theme/          # 主题
│   │   └── viewmodel/      # ViewModel
│   ├── worker/             # 后台任务
│   ├── di/                 # 依赖注入模块
│   ├── AIWeChatApplication.kt
│   └── MainActivity.kt
```

## 核心功能

### 1. AI 角色系统
- **自定义创建**: 配置昵称、年龄、性别、职业、性格
- **智能头像生成**: 根据人设自动生成写实风格头像
- **生命周期管理**: 年龄增长、自主更新头像和签名
- **时间感知**: 支持时间倍速（1-30 倍速）

### 2. 记忆系统（Graphiti + Neo4j）
- **时间感知记忆**: 双时态模型，支持历史状态回溯
- **向量检索**: 基于向量相似度的记忆召回
- **时间衰减**: 近期记忆权重更高
- **重排优化**: 使用重排模型精排 Top 10

### 3. 关系系统
- **亲密度**: 0-100 数值，随互动变化
- **关系状态**: 陌生人→认识→熟人→好友→密友
- **朋友圈机制**: 仅对亲密度≥21 的角色可见
- **私人群聊**: 亲密度突破 20 自动创建

### 4. 任务系统
- **任务类型**: 文本生成、图像生成、代码编写、调研分析、创意设计
- **个人任务**: 角色独立接取，奖励全额归个人
- **公司任务**: 公司统一接取，成员协作完成
- **审核机制**: 用户确认成果后发放奖励

### 5. 经济系统
- **初始资金**: 每个角色创建时 50 资金
- **日常消耗**: 每天 5 资金
- **贷款机制**: 资金归零连续 3 天自动贷款 100（日息 1%）
- **破产处理**: 无力偿还触发剧情事件

### 6. 公司系统
- **创建条件**: 年龄≥18 岁，资金≥200，至少 1 名联合创始人
- **公司结构**: 法人、联合创始人、普通成员
- **知识库**: 成员反思报告自动加入，全员共享

### 7. 反思引擎
- **触发时机**: 任务成功/失败、审核不通过
- **经验提取**: 自动总结教训和技能提升
- **技能系统**: 需求理解、执行效率等维度

## 技术架构

### UI 层
- **Jetpack Compose**: 声明式 UI 框架
- **Material 3**: 现代化设计规范
- **Navigation Compose**: 页面导航

### 业务逻辑层
- **Dagger Hilt**: 依赖注入
- **Kotlin Coroutines**: 异步编程
- **WorkManager**: 后台定时任务

### 数据层
- **Room**: SQLite 本地缓存
- **Neo4j Driver**: 图数据库连接
- **Graphiti**: 时间知识图谱引擎

### AI 服务层
- **Retrofit + OkHttp**: 网络请求
- **多服务商支持**: OpenAI、Azure、百度文心等
- **备用机制**: 主模型失败自动切换备用

## 开发计划

### V1.0 基础版（已完成）
- [x] 项目初始化
- [x] 基础架构搭建
- [x] 仿微信 UI 框架
- [x] AI 服务集成

### V2.0 社交版（进行中）
- [ ] 多角色交互
- [ ] 亲密度系统完善
- [ ] 朋友圈功能

### V3.0 记忆版
- [ ] Graphiti 时间记忆
- [ ] 向量检索优化
- [ ] 私人群聊

### V4.0 经济版
- [ ] 资金系统完善
- [ ] 任务系统完善
- [ ] 反思机制

### V5.0 生态版
- [ ] 公司系统
- [ ] 知识库
- [ ] 地图系统

## 配置说明

### API 配置
在设置页面配置 AI 模型：
1. 语言模型（对话、文本生成）
2. 图像模型（头像、任务图像）
3. 向量模型（记忆检索）
4. 重排模型（记忆精排）

### Neo4j 配置
环境变量：
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

## 构建运行

### 环境要求
- Android Studio Hedgehog 或更高版本
- JDK 17
- Android SDK 34

### 构建命令
```bash
./gradlew assembleDebug
```

### 运行
在 Android Studio 中点击 Run 按钮，或使用：
```bash
./gradlew installDebug
```

## 许可证

MIT License

## 项目仓库

https://github.com/LMG-arch/ai-word-wechat.git
