package com.ai.socialworld.data.database

import org.neo4j.driver.Driver
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class Neo4jDatabaseManager @Inject constructor(
    private val driver: Driver
) {

    fun getDriver(): Driver {
        return driver
    }

    fun close() {
        driver.close()
    }
}
