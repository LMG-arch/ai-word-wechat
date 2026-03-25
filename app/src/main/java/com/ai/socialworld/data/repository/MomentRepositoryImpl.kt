package com.ai.socialworld.data.repository

import com.ai.socialworld.data.database.dao.SocialDao
import com.ai.socialworld.data.database.entity.MomentEntity
import com.ai.socialworld.data.model.Comment
import com.ai.socialworld.data.model.Like
import com.ai.socialworld.data.model.Moment
import com.ai.socialworld.domain.repository.MomentRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant

class MomentRepositoryImpl(
    private val socialDao: SocialDao
) : MomentRepository {

    override fun getAllMoments(): Flow<List<Moment>> {
        return socialDao.getAllMoments().map { entities ->
            entities.map { it.toModel() }
        }
    }

    override fun getMomentsByCharacter(characterId: String): Flow<List<Moment>> {
        return socialDao.getMomentsByCharacter(characterId).map { entities ->
            entities.map { it.toModel() }
        }
    }

    override suspend fun getMomentById(momentId: String): Moment? {
        return socialDao.getMomentById(momentId)?.toModel()
    }

    override suspend fun createMoment(characterId: String, content: String, imageUrl: String?): String {
        val id = System.currentTimeMillis().toString()
        val entity = MomentEntity(
            id = id,
            characterId = characterId,
            content = content,
            imageUrl = imageUrl,
            createdAt = System.currentTimeMillis()
        )
        socialDao.insertMoment(entity)
        return id
    }

    override suspend fun deleteMoment(momentId: String) {
        socialDao.deleteMomentById(momentId)
    }

    override suspend fun likeMoment(momentId: String, characterId: String) {
        val moment = socialDao.getMomentById(momentId) ?: return
        val likes = parseLikes(moment.likesJson).toMutableList()
        if (likes.none { it.characterId == characterId }) {
            likes.add(Like(characterId = characterId))
            val updated = moment.copy(likesJson = serializeLikes(likes))
            socialDao.updateMoment(updated)
        }
    }

    override suspend fun unlikeMoment(momentId: String, characterId: String) {
        val moment = socialDao.getMomentById(momentId) ?: return
        val likes = parseLikes(moment.likesJson).toMutableList()
        likes.removeAll { it.characterId == characterId }
        val updated = moment.copy(likesJson = serializeLikes(likes))
        socialDao.updateMoment(updated)
    }

    override suspend fun isLikedBy(momentId: String, characterId: String): Boolean {
        val moment = socialDao.getMomentById(momentId) ?: return false
        return parseLikes(moment.likesJson).any { it.characterId == characterId }
    }

    override suspend fun addComment(momentId: String, characterId: String, content: String, replyTo: String?): String {
        val moment = socialDao.getMomentById(momentId) ?: return ""
        val comments = parseComments(moment.commentsJson).toMutableList()
        val id = System.currentTimeMillis().toString()
        comments.add(Comment(id = id, characterId = characterId, content = content, replyTo = replyTo))
        val updated = moment.copy(commentsJson = serializeComments(comments))
        socialDao.updateMoment(updated)
        return id
    }

    override suspend fun deleteComment(commentId: String) {
        // Not directly supported, would need to find and update the moment
    }

    private fun parseLikes(json: String): List<Like> {
        return try {
            val array = JSONArray(json)
            (0 until array.length()).map { i ->
                val obj = array.getJSONObject(i)
                Like(
                    characterId = obj.getString("characterId"),
                    timestamp = Instant.ofEpochMilli(obj.optLong("timestamp", System.currentTimeMillis()))
                )
            }
        } catch (e: Exception) {
            emptyList()
        }
    }

    private fun serializeLikes(likes: List<Like>): String {
        val array = JSONArray()
        likes.forEach { like ->
            val obj = JSONObject().apply {
                put("characterId", like.characterId)
                put("timestamp", like.timestamp.toEpochMilli())
            }
            array.put(obj)
        }
        return array.toString()
    }

    private fun parseComments(json: String): List<Comment> {
        return try {
            val array = JSONArray(json)
            (0 until array.length()).map { i ->
                val obj = array.getJSONObject(i)
                Comment(
                    id = obj.getString("id"),
                    characterId = obj.getString("characterId"),
                    content = obj.getString("content"),
                    replyTo = obj.optString("replyTo", null),
                    timestamp = Instant.ofEpochMilli(obj.optLong("timestamp", System.currentTimeMillis()))
                )
            }
        } catch (e: Exception) {
            emptyList()
        }
    }

    private fun serializeComments(comments: List<Comment>): String {
        val array = JSONArray()
        comments.forEach { comment ->
            val obj = JSONObject().apply {
                put("id", comment.id)
                put("characterId", comment.characterId)
                put("content", comment.content)
                comment.replyTo?.let { put("replyTo", it) }
                put("timestamp", comment.timestamp.toEpochMilli())
            }
            array.put(obj)
        }
        return array.toString()
    }

    private fun MomentEntity.toModel(): Moment {
        return Moment(
            id = id,
            characterId = characterId,
            content = content,
            imageUrl = imageUrl,
            createdAt = Instant.ofEpochMilli(createdAt),
            likes = parseLikes(likesJson),
            comments = parseComments(commentsJson)
        )
    }
}