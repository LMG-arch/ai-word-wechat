# AI社交世界 - Android应用

> 一款基于Jetpack Compose的仿微信风格AI社交模拟应用

## 📱 项目概述

AI社交世界是一个创新的Android应用，让用户创建和管理AI角色，观察他们在虚拟世界中自主生活、社交、工作、成长。每个AI角色拥有独立记忆、性格、职业和经济系统。

## 🎯 核心功能

### ✅ 已实现功能

- **角色管理** - 创建AI角色，定义性格、职业、年龄
- **生命周期** - 角色年龄自动增长，成长阶段变化
- **经济系统** - 初始资金、每日消耗、贷款机制
- **公司系统** - 创建公司、邀请成员、知识库
- **任务系统** - 个人/公司任务、投票机制
- **关系系统** - 亲密度计算、关系演变
- **日程系统** - 每日自动生成日程
- **反思引擎** - 任务完成后自动反思学习
- **记忆系统** - 向量检索、时间衰减
- **地图系统** - 位置追踪、相遇检测
- **日志面板** - 实时日志、世界控制

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| Kotlin | 开发语言 |
| Jetpack Compose | UI框架 |
| MVVM | 架构模式 |
| Clean Architecture | 分层架构 |
| Hilt | 依赖注入 |
| Room | 本地数据库 |
| Retrofit | 网络请求 |
| Kotlin Flow | 响应式数据流 |
| Coroutines | 异步处理 |

## 📂 项目结构

```
app/src/main/java/com/ai/socialworld/
├── data/              # 数据层
│   ├── local/         # 数据库、DAO
│   ├── model/         # 数据模型
│   ├── remote/        # 远程API
│   └── repository/    # 仓库实现
├── domain/            # 领域层
│   ├── repository/    # 仓库接口
│   └── service/       # 核心服务
├── presentation/      # 表现层
│   ├── chat/          # 聊天界面
│   ├── contacts/      # 通讯录
│   ├── tasks/         # 任务界面
│   ├── map/           # 地图界面
│   ├── logs/          # 日志面板
│   └── ...            # 其他界面
├── di/                # 依赖注入
└── util/              # 工具类
```

## 🚀 快速开始

### 环境要求

- Android Studio Hedgehog 或更高版本
- JDK 17+
- Android SDK 34
- minSdk 24

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/ai-social-world.git
```

2. **打开项目**
```
用 Android Studio 打开项目目录
```

3. **配置API**
```
运行应用后，进入 设置 -> API配置
配置以下模型：
- 语言模型（如 OpenAI GPT-4）
- 图像模型（如 DALL-E 3）
- 向量模型（如 text-embedding-ada-002）
```

4. **运行应用**
```
点击 Run 按钮或按 Shift+F10
```

## 📖 使用指南

### 创建AI角色

1. 进入 **通讯录** 页面
2. 点击右上角 **添加** 按钮
3. 填写角色信息（昵称、年龄、性别、职业、性格）
4. 点击 **生成头像**
5. 保存角色

### 启动世界

1. 进入 **日志面板** 页面
2. 点击 **开始** 按钮
3. 调整时间倍速（1x-30x）
4. 观察世界运行

### 执行任务

1. 进入 **任务** 页面
2. 选择可接取的任务
3. 指派执行人
4. 等待任务完成
5. 查看反思报告

### 创建公司

1. 年龄 ≥ 18岁
2. 资金 ≥ 200
3. 选择联合创始人（亲密度 ≥ 60）
4. 确认创建

## 🔧 核心服务

| 服务 | 说明 |
|------|------|
| WorldManager | 世界总管理器 |
| WorldTimeManager | 时间倍速、定时任务 |
| EconomyService | 经济系统 |
| CompanyService | 公司管理 |
| TaskExecutionService | 任务执行 |
| RelationshipEngine | 关系引擎 |
| ScheduleEngine | 日程引擎 |
| ReflectionEngine | 反思引擎 |
| MemoryRecallService | 记忆召回 |
| MapService | 地图服务 |
| LogService | 日志服务 |

## 📊 系统参数

### 经济参数
- 初始资金: 50
- 每日消耗: 5
- 贷款额度: 100
- 日息: 1%

### 关系参数
- 陌生人: 0-19
- 认识: 20-39
- 熟人: 40-59
- 好友: 60-79
- 密友: 80-100

### 任务参数
- 投票参与率: ≥50%
- 投票赞成率: ≥60%
- 最大修改次数: 3次

## 🔒 API配置支持

### 语言模型
- OpenAI GPT-4 / GPT-3.5-Turbo
- Anthropic Claude-3
- 其他兼容API

### 图像模型
- OpenAI DALL-E 3 / DALL-E 2
- Stability AI
- 其他兼容API

### 向量模型
- OpenAI text-embedding-ada-002
- 其他兼容API

## 📝 开发进度

详见 [PROGRESS_REPORT.md](PROGRESS_REPORT.md)

- 总体完成度: **80%**
- 核心功能完成度: **90%+**

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**开发者**: AI Social World Team  
**版本**: 1.0.0  
**更新时间**: 2026-03-24
