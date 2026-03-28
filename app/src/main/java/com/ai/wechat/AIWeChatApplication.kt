package com.ai.wechat

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * AI 社交世界应用程序入口
 * 初始化全局组件和配置
 */
@HiltAndroidApp
class AIWeChatApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        
        // 初始化全局配置
        initGlobalConfig()
    }
    
    private fun initGlobalConfig() {
        // 这里可以初始化全局配置
        // 例如：时间倍速、死亡机制开关等
    }
}
