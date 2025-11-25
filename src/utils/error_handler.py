"""Error handling middleware and utilities."""

from flask import jsonify
from typing import Dict, Any
import traceback


class PersonaForgeError(Exception):
    """Base exception for PersonaForge."""
    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(PersonaForgeError):
    """Validation error (400)."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=400, details=details)


class NotFoundError(PersonaForgeError):
    """Not found error (404)."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=404, details=details)


class DatabaseError(PersonaForgeError):
    """Database error (500)."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=500, details=details)


def register_error_handlers(app):
    """Register error handlers for Flask app."""
    
    @app.errorhandler(PersonaForgeError)
    def handle_personaforge_error(error: PersonaForgeError):
        """Handle PersonaForge custom errors."""
        response = {
            "error": error.message,
            "status_code": error.status_code
        }
        if error.details:
            response["details"] = error.details
        return jsonify(response), error.status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        return jsonify({
            "error": "Endpoint not found",
            "status_code": 404
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 errors."""
        return jsonify({
            "error": "Internal server error",
            "status_code": 500
        }), 500
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Handle generic exceptions."""
        # Log the full traceback
        import logging
        logger = logging.getLogger("personaforge.app")
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        
        return jsonify({
            "error": "An unexpected error occurred",
            "status_code": 500
        }), 500

