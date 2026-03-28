# AI 社交世界 (AIWeChat)

一款基于 Android 平台的社交模拟应用，采用微信风格的 UI 设计，核心玩法是创建一个由 AI 角色自主运行的虚拟世界。

## 🚀 快速开始

### Web 版（推荐用于测试）

**启动服务器:**
```bash
cd server
# Windows
start.bat
# 或手动启动
pip install -r requirements.txt
python main.py
```

**访问地址:**
- 电脑浏览器：http://localhost:8080
- 手机访问：http://你的电脑 IP:8080

**功能特性:**
- ✅ 完整的 RESTful API
- ✅ 数据持久化（JSON 文件）
- ✅ 手机端优化 UI
- ✅ 实时日志面板
- ✅ API 配置管理
- ✅ 后台年龄增长任务

```
app/
├── src/main/java/com/ai/wechat/
│   ├── data/
│   │   ├── model/          # 数据模型 (7 个实体类)
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
│   │   └── dao/            # 数据访问对象 (7 个 DAO)
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
│   │   ├── screens/        # 页面 (11 个)
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
│   ├── di/                 # 依赖注入模块 (5 个)
│   ├── AIWeChatApplication.kt
│   └── MainActivity.kt
├── src/test/               # 单元测试
└── src/androidTest/        # UI 测试
```

**统计**: 50+ Kotlin 文件，7200+ 行代码

## 核心功能

### 1. AI 角色系统 ✅
- **自定义创建**: 配置昵称、年龄、性别、职业、性格
- **智能头像生成**: 根据人设自动生成写实风格头像
- **生命周期管理**: 年龄增长、自主更新头像和签名
- **时间感知**: 支持时间倍速（1-30 倍速）
- **年龄段划分**: 儿童期、青少年期、青年期、中年期、老年期

### 2. 记忆系统（Graphiti + Neo4j） ✅
- **时间感知记忆**: 双时态模型，支持历史状态回溯
- **向量检索**: 基于向量相似度的记忆召回
- **时间衰减**: 近期记忆权重更高（半衰期 2.5 天）
- **重排优化**: 使用重排模型精排 Top 10
- **反思记忆**: 失败教训衰减更慢（半衰期 7 天）

### 3. 关系系统 ✅
- **亲密度**: 0-100 数值，随互动变化
- **关系状态**: 陌生人→认识→熟人→好友→密友
- **关系系数**: 陌生人加成 (1.2x)、密友边际递减 (0.8x)
- **阈值跨越**: 亲密度突破 20 自动创建私人群聊
- **每日衰减**: 超过 3 天不互动每日 -1

### 4. 任务系统 ✅
- **任务类型**: 文本生成、图像生成、代码编写、调研分析、创意设计
- **个人任务**: 角色独立接取，奖励全额归个人
- **公司任务**: 公司统一接取，成员协作完成
- **审核机制**: 用户确认成果后发放奖励
- **图像质量**: 史诗感、电影质感、8K 分辨率

### 5. 经济系统 ✅
- **初始资金**: 每个角色创建时 50 资金
- **日常消耗**: 每天 5 资金（吃饭、住宿）
- **贷款机制**: 资金归零连续 3 天自动贷款 100（日息 1%）
- **破产处理**: 无力偿还触发剧情事件
- **公司创建**: 年龄≥18 岁，资金≥200，至少 1 名联合创始人

### 6. 公司系统 ✅
- **组织结构**: 法人（群主）、联合创始人、普通成员
- **资金管理**: 任务奖励、工资发放、奖金分配
- **成员贡献**: 记录每个成员的贡献度
- **公司群聊**: 自动创建，全员参与任务讨论

### 7. 反思引擎 ✅
- **触发时机**: 任务成功/失败、审核不通过
- **经验提取**: 自动总结教训和技能提升
- **技能系统**: 需求理解、执行效率、史诗感把控等维度
- **记忆存储**: 反思记忆存入个人记忆库

## 技术架构

### UI 层
- **Jetpack Compose**: 声明式 UI 框架
- **Material 3**: 现代化设计规范
- **Navigation Compose**: 页面导航
- **Coil**: 图片加载

### 业务逻辑层
- **Dagger Hilt**: 依赖注入
- **Kotlin Coroutines**: 异步编程
- **Flow**: 响应式数据流
- **WorkManager**: 后台定时任务

### 数据层
- **Room**: SQLite 本地缓存
- **Neo4j Driver**: 图数据库连接
- **Graphiti**: 时间知识图谱引擎
- **Gson**: JSON 序列化

### AI 服务层
- **Retrofit + OkHttp**: 网络请求
- **多服务商支持**: OpenAI、Azure、百度文心、阿里云、Stability AI 等
- **备用机制**: 主模型失败自动切换备用
- **超时控制**: 连接 5 秒，读取 30 秒

## 开发计划

### V1.0 基础版 ✅
- [x] 项目初始化
- [x] 基础架构搭建 (Dagger Hilt, Room, Retrofit)
- [x] 仿微信 UI 框架 (Jetpack Compose, Material 3)
- [x] AI 服务集成 (多模型支持，备用机制)

### V2.0 社交版 ✅
- [x] 多角色交互 (CharacterManager, 通讯录)
- [x] 亲密度系统完善 (RelationshipEngine, 阈值跨越)
- [ ] 朋友圈功能

### V3.0 记忆版 ✅
- [x] Graphiti 时间记忆 (双时态模型)
- [x] 向量检索优化 (时间衰减，重排模型)
- [x] 私人群聊 (GroupChat, 自动创建)

### V4.0 经济版 ✅
- [x] 资金系统完善 (转账，日常消耗)
- [x] 任务系统完善 (个人/公司任务，审核机制)
- [x] 反思机制 (ReflectionEngine, 技能系统)

### V5.0 生态版 🔄
- [x] 公司系统 (创建，成员管理，资金分配)
- [ ] 知识库 (反思报告共享)
- [x] 地图系统 (基础框架)

### 待完成功能
- [ ] 朋友圈发布与互动
- [ ] 公司知识库与反思共享
- [ ] 地图角色实时位置显示
- [ ] 日程系统自动生成
- [ ] 角色死亡机制
- [ ] ViewModel 与 UI 完全对接
- [ ] API 配置持久化

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

## 运行方式

### 后端服务 + 手机 UI（推荐）

完整的测试环境，数据存储在本地 JSON 文件。

**启动服务器:**
```bash
cd server
# Windows
start.bat
# 或手动启动
pip install -r requirements.txt
python main.py
```

**访问地址:**
- 电脑浏览器：http://localhost:8080
- 手机访问：http://你的电脑 IP:8080

**功能特性:**
- ✅ 完整的 RESTful API
- ✅ 数据持久化（JSON 文件）
- ✅ 手机端优化 UI
- ✅ 实时日志面板
- ✅ 后台年龄增长任务
- ✅ 支持多设备访问

### Web 测试版 (离线版)

无需安装，直接在浏览器运行。

1. **直接打开**
   ```
   双击 web/index.html
   ```

2. **或使用 HTTP 服务器**
   ```bash
   cd web
   python -m http.server 8080
   # 访问 http://localhost:8080
   ```

**Web 版功能**:
- ✅ 角色创建与管理
- ✅ 聊天对话（模拟 AI）
- ✅ 通讯录
- ✅ 数据持久化（LocalStorage）
- ✅ 实时日志面板
- ⚠️ AI 回复为模拟文本
- ❌ 暂无真实 AI 集成

### Android 版本

**环境要求**
- Android Studio Hedgehog (2023.1.1) 或更高版本
- JDK 17 或 JDK 21（Java 25 不兼容）
- Android SDK 35

### 构建命令
```bash
./gradlew assembleDebug
```

---

## ⚙️ API 配置指南

### 支持的模型类型

| 类型 | 用途 | 示例 API 端点 |
|------|------|--------------|
| **语言模型 (LLM)** | 对话/文本生成 | `/v1/chat/completions` |
| **图像模型** | 绘画/图片生成 | `/v1/images/generations` |
| **向量模型** | 嵌入/向量检索 | `/v1/embeddings` |
| **重排模型** | 记忆精排 | `/reranker` |

### 常用服务商配置

#### OpenAI
- **语言模型**: `https://api.openai.com/v1/chat/completions`
- **图像模型**: `https://api.openai.com/v1/images/generations`
- **向量模型**: `https://api.openai.com/v1/embeddings`
- **模型名称**: `gpt-4`, `gpt-3.5-turbo`, `dall-e-3`

#### Azure OpenAI
- **语言模型**: `https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview`
- **图像模型**: `https://{resource}.openai.azure.com/openai/deployments/{deployment}/images/generations?api-version=2024-02-15-preview`
- **向量模型**: `https://{resource}.openai.azure.com/openai/deployments/{deployment}/embeddings?api-version=2024-02-15-preview`

#### 百度文心
- **语言模型**: `https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions`
- **图像模型**: `https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/sd_xl`
- **向量模型**: `https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/embedding-v1`
- **重排模型**: `https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/reranker/reranker`

#### 阿里云通义
- **语言模型**: `https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation`
- **图像模型**: `https://dashscope.aliyuncs.com/api/v1/services/aigc/text-to-image/generation`
- **向量模型**: `https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding`

#### Stability AI
- **图像模型**: `https://api.stability.ai/v2beta/stable-image/generate/core`
- **模型名称**: `stable-diffusion-xl`, `stable-image-core`

#### 本地部署 (Ollama 等)
- **语言模型**: `http://localhost:11434/v1/chat/completions`
- **图像模型**: `http://localhost:11434/v1/images/generations`
- **向量模型**: `http://localhost:11434/v1/embeddings`

### 运行
在 Android Studio 中点击 Run 按钮，或使用：
```bash
./gradlew installDebug
```

## 许可证

MIT License

## 项目仓库

https://github.com/LMG-arch/ai-word-wechat.git
