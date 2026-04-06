"""AIWeChat 路由层"""
from routes.character_routes import router as character_router
from routes.chat_routes import router as chat_router
from routes.moment_routes import router as moment_router
from routes.task_routes import router as task_router
from routes.company_routes import router as company_router
from routes.economy_routes import router as economy_router
from routes.map_routes import router as map_router
from routes.schedule_routes import router as schedule_router
from routes.relationship_routes import router as relationship_router
from routes.memory_routes import router as memory_router
from routes.settings_routes import router as settings_router
from routes.stats_routes import router as stats_router
from routes.scheduler_routes import router as scheduler_router
from routes.llm_usage_routes import router as llm_usage_router

__all__ = [
    'character_router', 'chat_router', 'moment_router', 'task_router',
    'company_router', 'economy_router', 'map_router', 'schedule_router',
    'relationship_router', 'memory_router', 'settings_router', 'stats_router',
    'scheduler_router', 'llm_usage_router',
]
