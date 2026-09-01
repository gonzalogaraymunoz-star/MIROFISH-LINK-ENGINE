"""
MiroFish Backend - Flask app factory adapted as LINK Study simulation engine.
"""

import hmac
import os
import warnings

warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, jsonify, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def _request_api_token() -> str | None:
    """Read LINK Engine token from Authorization or explicit internal header."""
    authorization = request.headers.get('Authorization', '')
    if authorization.lower().startswith('bearer '):
        return authorization[7:].strip()
    return request.headers.get('X-Link-Engine-Token')


def create_app(config_class=Config):
    """Create the MiroFish backend used by LINK Study."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    logger = setup_logger('mirofish')

    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info('=' * 50)
        logger.info('MIROFISH-LINK-ENGINE starting...')
        logger.info('=' * 50)

    # Browser access is optional. LINK Study itself talks server-to-server and
    # does not need CORS. If browser origins are explicitly configured, enable
    # CORS only for those origins instead of exposing /api/* to everyone.
    allowed_origins = app.config.get('LINK_ENGINE_ALLOWED_ORIGINS', [])
    if allowed_origins:
        CORS(
            app,
            resources={r'/api/*': {'origins': allowed_origins}},
            allow_headers=['Authorization', 'Content-Type', 'X-Link-Engine-Token'],
        )

    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info('Simulation cleanup registered')

    @app.before_request
    def protect_and_log_request():
        request_logger = get_logger('mirofish.request')
        request_logger.debug(f'Request: {request.method} {request.path}')

        # /health stays public so infrastructure and LINK Study can verify the
        # service without exposing any simulation data or capabilities.
        if request.path.startswith('/api/'):
            if request.method == 'OPTIONS':
                return None

            expected = app.config.get('LINK_ENGINE_API_TOKEN')
            if not expected:
                return jsonify({
                    'success': False,
                    'error': 'api_auth_not_configured',
                }), 503

            supplied = _request_api_token()
            if not supplied or not hmac.compare_digest(str(supplied), str(expected)):
                return jsonify({
                    'success': False,
                    'error': 'unauthorized',
                }), 401

        # Do not log JSON bodies: prompts and business context may contain
        # sensitive study material.
        return None

    @app.after_request
    def log_response(response):
        request_logger = get_logger('mirofish.request')
        request_logger.debug(f'Response: {response.status_code}')
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')

    @app.route('/health')
    def health():
        return {
            'status': 'ok',
            'service': 'MIROFISH-LINK-ENGINE',
            'api_auth': 'configured' if app.config.get('LINK_ENGINE_API_TOKEN') else 'missing',
            'llm': 'configured' if app.config.get('LLM_API_KEY') else 'missing',
            'zep': 'configured' if app.config.get('ZEP_API_KEY') else 'missing',
        }

    if should_log_startup:
        logger.info('MIROFISH-LINK-ENGINE ready')

    return app
