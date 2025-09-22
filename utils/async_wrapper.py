"""
Async wrapper utilities for OceanScope.
Provides synchronous interfaces for async database operations.
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Optional


def async_to_sync(async_func: Callable) -> Callable:
    """Convert async function to sync function."""
    @wraps(async_func)
    def sync_wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, create a new one
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, async_func(*args, **kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(async_func(*args, **kwargs))
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(async_func(*args, **kwargs))
    
    return sync_wrapper


class AsyncWrapper:
    """Wrapper class for async operations in sync contexts."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._loop = None
    
    def _get_loop(self):
        """Get or create event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    def run_async(self, coro):
        """Run async coroutine in sync context."""
        loop = self._get_loop()
        try:
            return loop.run_until_complete(coro)
        except Exception as e:
            self.logger.error(f"Error running async operation: {e}")
            raise


# Global async wrapper instance
_async_wrapper = AsyncWrapper()


def run_async(coro):
    """Run async coroutine in sync context."""
    return _async_wrapper.run_async(coro)


# Convenience functions for common async operations
def run_auth_operation(operation, *args, **kwargs):
    """Run authentication operation asynchronously."""
    from utils.auth_manager import AuthManager
    auth_manager = AuthManager()
    return run_async(operation(auth_manager, *args, **kwargs))


def run_chat_operation(operation, *args, **kwargs):
    """Run chat operation asynchronously."""
    from utils.chat_manager import ChatManager
    chat_manager = ChatManager()
    return run_async(operation(chat_manager, *args, **kwargs))
