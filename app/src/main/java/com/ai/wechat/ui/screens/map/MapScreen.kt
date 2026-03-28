package com.ai.wechat.ui.screens.map

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.unit.dp
import com.ai.wechat.data.model.Character

/**
 * 世界地图页面
 * 2D 俯视角地图，显示所有角色实时位置
 */
@Composable
fun MapScreen(
    onCharacterClick: (String) -> Unit
) {
    // TODO: 从 ViewModel 获取实际数据
    val characters = remember { mutableStateListOf<Character>() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("世界地图") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // 地图画布
            MapCanvas(
                characters = characters,
                onCharacterClick = onCharacterClick
            )

            // 缩放控制
            Column(
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(16.dp)
            ) {
                FilledTonalButton(onClick = { /* TODO: 放大 */ }) {
                    Text("+")
                }
                Spacer(modifier = Modifier.height(8.dp))
                FilledTonalButton(onClick = { /* TODO: 缩小 */ }) {
                    Text("-")
                }
            }
        }
    }
}

@Composable
fun MapCanvas(
    characters: List<Character>,
    onCharacterClick: (String) -> Unit
) {
    Canvas(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        val canvasWidth = size.width
        val canvasHeight = size.height

        // 绘制背景
        drawRect(color = Color(0xFFE8F5E9))

        // 绘制网格
        drawGrid(canvasWidth, canvasHeight)

        // 绘制角色位置
        characters.forEach { character ->
            // TODO: 根据实际坐标绘制
            val x = canvasWidth * 0.5f
            val y = canvasHeight * 0.5f

            drawCharacterMarker(
                x = x,
                y = y,
                name = character.name,
                isAlive = character.isAlive
            )
        }
    }
}

private fun DrawScope.drawGrid(width: Float, height: Float) {
    val gridSize = 50f
    val lineColor = Color(0xFFC8E6C9)

    // 垂直线
    var x = 0f
    while (x < width) {
        drawLine(
            color = lineColor,
            start = Offset(x, 0f),
            end = Offset(x, height),
            strokeWidth = 1f
        )
        x += gridSize
    }

    // 水平线
    var y = 0f
    while (y < height) {
        drawLine(
            color = lineColor,
            start = Offset(0f, y),
            end = Offset(width, y),
            strokeWidth = 1f
        )
        y += gridSize
    }
}

private fun DrawScope.drawCharacterMarker(
    x: Float,
    y: Float,
    name: String,
    isAlive: Boolean
) {
    val markerColor = if (isAlive) Color(0xFF07C160) else Color(0xFFBDBDBD)
    val radius = 15f

    // 绘制圆点
    drawCircle(
        color = markerColor,
        radius = radius,
        center = Offset(x, y)
    )

    // 绘制名称
    // 注意：Canvas 不支持直接绘制文本，这里简化处理
}
