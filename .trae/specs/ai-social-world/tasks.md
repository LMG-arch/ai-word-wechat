# Tasks

## Phase 1: 项目初始化

- [ ] Task 1.1: 创建Android项目结构
  - [ ] SubTask 1.1.1: 创建Kotlin Android项目，设置最低SDK为24
  - [ ] SubTask 1.1.2: 配置build.gradle，添加Jetpack Compose依赖
  - [ ] SubTask 1.1.3: 配置Dagger Hilt依赖注入
  - [ ] SubTask 1.1.4: 配置Room SQLite依赖
  - [ ] SubTask 1.1.5: 配置Retrofit + OkHttp网络依赖
  - [ ] SubTask 1.1.6: 配置Coil图片加载依赖
  - [ ] SubTask 1.1.7: 配置MPAndroidChart图表依赖
  - [ ] SubTask 1.1.8: 配置Kotlin Coroutines + Flow
- [ ] Task 1.2: 配置Neo4j连接
  - [ ] SubTask 1.2.1: 添加Neo4j Java驱动依赖
  - [ ] SubTask 1.2.2: 配置Graphiti引擎
  - [ ] SubTask 1.2.3: 创建Neo4j连接管理类
- [ ] Task 1.3: 创建项目基础架构
  - [ ] SubTask 1.3.1: 创建数据层（Repository模式）
  - [ ] SubTask 1.3.2: 创建业务逻辑层（UseCase模式）
  - [ ] SubTask 1.3.3: 创建UI层（ViewModel + Compose）
  - [ ] SubTask 1.3.4: 创建依赖注入模块

## Phase 2: AI角色管理系统

- [ ] Task 2.1: 实现角色数据模型
  - [ ] SubTask 2.1.1: 创建Character实体类（id, name, age, gender, occupation, personality, money, createdAt）
  - [ ] SubTask 2.1.2: 创建Character DAO（Room数据库）
  - [ ] SubTask 2.1.3: 创建Character Repository
- [x] Task 2.2: 实现角色创建功能
  - [ ] SubTask 2.2.1: 创建角色创建UI页面
  - [ ] SubTask 2.2.2: 实现基础信息输入（昵称、性别、年龄、职业）
  - [ ] SubTask 2.2.3: 实现性格设定输入（手动输入或AI生成）
  - [ ] SubTask 2.2.4: 实现声音设定选择
  - [ ] SubTask 2.2.5: 集成图像模型API，实现智能头像生成
  - [ ] SubTask 2.2.6: 实现多次生成供用户选择（最多3次）
- [ ] Task 2.3: 实现API配置体系
  - [ ] SubTask 2.3.1: 创建API配置数据模型（语言模型/图像模型/向量模型/重排模型）
  - [ ] SubTask 2.3.2: 创建API配置管理类
  - [ ] SubTask 2.3.3: 实现多服务商切换功能
  - [ ] SubTask 2.3.4: 实现备用机制（3-5个备用模型）
  - [ ] SubTask 2.3.5: 实现API密钥加密存储（Android Keystore）
- [ ] Task 2.4: 实现角色生命周期系统
  - [ ] SubTask 2.4.1: 创建世界时间管理器（支持1-30倍速）
  - [ ] SubTask 2.4.2: 实现角色年龄自动增长
  - [ ] SubTask 2.4.3: 实现成长阶段划分（儿童/青少年/青年/中年/老年）
  - [ ] SubTask 2.4.4: 实现年龄影响（对话风格、职业限制、头像更新）
  - [ ] SubTask 2.4.5: 实现角色死亡机制（可选开关）
- [ ] Task 2.5: 实现角色自主更新机制
  - [ ] SubTask 2.5.1: 实现头像更换规则（每周最多2次，年龄段跨越强制更新）
  - [ ] SubTask 2.5.2: 实现个性签名更新（每周最多2次）
  - [ ] SubTask 2.5.3: 集成图像模型生成新头像

## Phase 3: 记忆系统

- [ ] Task 3.1: 实现Neo4j图数据库集成
  - [ ] SubTask 3.1.1: 创建Neo4j节点类型（Character, Company, Task, Location, Reflection）
  - [ ] SubTask 3.1.2: 创建Neo4j关系类型（FRIEND\_WITH, WORK\_AT, POSTED, LOCATED\_AT, HAS\_MEMORY, PARTICIPATED\_IN）
  - [ ] SubTask 3.1.3: 实现双时态模型（valid\_from, valid\_to）
  - [ ] SubTask 3.1.4: 创建记忆数据模型
- [ ] Task 3.2: 实现记忆存储功能
  - [ ] SubTask 3.2.1: 实现记忆存储API
  - [ ] SubTask 3.2.2: 实现时间戳存储
  - [ ] SubTask 3.2.3: 实现相关实体记录
- [ ] Task 3.3: 实现记忆召回流程
  - [ ] SubTask 3.3.1: 集成向量模型API
  - [ ] SubTask 3.3.2: 实现Query向量生成
  - [ ] SubTask 3.3.3: 实现Top 50相似记忆检索（带时间范围过滤）
  - [ ] SubTask 3.3.4: 实现时间衰减加权（exp(-hours\_since / 72)）
  - [ ] SubTask 3.3.5: 集成重排模型API
  - [ ] SubTask 3.3.6: 实现重排排序，返回Top 10
  - [ ] SubTask 3.3.7: 实现上下文注入
- [ ] Task 3.4: 实现历史状态查询
  - [ ] SubTask 3.4.1: 实现任意时间点角色状态查询
  - [ ] SubTask 3.4.2: 实现关系亲密度历史查询
  - [ ] SubTask 3.4.3: 实现位置历史查询

## Phase 4: 关系与社交系统

- [ ] Task 4.1: 实现亲密度系统
  - [ ] SubTask 4.1.1: 创建亲密度数据模型（0-100）
  - [ ] SubTask 4.1.2: 实现亲密度变化计算（聊天+1~~3，点赞+1，评论+2，见面+2~~5，合作+1~~10，冲突-5~~15，长期不互动-1）
  - [ ] SubTask 4.1.3: 实现关系系数（初次1.2倍，密友0.8倍，性格冲突0.5倍）
- [ ] Task 4.2: 实现关系状态阈值
  - [ ] SubTask 4.2.1: 实现关系状态判断（0-20陌生人，21-40认识，41-60熟人，61-80好友，81-100密友）
  - [ ] SubTask 4.2.2: 实现权限控制（朋友圈可见性、私聊权限）
- [ ] Task 4.3: 实现关系演变流程
  - [ ] SubTask 4.3.1: 实现亲密度突破20自动加好友
  - [ ] SubTask 4.3.2: 实现私人群聊创建
  - [ ] SubTask 4.3.3: 实现亲密度突破60增加互动频率
  - [ ] SubTask 4.3.4: 实现跌破20持续24小时触发关系破裂
  - [ ] SubTask 4.3.5: 实现删除好友和群聊解散
- [ ] Task 4.4: 实现朋友圈机制
  - [ ] SubTask 4.4.1: 创建朋友圈数据模型
  - [ ] SubTask 4.4.2: 实现朋友圈发布触发（重要日程、情绪波动、随机）
  - [ ] SubTask 4.4.3: 实现可见性控制（仅亲密度≥21可见）
  - [ ] SubTask 4.4.4: 实现点赞功能（AI根据人设和关系生成）
  - [ ] SubTask 4.4.5: 实现评论功能（AI根据人设和关系生成）
  - [ ] SubTask 4.4.6: 实现时间线倒序排列
- [ ] Task 4.5: 实现私人群聊
  - [ ] SubTask 4.5.1: 创建群聊数据模型
  - [ ] SubTask 4.5.2: 实现群聊创建时机（亲密度首次突破20）
  - [ ] SubTask 4.5.3: 实现用户权限（可查看，不可发送）
  - [ ] SubTask 4.5.4: 实现群聊消亡机制（关系破裂时可选解散）

## Phase 5: 任务系统

- [ ] Task 5.1: 实现任务数据模型
  - [ ] SubTask 5.1.1: 创建Task实体类（id, title, description, type, reward, status）
  - [ ] SubTask 5.1.2: 创建Task DAO
  - [ ] SubTask 5.1.3: 创建Task Repository
- [ ] Task 5.2: 实现任务类型
  - [ ] SubTask 5.2.1: 实现文本生成任务
  - [ ] SubTask 5.2.2: 实现图像生成任务（史诗感、非二次元）
  - [ ] SubTask 5.2.3: 实现代码编写任务
  - [ ] SubTask 5.2.4: 实现调研分析任务
  - [ ] SubTask 5.2.5: 实现创意设计任务
- [ ] Task 5.3: 实现个人任务流程
  - [ ] SubTask 5.3.1: 实现角色接取任务
  - [ ] SubTask 5.3.2: 集成AI能力生成初稿
  - [ ] SubTask 5.3.3: 实现提交用户审核
  - [ ] SubTask 5.3.4: 实现用户确认发放奖励
  - [ ] SubTask 5.3.5: 集成反思引擎生成报告
  - [ ] SubTask 5.3.6: 实现存入个人记忆库
  - [ ] SubTask 5.3.7: 实现技能更新
- [ ] Task 5.4: 实现公司任务流程
  - [ ] SubTask 5.4.1: 实现公司接取任务
  - [ ] SubTask 5.4.2: 实现法人指派执行人
  - [ ] SubTask 5.4.3: 实现执行人提交初稿
  - [ ] SubTask 5.4.4: 实现全员审核投票（≥50%参与，≥60%赞成）
  - [ ] SubTask 5.4.5: 实现不通过修改（最多3轮）
  - [ ] SubTask 5.4.6: 实现法人提交用户
  - [ ] SubTask 5.4.7: 实现用户确认发放奖励到公司账户
  - [ ] SubTask 5.4.8: 实现法人分配奖金（按贡献度）
  - [ ] SubTask 5.4.9: 实现触发全员反思
  - [ ] SubTask 5.4.10: 实现反思报告加入公司知识库
  - [ ] SubTask 5.4.11: 实现更新各成员技能
- [ ] Task 5.5: 实现任务管理器
  - [ ] SubTask 5.5.1: 创建任务管理器UI
  - [ ] SubTask 5.5.2: 实现任务列表分类（可接取、进行中、已完成）
  - [ ] SubTask 5.5.3: 实现任务创建（用户自定义，奖励100-10000）
  - [ ] SubTask 5.5.4: 实现AI自动生成任务（每日0点生成3-5个，奖励100-1000）
- [ ] Task 5.6: 实现图像生成质量要求
  - [ ] SubTask 5.6.1: 实现禁止风格检测（二次元、卡通、Q版）
  - [ ] SubTask 5.6.2: 实现要求风格（史诗感、宏大构图、电影质感、8K、光影追踪、细节丰富）
  - [ ] SubTask 5.6.3: 实现负面提示词（卡通,二次元,动漫,Q版,简笔画,低分辨率,模糊）

## Phase 6: 反思引擎

- [ ] Task 6.1: 实现反思触发时机
  - [ ] SubTask 6.1.1: 实现任务成功完成触发
  - [ ] SubTask 6.1.2: 实现任务失败触发
  - [ ] SubTask 6.1.3: 实现审核不通过记录
- [ ] Task 6.2: 实现反思流程
  - [ ] SubTask 6.2.1: 实现收集过程数据
  - [ ] SubTask 6.2.2: 集成AI生成反思报告
  - [ ] SubTask 6.2.3: 实现提取经验教训
  - [ ] SubTask 6.2.4: 实现存为反思记忆（带时间戳）
  - [ ] SubTask 6.2.5: 实现更新技能库
  - [ ] SubTask 6.2.6: 实现影响未来行为
- [ ] Task 6.3: 实现反思报告结构
  - [ ] SubTask 6.3.1: 创建反思报告数据模型（task\_id, task\_name, completion\_time, success, what\_went\_well, what\_went\_wrong, root\_causes, lessons\_learned, action\_items, skill\_improvements）
  - [ ] SubTask 6.3.2: 实现成功反思提示词模板
  - [ ] SubTask 6.3.3: 实现失败反思提示词模板
- [ ] Task 6.4: 实现反思记忆召回优化
  - [ ] SubTask 6.4.1: 实现向量检索时加入任务类型和错误类型标签
  - [ ] SubTask 6.4.2: 实现重排加权（反思记忆更高权重）
  - [ ] SubTask 6.4.3: 实现时效性（近期反思7天内权重更高）
  - [ ] SubTask 6.4.4: 实现失败教训衰减更慢（半衰期7天）
- [ ] Task 6.5: 实现技能系统
  - [ ] SubTask 6.5.1: 创建技能维度（需求理解、史诗感把控、细节丰富度、风格准确性、修改效率、团队协作）
  - [ ] SubTask 6.5.2: 实现技能更新规则（成功+1~~5，失败+2~~8，同类任务收益递减）

## Phase 7: 公司系统

- [ ] Task 7.1: 实现公司数据模型
  - [ ] SubTask 7.1.1: 创建Company实体类（id, name, founderId, money, createdAt）
  - [ ] SubTask 7.1.2: 创建Company DAO
  - [ ] SubTask 7.1.3: 创建Company Repository
- [ ] Task 7.2: 实现公司创建
  - [ ] SubTask 7.2.1: 实现创建条件检查（年龄≥18，资金≥200，至少1名联合创始人亲密度≥60）
  - [ ] SubTask 7.2.2: 实现角色A发起邀请流程
  - [ ] SubTask 7.2.3: 实现双方同意流程
  - [ ] SubTask 7.2.4: 实现扣除200资金
  - [ ] SubTask 7.2.5: 实现公司成立
- [ ] Task 7.3: 实现公司结构
  - [ ] SubTask 7.3.1: 实现法人权限（最终决策权、资金分配权）
  - [ ] SubTask 7.3.2: 实现成员管理（参与任务、获得工资）
  - [ ] SubTask 7.3.3: 实现公司群聊自动创建
- [ ] Task 7.4: 实现公司知识库
  - [ ] SubTask 7.4.1: 实现反思报告自动加入知识库
  - [ ] SubTask 7.4.2: 实现重要反思自动分享（重要性≥0.8）
  - [ ] SubTask 7.4.3: 实现新成员自动推送高频反思
  - [ ] SubTask 7.4.4: 实现成员点赞评论反思（增强亲密度）
- [ ] Task 7.5: 实现公司资金管理
  - [ ] SubTask 7.5.1: 实现收入记录（完成任务奖励）
  - [ ] SubTask 7.5.2: 实现支出记录（发放工资、日常消耗）
  - [ ] SubTask 7.5.3: 实现奖金分配（法人按贡献度分配）

## Phase 8: 经济系统

- [ ] Task 8.1: 实现资金模型
  - [ ] SubTask 8.1.1: 实现初始资金（每个角色50资金）
  - [ ] SubTask 8.1.2: 实现日常消耗（每天5资金）
  - [ ] SubTask 8.1.3: 实现收入来源记录
- [ ] Task 8.2: 实现贷款机制
  - [ ] SubTask 8.2.1: 实现触发条件检查（资金归零连续3天）
  - [ ] SubTask 8.2.2: 实现贷款额度（100资金）
  - [ ] SubTask 8.2.3: 实现利息计算（日息1%）
  - [ ] SubTask 8.2.4: 实现逾期触发（7天触发剧情事件）
- [ ] Task 8.3: 实现破产机制
  - [ ] SubTask 8.3.1: 实现贫困状态（资金归零，对话消极）
  - [ ] SubTask 8.3.2: 实现自动贷款（连续3天资金为0）
  - [ ] SubTask 8.3.3: 实现无力偿还流落街头

## Phase 9: 日程系统

- [ ] Task 9.1: 实现日程数据模型
  - [ ] SubTask 9.1.1: 创建Schedule实体类
  - [ ] SubTask 9.1.2: 创建Schedule DAO
  - [ ] SubTask 9.1.3: 创建Schedule Repository
- [ ] Task 9.2: 实现每日日程生成
  - [ ] SubTask 9.2.1: 实现每日0点触发
  - [ ] SubTask 9.2.2: 实现权重计算（职业40%，性格30%，关系20%，经济10%）
  - [ ] SubTask 9.2.3: 实现日程格式（时间-地点-活动-可能遇到的人）
- [ ] Task 9.3: 实现动态调整
  - [ ] SubTask 9.3.1: 实现突发事件打断（朋友约饭、公司紧急任务）
  - [ ] SubTask 9.3.2: 实现实时重排剩余日程
- [ ] Task 9.4: 实现位置更新
  - [ ] SubTask 9.4.1: 实现角色按日程移动
  - [ ] SubTask 9.4.2: 实现地图位置同步更新
  - [ ] SubTask 9.4.3: 实现位置信息时间戳

## Phase 10: 地图系统

- [ ] Task 10.1: 实现世界地图
  - [ ] SubTask 10.1.1: 创建2D俯视角地图UI
  - [ ] SubTask 10.1.2: 实现所有角色实时位置标注
  - [ ] SubTask 10.1.3: 实现缩放功能
  - [ ] SubTask 10.1.4: 实现点击查看角色状态
- [ ] Task 10.2: 实现位置历史
  - [ ] SubTask 10.2.1: 实现位置变化记录（带时间戳）
  - [ ] SubTask 10.2.2: 实现历史轨迹回放
- [ ] Task 10.3: 实现相遇检测
  - [ ] SubTask 10.3.1: 实现坐标判断（误差≤50米）
  - [ ] SubTask 10.3.2: 实现停留时间判断（≥5分钟）
  - [ ] SubTask 10.3.3: 实现相遇事件触发
  - [ ] SubTask 10.3.4: 实现根据关系状态自动交互

## Phase 11: 仿微信界面

- [ ] Task 11.1: 实现底部导航栏
  - [ ] SubTask 11.1.1: 创建底部导航组件
  - [ ] SubTask 11.1.2: 实现五个主Tab（聊天 | 通讯录 | 群聊 | 任务 | 发现 | 我）
  - [ ] SubTask 11.1.3: 实现Tab切换逻辑
- [ ] Task 11.2: 实现聊天模块
  - [ ] SubTask 11.2.1: 创建私聊列表UI
  - [ ] SubTask 11.2.2: 实现消息类型（文字、图片、语音）
  - [ ] SubTask 11.2.3: 实现聊天详情页
- [ ] Task 11.3: 实现通讯录模块
  - [ ] SubTask 11.3.1: 创建角色列表UI（按字母索引）
  - [ ] SubTask 11.3.2: 实现标签分组
  - [ ] SubTask 11.3.3: 实现点击头像进入角色详情页
- [ ] Task 11.4: 实现角色详情页
  - [ ] SubTask 11.4.1: 创建角色详情UI（大头像+昵称+签名）
  - [ ] SubTask 11.4.2: 实现基本信息显示（年龄/性别/职业+亲密度标签+资金余额）
  - [ ] SubTask 11.4.3: 实现性格标签+最近动态+今日日程
  - [ ] SubTask 11.4.4: 实现技能雷达图（MPAndroidChart）
  - [ ] SubTask 11.4.5: 实现亲密度时间线（历史变化曲线）
  - [ ] SubTask 11.4.6: 实现他的好友（横向滑动头像）
  - [ ] SubTask 11.4.7: 实现他的公司（若加入）
  - [ ] SubTask 11.4.8: 实现最近反思（最近3条）
  - [ ] SubTask 11.4.9: 实现操作按钮（发消息 | 看朋友圈 | 赠送资金）
- [ ] Task 11.5: 实现群聊列表页
  - [ ] SubTask 11.5.1: 创建群聊列表UI
  - [ ] SubTask 11.5.2: 实现私人群聊标识（👥）
  - [ ] SubTask 11.5.3: 实现公司群聊标识（🏢）
  - [ ] SubTask 11.5.4: 实现列表项（群头像+群名称+最后消息预览+时间+未读小红点）
- [ ] Task 11.6: 实现群聊详情页
  - [ ] SubTask 11.6.1: 创建群聊详情UI
  - [ ] SubTask 11.6.2: 实现群成员列表
  - [ ] SubTask 11.6.3: 实现聊天记录区
  - [ ] SubTask 11.6.4: 实现底部提示（"你以观察者身份查看此群聊"）
- [ ] Task 11.7: 实现任务详情页
  - [ ] SubTask 11.7.1: 创建任务详情UI
  - [ ] SubTask 11.7.2: 实现任务名称+奖励金额+状态标签
  - [ ] SubTask 11.7.3: 实现类型+创建时间+截止时间
  - [ ] SubTask 11.7.4: 实现需求描述
  - [ ] SubTask 11.7.5: 实现接取信息（执行角色/公司）
  - [ ] SubTask 11.7.6: 实现进度记录
  - [ ] SubTask 11.7.7: 实现成果展示
  - [ ] SubTask 11.7.8: 实现反思报告入口（完成后）
- [ ] Task 11.8: 实现公司详情页
  - [ ] SubTask 11.8.1: 创建公司详情UI
  - [ ] SubTask 11.8.2: 实现公司基本信息（名称、法人、资金余额）
  - [ ] SubTask 11.8.3: 实现成员列表（按贡献度排序）
  - [ ] SubTask 11.8.4: 实现当前任务
  - [ ] SubTask 11.8.5: 实现知识库入口（反思合集）
  - [ ] SubTask 11.8.6: 实现团队技能平均值变化曲线
- [ ] Task 11.9: 实现发现模块（朋友圈）
  - [ ] SubTask 11.9.1: 创建朋友圈UI
  - [ ] SubTask 11.9.2: 实现好友动态信息流
  - [ ] SubTask 11.9.3: 实现点赞、评论（仅亲密度≥21可见）
- [ ] Task 11.10: 实现个人中心
  - [ ] SubTask 11.10.1: 创建个人中心UI
  - [ ] SubTask 11.10.2: 实现用户资料卡
  - [ ] SubTask 11.10.3: 实现设置入口（API配置、世界参数、日志面板）

## Phase 12: 日志面板

- [ ] Task 12.1: 实现实时日志流
  - [ ] SubTask 12.1.1: 创建日志UI
  - [ ] SubTask 12.1.2: 实现日志格式（\[HH:MM:SS] \[角色名] \[行为类型] 行为描述）
  - [ ] SubTask 12.1.3: 实现日志实时更新
- [ ] Task 12.2: 实现过滤功能
  - [ ] SubTask 12.2.1: 实现按角色筛选
  - [ ] SubTask 12.2.2: 实现按行为类型筛选（任务/社交/记忆/经济）
  - [ ] SubTask 12.2.3: 实现按关键词搜索
- [ ] Task 12.3: 实现世界控制
  - [ ] SubTask 12.3.1: 实现速度调节（1x-30x）
  - [ ] SubTask 12.3.2: 实现手动干预（调整亲密度、发放资金）
  - [ ] SubTask 12.3.3: 实现快照保存与回溯

## Phase 13: AI模型集成

- [ ] Task 13.1: 实现语言模型集成
  - [ ] SubTask 13.1.1: 创建语言模型API客户端
  - [ ] SubTask 13.1.2: 实现对话生成
  - [ ] SubTask 13.1.3: 实现文本生成
  - [ ] SubTask 13.1.4: 实现反思报告生成
- [ ] Task 13.2: 实现图像模型集成
  - [ ] SubTask 13.2.1: 创建图像模型API客户端
  - [ ] SubTask 13.2.2: 实现绘图功能
  - [ ] SubTask 13.2.3: 实现头像生成
- [ ] Task 13.3: 实现向量模型集成
  - [ ] SubTask 13.3.1: 创建向量模型API客户端
  - [ ] SubTask 13.3.2: 实现向量生成
  - [ ] SubTask 13.3.3: 实现BM25降级方案
- [ ] Task 13.4: 实现重排模型集成
  - [ ] SubTask 13.4.1: 创建重排模型API客户端
  - [ ] SubTask 13.4.2: 实现记忆重排
  - [ ] SubTask 13.4.3: 实现直接取Top10降级方案
- [ ] Task 13.5: 实现API调用规范
  - [ ] SubTask 13.5.1: 实现异步处理（不阻塞UI）
  - [ ] SubTask 13.5.2: 实现超时控制（连接5秒，读取30秒）
  - [ ] SubTask 13.5.3: 实现重试策略（失败重试2次，连续失败3次切换备用）
  - [ ] SubTask 13.5.4: 实现API密钥加密存储

## Phase 14: 性能优化

- [ ] Task 14.1: 实现冷启动优化
  - [ ] SubTask 14.1.1: 优化应用启动流程
  - [ ] SubTask 14.1.2: 实现延迟加载
  - [ ] SubTask 14.1.3: 目标冷启动时间<3秒
- [ ] Task 14.2: 实现内存优化
  - [ ] SubTask 14.2.1: 优化内存使用
  - [ ] SubTask 14.2.2: 实现内存泄漏检测
  - [ ] SubTask 14.2.3: 目标内存占用<200MB
- [ ] Task 14.3: 实现帧率优化
  - [ ] SubTask 14.3.1: 优化Compose渲染
  - [ ] SubTask 14.3.2: 实现帧率监控
  - [ ] SubTask 14.3.3: 目标帧率>50fps
- [ ] Task 14.4: 实现后台耗电优化
  - [ ] SubTask 14.4.1: 优化后台任务
  - [ ] SubTask 14.4.2: 目标后台耗电<5%/小时
- [ ] Task 14.5: 实现AI并发控制
  - [ ] SubTask 14.5.1: 实现AI请求队列
  - [ ] SubTask 14.5.2: 实现最大并发数控制（最大3）
  - [ ] SubTask 14.5.3: 实现请求优先级
- [ ] Task 14.6: 实现记忆检索优化
  - [ ] SubTask 14.6.1: 优化Neo4j查询
  - [ ] SubTask 14.6.2: 实现缓存机制
  - [ ] SubTask 14.6.3: 目标检索时间<500ms

## Phase 15: 测试与部署

- [ ] Task 15.1: 实现单元测试
  - [ ] SubTask 15.1.1: 编写数据层单元测试
  - [ ] SubTask 15.1.2: 编写业务逻辑层单元测试
  - [ ] SubTask 15.1.3: 编写ViewModel单元测试
- [ ] Task 15.2: 实现集成测试
  - [ ] SubTask 15.2.1: 编写API集成测试
  - [ ] SubTask 15.2.2: 编写数据库集成测试
  - [ ] SubTask 15.2.3: 编写UI集成测试
- [ ] Task 15.3: 实现性能测试
  - [ ] SubTask 15.3.1: 测试冷启动时间
  - [ ] SubTask 15.3.2: 测试内存占用
  - [ ] SubTask 15.3.3: 测试帧率
  - [ ] SubTask 15.3.4: 测试AI并发
  - [ ] SubTask 15.3.5: 测试记忆检索时间
- [ ] Task 15.4: 实现UI测试
  - [ ] SubTask 15.4.1: 测试所有页面UI
  - [ ] SubTask 15.4.2: 测试用户交互流程
  - [ ] SubTask 15.4.3: 测试响应式布局
- [ ] Task 15.5: 构建APK
  - [ ] SubTask 15.5.1: 配置ProGuard混淆
  - [ ] SubTask 15.5.2: 生成Release APK
  - [ ] SubTask 15.5.3: 签名APK
- [ ] Task 15.6: 部署到GitHub
  - [ ] SubTask 15.6.1: 更新版本号
  - [ ] SubTask 15.6.2: 提交代码
  - [ ] SubTask 15.6.3: 推送到远程仓库

# Task Dependencies

- \[Phase 2-14] depends on \[Phase 1]
- \[Phase 3] depends on \[Phase 1]
- \[Phase 4] depends on \[Phase 2, Phase 3]
- \[Phase 5] depends on \[Phase 2, Phase 3]
- \[Phase 6] depends on \[Phase 5]
- \[Phase 7] depends on \[Phase 2, Phase 4]
- \[Phase 8] depends on \[Phase 2, Phase 5, Phase 7]
- \[Phase 9] depends on \[Phase 2]
- \[Phase 10] depends on \[Phase 2, Phase 9]
- \[Phase 11] depends on \[Phase 2, Phase 4, Phase 5, Phase 7, Phase 9, Phase 10]
- \[Phase 12] depends on \[Phase 2, Phase 4, Phase 5, Phase 7, Phase 9, Phase 10]
- \[Phase 13] depends on \[Phase 1]
- \[Phase 14] depends on \[Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6, Phase 7, Phase 8, Phase 9, Phase 10, Phase 11, Phase 12, Phase 13]
- \[Phase 15] depends on \[Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6, Phase 7, Phase 8, Phase 9, Phase 10, Phase 11, Phase 12, Phase 13, Phase 14]

