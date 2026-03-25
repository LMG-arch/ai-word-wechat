package com.ai.socialworld.presentation.discover

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.rememberAsyncImagePainter
import com.ai.socialworld.presentation.components.TopAppBar
import java.text.SimpleDateFormat
import java.util.*

/**
 * 朋友圈页面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MomentsScreen(
    viewModel: MomentsViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = "朋友圈",
                onNavigateBack = onNavigateBack,
                actions = {
                    IconButton(onClick = { /* TODO: 发布动态 */ }) {
                        Icon(Icons.Default.CameraAlt, contentDescription = "发布")
                    }
                }
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier.padding(paddingValues)
        ) {
            items(uiState.moments) { moment ->
                MomentItem(
                    moment = moment,
                    onLike = { viewModel.likeMoment(moment.id) },
                    onComment = { viewModel.commentMoment(moment.id, it) }
                )
                Divider()
            }
        }
    }
}

@Composable
private fun MomentItem(
    moment: Moment,
    onLike: () -> Unit,
    onComment: (String) -> Unit
) {
    var showCommentInput by remember { mutableStateOf(false) }
    var commentText by remember { mutableStateOf("") }
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        // 头部：头像和昵称
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            if (moment.authorAvatar != null) {
                Image(
                    painter = rememberAsyncImagePainter(moment.authorAvatar),
                    contentDescription = null,
                    modifier = Modifier.size(40.dp),
                    contentScale = ContentScale.Crop
                )
            } else {
                Surface(
                    modifier = Modifier.size(40.dp),
                    shape = MaterialTheme.shapes.small,
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Default.Person,
                            contentDescription = null
                        )
                    }
                }
            }
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Column {
                Text(
                    text = moment.authorName,
                    fontWeight = FontWeight.Medium
                )
                Text(
                    text = formatTime(moment.timestamp),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        
        // 内容
        Text(
            text = moment.content,
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.padding(vertical = 12.dp)
        )
        
        // 图片
        if (moment.imageUrl != null) {
            Image(
                painter = rememberAsyncImagePainter(moment.imageUrl),
                contentDescription = null,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp),
                contentScale = ContentScale.Crop
            )
        }
        
        // 点赞和评论按钮
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 12.dp),
            horizontalArrangement = Arrangement.End
        ) {
            TextButton(onClick = onLike) {
                Icon(
                    imageVector = if (moment.isLiked) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                    contentDescription = "点赞",
                    tint = if (moment.isLiked) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.width(4.dp))
                Text("${moment.likes}")
            }
            
            TextButton(onClick = { showCommentInput = true }) {
                Icon(Icons.Default.Comment, contentDescription = "评论")
                Spacer(modifier = Modifier.width(4.dp))
                Text("${moment.comments.size}")
            }
        }
        
        // 点赞列表
        if (moment.likedBy.isNotEmpty()) {
            Surface(
                color = MaterialTheme.colorScheme.surfaceVariant,
                shape = MaterialTheme.shapes.small,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.Favorite,
                        contentDescription = null,
                        modifier = Modifier.size(16.dp),
                        tint = MaterialTheme.colorScheme.error
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = moment.likedBy.joinToString(", ") + "觉得很赞",
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }
        
        // 评论列表
        if (moment.comments.isNotEmpty()) {
            Surface(
                color = MaterialTheme.colorScheme.surfaceVariant,
                shape = MaterialTheme.shapes.small,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = if (moment.likedBy.isNotEmpty()) 4.dp else 0.dp)
            ) {
                Column(modifier = Modifier.padding(8.dp)) {
                    moment.comments.forEach { comment ->
                        Text(
                            text = "${comment.authorName}: ${comment.content}",
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }
            }
        }
        
        // 评论输入框
        if (showCommentInput) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = commentText,
                    onValueChange = { commentText = it },
                    placeholder = { Text("发表评论...") },
                    modifier = Modifier.weight(1f),
                    singleLine = true
                )
                Spacer(modifier = Modifier.width(8.dp))
                Button(
                    onClick = {
                        if (commentText.isNotBlank()) {
                            onComment(commentText)
                            commentText = ""
                            showCommentInput = false
                        }
                    }
                ) {
                    Text("发送")
                }
            }
        }
    }
}

private fun formatTime(timestamp: Long): String {
    val sdf = SimpleDateFormat("MM-dd HH:mm", Locale.getDefault())
    return sdf.format(Date(timestamp))
}

// 数据类
data class Moment(
    val id: String,
    val authorId: String,
    val authorName: String,
    val authorAvatar: String? = null,
    val content: String,
    val imageUrl: String? = null,
    val timestamp: Long = System.currentTimeMillis(),
    val likes: Int = 0,
    val likedBy: List<String> = emptyList(),
    val isLiked: Boolean = false,
    val comments: List<Comment> = emptyList()
)

data class Comment(
    val id: String,
    val authorId: String,
    val authorName: String,
    val content: String,
    val timestamp: Long = System.currentTimeMillis()
)
