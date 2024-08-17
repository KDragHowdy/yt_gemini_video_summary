class VideoProcessingError(Exception):
    """Custom exception for video processing errors."""

    pass


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except VideoProcessingError:
            raise
        except Exception as e:
            raise VideoProcessingError(f"An unexpected error occurred: {str(e)}")

    return wrapper


# Example usage in other modules:
# from error_handling import handle_exceptions, VideoProcessingError

# @handle_exceptions
# def some_function():
#     # Your code here
#     pass

# try:
#     some_function()
# except VideoProcessingError as e:
#     print(f"Error: {str(e)}")
