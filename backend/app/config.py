"""
Configuración de MiroFish + LINK Engine.

Las credenciales se cargan desde el .env raíz en desarrollo o desde variables
de entorno en producción. Ningún secreto debe llegar al frontend ni al repo.
"""

import os
from dotenv import load_dotenv

project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    load_dotenv(override=True)


def _csv_env(name: str) -> list[str]:
    return [
        value.strip()
        for value in os.environ.get(name, '').split(',')
        if value.strip()
    ]


class Config:
    """Configuración del backend MiroFish usado como motor de LINK Study."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mirofish-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    JSON_AS_ASCII = False

    # Seguridad server-to-server LINK Study -> MiroFish.
    # Fail closed: si no existe token, /api/* responde 503.
    LINK_ENGINE_API_TOKEN = os.environ.get('LINK_ENGINE_API_TOKEN')
    LINK_ENGINE_ALLOWED_ORIGINS = _csv_env('LINK_ENGINE_ALLOWED_ORIGINS')

    # LLM (API compatible con OpenAI SDK)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')

    # Zep Cloud
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')

    # Archivos
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    # Procesamiento de texto
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50

    # OASIS
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')

    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Report Agent
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    @classmethod
    def validate(cls) -> list[str]:
        """Valida configuración necesaria sin exponer valores secretos."""
        errors: list[str] = []
        if not cls.LINK_ENGINE_API_TOKEN:
            errors.append('LINK_ENGINE_API_TOKEN no configurado')
        if not cls.LLM_API_KEY:
            errors.append('LLM_API_KEY no configurado')
        if not cls.ZEP_API_KEY:
            errors.append('ZEP_API_KEY no configurado')
        if os.environ.get('ZEP_API_URL'):
            errors.append('ZEP_API_URL no soportado; MiroFish usa Zep Cloud')
        if cls.DEBUG:
            import warnings
            warnings.warn(
                'Flask DEBUG mode is enabled. Do not use in production.',
                RuntimeWarning,
            )
        return errors
