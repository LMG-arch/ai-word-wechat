package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.Task
import com.ai.socialworld.data.model.TaskDifficulty
import com.ai.socialworld.data.model.TaskStatus
import com.ai.socialworld.data.model.TaskType
import com.ai.socialworld.domain.repository.TaskRepository
import com.ai.socialworld.domain.repository.ApiConfigRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.random.Random

/**
 * 任务生成服务
 * 每日自动生成任务
 */
@Singleton
class TaskGeneratorService @Inject constructor(
    private val taskRepository: TaskRepository,
    private val apiConfigRepository: ApiConfigRepository
) {
    
    companion object {
        const val MIN_DAILY_TASKS = 3
        const val MAX_DAILY_TASKS = 5
        const val MIN_REWARD = 100
        const val MAX_REWARD = 1000
    }
    
    // 任务模板
    private val taskTemplates = mapOf(
        TaskType.TEXT to listOf(
            "撰写一篇关于{topic}的文章",
            "写一个关于{topic}的故事",
            "撰写产品使用说明书",
            "写一篇产品评测报告",
            "创作一篇散文"
        ),
        TaskType.IMAGE to listOf(
            "绘制一幅{style}风格的风景画",
            "设计一个logo",
            "创作一幅海报",
            "绘制人物肖像",
            "设计产品包装"
        ),
        TaskType.CODE to listOf(
            "开发一个简单的计算器",
            "编写数据抓取脚本",
            "实现一个待办事项应用",
            "编写自动化测试脚本",
            "开发简单的网页爬虫"
        ),
        TaskType.RESEARCH to listOf(
            "调研{topic}市场现状",
            "分析竞争对手产品",
            "收集用户反馈数据",
            "研究行业发展趋势",
            "分析用户行为数据"
        ),
        TaskType.DESIGN to listOf(
            "设计APP界面原型",
            "制作产品宣传海报",
            "设计品牌VI系统",
            "创作插画素材",
            "设计网页布局"
        )
    )
    
    private val topics = listOf(
        "人工智能", "区块链", "新能源", "健康生活", 
        "科技趋势", "环保", "教育创新", "文化传承"
    )
    
    private val styles = listOf(
        "史诗", "写实", "印象派", "现代简约", "古典"
    )
    
    /**
     * 生成每日任务
     */
    suspend fun generateDailyTasks(): List<Task> = withContext(Dispatchers.IO) {
        val taskCount = Random.nextInt(MIN_DAILY_TASKS, MAX_DAILY_TASKS + 1)
        val tasks = mutableListOf<Task>()
        
        repeat(taskCount) {
            val task = generateRandomTask()
            taskRepository.insertTask(task)
            tasks.add(task)
        }
        
        // 记录日志
        apiConfigRepository.addLog(
            characterId = null,
            characterName = null,
            logType = com.ai.socialworld.domain.repository.LogType.SYSTEM,
            content = "自动生成 ${tasks.size} 个每日任务"
        )
        
        tasks
    }
    
    /**
     * 生成随机任务
     */
    private fun generateRandomTask(): Task {
        val taskType = TaskType.values().random()
        val template = taskTemplates[taskType]?.random() ?: "完成一个${taskType.name}任务"
        
        // 替换模板中的占位符
        val description = template
            .replace("{topic}", topics.random())
            .replace("{style}", styles.random())
        
        // 根据难度设置奖励
        val difficulty = TaskDifficulty.values().random()
        val reward = when (difficulty) {
            TaskDifficulty.EASY -> Random.nextInt(100, 200)
            TaskDifficulty.MEDIUM -> Random.nextInt(200, 400)
            TaskDifficulty.HARD -> Random.nextInt(400, 700)
            TaskDifficulty.EPIC -> Random.nextInt(700, 1001)
        }
        
        // 设置截止时间（未来3-7天）
        val deadlineDays = Random.nextLong(3, 8)
        val deadline = System.currentTimeMillis() + (deadlineDays * 24 * 60 * 60 * 1000)
        
        return Task(
            id = UUID.randomUUID().toString(),
            title = "${taskType.name}任务",
            description = description,
            type = taskType,
            difficulty = difficulty,
            reward = reward,
            status = TaskStatus.PENDING,
            createdAt = System.currentTimeMillis(),
            deadline = deadline
        )
    }
    
    /**
     * 创建自定义任务
     */
    suspend fun createCustomTask(
        title: String,
        description: String,
        type: TaskType,
        reward: Int,
        deadline: Long? = null
    ): Task = withContext(Dispatchers.IO) {
        val task = Task(
            id = UUID.randomUUID().toString(),
            title = title,
            description = description,
            type = type,
            difficulty = when {
                reward < 200 -> TaskDifficulty.EASY
                reward < 400 -> TaskDifficulty.MEDIUM
                reward < 700 -> TaskDifficulty.HARD
                else -> TaskDifficulty.EPIC
            },
            reward = reward.coerceIn(MIN_REWARD, 10000),
            status = TaskStatus.PENDING,
            createdAt = System.currentTimeMillis(),
            deadline = deadline ?: (System.currentTimeMillis() + 7 * 24 * 60 * 60 * 1000)
        )
        
        taskRepository.insertTask(task)
        
        // 记录日志
        apiConfigRepository.addLog(
            characterId = null,
            characterName = null,
            logType = com.ai.socialworld.domain.repository.LogType.TASK,
            content = "创建自定义任务: $title"
        )
        
        task
    }
    
    /**
     * 生成基于角色的个性化任务
     */
    suspend fun generatePersonalizedTask(
        characterId: String,
        characterOccupation: String,
        characterSkills: Map<String, Float>
    ): Task? = withContext(Dispatchers.IO) {
        // 根据职业和技能选择合适的任务类型
        val preferredType = when {
            characterOccupation.contains("程序员") || characterOccupation.contains("开发") -> TaskType.CODE
            characterOccupation.contains("设计师") -> TaskType.DESIGN
            characterOccupation.contains("作家") || characterOccupation.contains("编辑") -> TaskType.TEXT
            characterOccupation.contains("分析师") -> TaskType.RESEARCH
            else -> TaskType.values().random()
        }
        
        val task = generateRandomTask().copy(
            type = preferredType,
            title = "${characterOccupation}专属任务"
        )
        
        taskRepository.insertTask(task)
        task
    }
}
