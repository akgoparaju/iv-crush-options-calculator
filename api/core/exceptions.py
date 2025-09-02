"""
Custom exceptions for the Options Trading API
"""

class APIException(Exception):
    """Base API exception"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

class ValidationError(APIException):
    """Raised when request data validation fails"""
    pass

class AuthenticationError(APIException):
    """Raised when authentication fails"""
    pass

class AuthorizationError(APIException):
    """Raised when user lacks required permissions"""
    pass

class PortfolioServiceError(APIException):
    """Raised when portfolio service operations fail"""
    pass

class ScreeningServiceError(APIException):
    """Raised when screening service operations fail"""
    pass

class MarketDataError(APIException):
    """Raised when market data operations fail"""
    pass

class DatabaseError(APIException):
    """Raised when database operations fail"""
    pass

class CacheError(APIException):
    """Raised when cache operations fail"""
    pass

class EducationServiceError(APIException):
    """Raised when education service operations fail"""
    pass