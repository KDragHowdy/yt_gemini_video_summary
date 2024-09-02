class MiniVideoProcessingError(Exception):
    """Custom exception for mini video processing errors."""

    pass


def handle_mini_exceptions(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MiniVideoProcessingError:
            raise
        except Exception as e:
            raise MiniVideoProcessingError(f"An unexpected error occurred: {str(e)}")

    return wrapper
