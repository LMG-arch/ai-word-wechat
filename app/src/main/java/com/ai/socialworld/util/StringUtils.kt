package com.ai.socialworld.util

import java.security.MessageDigest
import java.util.*

/**
 * 字符串工具类
 */
object StringUtils {
    
    /**
     * 判断字符串是否为空或空白
     */
    fun isBlank(str: String?): Boolean {
        return str.isNullOrBlank()
    }
    
    /**
     * 判断字符串不为空
     */
    fun isNotBlank(str: String?): Boolean {
        return !isBlank(str)
    }
    
    /**
     * 截断字符串
     */
    fun truncate(str: String, maxLength: Int, suffix: String = "..."): String {
        return if (str.length <= maxLength) {
            str
        } else {
            str.take(maxLength - suffix.length) + suffix
        }
    }
    
    /**
     * 生成唯一ID
     */
    fun generateId(): String {
        return UUID.randomUUID().toString()
    }
    
    /**
     * 生成短ID
     */
    fun generateShortId(): String {
        return UUID.randomUUID().toString().take(8)
    }
    
    /**
     * 计算字符串的MD5哈希
     */
    fun md5(str: String): String {
        val md = MessageDigest.getInstance("MD5")
        val digest = md.digest(str.toByteArray())
        return digest.joinToString("") { "%02x".format(it) }
    }
    
    /**
     * 计算字符串的SHA-256哈希
     */
    fun sha256(str: String): String {
        val md = MessageDigest.getInstance("SHA-256")
        val digest = md.digest(str.toByteArray())
        return digest.joinToString("") { "%02x".format(it) }
    }
    
    /**
     * 拼接字符串（带分隔符）
     */
    fun joinWithSeparator(items: List<String>, separator: String = ", "): String {
        return items.joinToString(separator)
    }
    
    /**
     * 分割字符串
     */
    fun splitBySeparator(str: String, separator: String = ","): List<String> {
        return if (str.isBlank()) {
            emptyList()
        } else {
            str.split(separator).map { it.trim() }.filter { it.isNotEmpty() }
        }
    }
    
    /**
     * 首字母大写
     */
    fun capitalize(str: String): String {
        return if (str.isEmpty()) str else str.replaceFirstChar { it.uppercase() }
    }
    
    /**
     * 移除HTML标签
     */
    fun stripHtmlTags(html: String): String {
        return html.replace(Regex("<[^>]*>"), "")
    }
    
    /**
     * 计算字符串的字数（中文按字符计算，英文按单词计算）
     */
    fun countWords(str: String): Int {
        val chineseCount = str.count { it.code in 0x4E00..0x9FFF }
        val englishWords = str.replace(Regex("[\\u4e00-\\u9fff]"), " ")
            .split(Regex("\\s+"))
            .count { it.isNotBlank() }
        return chineseCount + englishWords
    }
    
    /**
     * 简单的字符串相似度计算（Levenshtein距离）
     */
    fun similarity(str1: String, str2: String): Float {
        if (str1 == str2) return 1f
        if (str1.isEmpty() || str2.isEmpty()) return 0f
        
        val distance = levenshteinDistance(str1, str2)
        val maxLength = maxOf(str1.length, str2.length)
        return 1f - distance.toFloat() / maxLength
    }
    
    private fun levenshteinDistance(str1: String, str2: String): Int {
        val dp = Array(str1.length + 1) { IntArray(str2.length + 1) }
        
        for (i in 0..str1.length) dp[i][0] = i
        for (j in 0..str2.length) dp[0][j] = j
        
        for (i in 1..str1.length) {
            for (j in 1..str2.length) {
                val cost = if (str1[i - 1] == str2[j - 1]) 0 else 1
                dp[i][j] = minOf(
                    dp[i - 1][j] + 1,      // 删除
                    dp[i][j - 1] + 1,      // 插入
                    dp[i - 1][j - 1] + cost // 替换
                )
            }
        }
        
        return dp[str1.length][str2.length]
    }
}
