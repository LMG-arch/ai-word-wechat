package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.Character
import com.ai.socialworld.data.model.GrowthStage
import com.ai.socialworld.data.model.LogType
import com.ai.socialworld.domain.repository.ApiConfigRepository
import com.ai.socialworld.domain.repository.CharacterRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.abs

/**
 * 角色自主更新服务
 * 处理角色头像更换、签名更新等自主行为
 */
@Singleton
class CharacterAutonomyService @Inject constructor(
    private val characterRepository: CharacterRepository,
    private val imageGenerationService: ImageGenerationService,
    private val languageModelService: LanguageModelService,
    private val apiConfigRepository: ApiConfigRepository
) {
    
    companion object {
        const val MAX_AVATAR_CHANGES_PER_WEEK = 2
        const val MAX_SIGNATURE_CHANGES_PER_WEEK = 2
        const val WEEK_IN_MILLIS = 7 * 24 * 60 * 60 * 1000L
    }
    
    // 记录每周更新次数
    private val avatarChangesThisWeek = mutableMapOf<String, Int>()
    private val signatureChangesThisWeek = mutableMapOf<String, Int>()
    private var lastResetTime = System.currentTimeMillis()
    
    /**
     * 检查并执行角色自主更新
     */
    suspend fun checkAndUpdateAutonomy(characterId: String) = withContext(Dispatchers.IO) {
        // 重置每周计数
        resetWeeklyCountersIfNeeded()
        
        val character = characterRepository.getCharacterById(characterId.toLong()) ?: return@withContext
        
        // 检查是否需要更新头像（年龄段跨越强制更新）
        checkAvatarUpdate(character)
        
        // 检查是否需要更新签名
        checkSignatureUpdate(character)
    }
    
    /**
     * 检查头像更新
     */
    private suspend fun checkAvatarUpdate(character: Character) {
        val changes = avatarChangesThisWeek[character.id.toString()] ?: 0
        
        // 检查年龄段跨越
        val currentStage = getGrowthStage(character.age)
        val lastKnownStage = getGrowthStage(character.age - 1)
        
        if (currentStage != lastKnownStage) {
            // 年龄段跨越，强制更新头像
            forceUpdateAvatar(character)
            return
        }
        
        // 检查是否可以自主更新
        if (changes < MAX_AVATAR_CHANGES_PER_WEEK) {
            // 根据心情或重大事件决定是否更新
            if (shouldUpdateAvatar(character)) {
                updateAvatar(character)
            }
        }
    }
    
    /**
     * 判断是否应该更新头像
     */
    private fun shouldUpdateAvatar(character: Character): Boolean {
        // 基于随机因素决定（简化实现）
        // 实际可以根据：心情、重大事件、职业变化等
        return false // 默认不主动更新，只有年龄段跨越时强制更新
    }
    
    /**
     * 强制更新头像（年龄段跨越）
     */
    private suspend fun forceUpdateAvatar(character: Character) {
        val result = imageGenerationService.generateCharacterAvatar(
            character = character,
            style = com.ai.socialworld.domain.service.AvatarStyle.REALISTIC
        )
        
        when (result) {
            is ImageResult.Success -> {
                // 更新头像URL
                val updated = character.copy(avatarUrl = result.imageUrl)
                characterRepository.updateCharacter(updated)
                
                // 记录日志
                apiConfigRepository.addLog(
                    characterId = character.id.toString(),
                    characterName = character.name,
                    logType = LogType.SYSTEM,
                    content = "年龄段跨越，更新头像: ${getGrowthStage(character.age)}"
                )
            }
            is ImageResult.Error -> {
                // 记录失败日志
                apiConfigRepository.addLog(
                    characterId = character.id.toString(),
                    characterName = character.name,
                    logType = LogType.SYSTEM,
                    content = "头像更新失败: ${result.message}"
                )
            }
        }
    }
    
    /**
     * 更新头像（自主）
     */
    private suspend fun updateAvatar(character: Character) {
        val result = imageGenerationService.generateCharacterAvatar(
            character = character,
            style = com.ai.socialworld.domain.service.AvatarStyle.REALISTIC
        )
        
        when (result) {
            is ImageResult.Success -> {
                val updated = character.copy(avatarUrl = result.imageUrl)
                characterRepository.updateCharacter(updated)
                
                avatarChangesThisWeek[character.id.toString()] = 
                    (avatarChangesThisWeek[character.id.toString()] ?: 0) + 1
                
                apiConfigRepository.addLog(
                    characterId = character.id.toString(),
                    characterName = character.name,
                    logType = LogType.SYSTEM,
                    content = "更新头像"
                )
            }
            is ImageResult.Error -> {
                // 忽略失败
            }
        }
    }
    
    /**
     * 检查签名更新
     */
    private suspend fun checkSignatureUpdate(character: Character) {
        val changes = signatureChangesThisWeek[character.id.toString()] ?: 0
        
        if (changes < MAX_SIGNATURE_CHANGES_PER_WEEK) {
            if (shouldUpdateSignature(character)) {
                updateSignature(character)
            }
        }
    }
    
    /**
     * 判断是否应该更新签名
     */
    private fun shouldUpdateSignature(character: Character): Boolean {
        // 基于随机因素（简化实现）
        // 实际可以根据：心情变化、重大事件、生活状态变化等
        return false
    }
    
    /**
     * 更新签名
     */
    private suspend fun updateSignature(character: Character) {
        val result = languageModelService.generateSignature(character)
        
        when (result) {
            is ChatResult.Success -> {
                val newSignature = result.content.take(50) // 限制长度
                val updated = character.copy(signature = newSignature)
                characterRepository.updateCharacter(updated)
                
                signatureChangesThisWeek[character.id.toString()] = 
                    (signatureChangesThisWeek[character.id.toString()] ?: 0) + 1
                
                apiConfigRepository.addLog(
                    characterId = character.id.toString(),
                    characterName = character.name,
                    logType = LogType.SYSTEM,
                    content = "更新签名: $newSignature"
                )
            }
            is ChatResult.Error -> {
                // 忽略失败
            }
        }
    }
    
    /**
     * 获取成长阶段
     */
    private fun getGrowthStage(age: Int): GrowthStage {
        return when {
            age <= 12 -> GrowthStage.CHILD
            age <= 17 -> GrowthStage.TEENAGER
            age <= 40 -> GrowthStage.YOUNG_ADULT
            age <= 60 -> GrowthStage.MIDDLE_AGED
            else -> GrowthStage.ELDERLY
        }
    }
    
    /**
     * 重置每周计数器
     */
    private fun resetWeeklyCountersIfNeeded() {
        val now = System.currentTimeMillis()
        if (now - lastResetTime >= WEEK_IN_MILLIS) {
            avatarChangesThisWeek.clear()
            signatureChangesThisWeek.clear()
            lastResetTime = now
        }
    }
    
    /**
     * 获取角色本周头像更换次数
     */
    fun getAvatarChangesThisWeek(characterId: String): Int {
        return avatarChangesThisWeek[characterId] ?: 0
    }
    
    /**
     * 获取角色本周签名更换次数
     */
    fun getSignatureChangesThisWeek(characterId: String): Int {
        return signatureChangesThisWeek[characterId] ?: 0
    }
}
