"""
Context propagator implementation.

This module provides a propagator for distributing context between threads and tasks.
"""

import asyncio
import contextvars
import threading
import uuid
from typing import Any, Dict, Optional, Set, TypeVar, cast

from core.logging.interfaces import ILoggingContext


T = TypeVar('T')


class ContextPropagator:
    """
    Propagator for distributing context between threads and tasks.
    
    This propagator ensures that context is properly propagated between threads and tasks.
    """
    
    def __init__(self):
        """Initialize a new context propagator."""
        self._contexts: Dict[str, contextvars.ContextVar[Any]] = {}
        self._lock = threading.RLock()
        self._thread_local = threading.local()
    
    def get_context_var(self, name: str, default: Optional[T] = None) -> contextvars.ContextVar[T]:
        """
        Get a context variable.
        
        Args:
            name: The context variable name
            default: The default value
            
        Returns:
            The context variable
        """
        with self._lock:
            if name not in self._contexts:
                self._contexts[name] = contextvars.ContextVar(name, default=default)
            
            return cast(contextvars.ContextVar[T], self._contexts[name])
    
    def set_context(self, name: str, value: Any) -> contextvars.Token:
        """
        Set a context value.
        
        Args:
            name: The context name
            value: The context value
            
        Returns:
            A token for resetting the context
        """
        context_var = self.get_context_var(name)
        return context_var.set(value)
    
    def get_context(self, name: str, default: Optional[T] = None) -> T:
        """
        Get a context value.
        
        Args:
            name: The context name
            default: The default value
            
        Returns:
            The context value
        """
        context_var = self.get_context_var(name, default)
        return context_var.get()
    
    def reset_context(self, name: str, token: contextvars.Token) -> None:
        """
        Reset a context value.
        
        Args:
            name: The context name
            token: The token from set_context
        """
        context_var = self.get_context_var(name)
        context_var.reset(token)
    
    def copy_context(self) -> contextvars.Context:
        """
        Copy the current context.
        
        Returns:
            A copy of the current context
        """
        return contextvars.copy_context()
    
    def run_with_context(self, context: contextvars.Context, func: callable, *args: Any, **kwargs: Any) -> Any:
        """
        Run a function with a specific context.
        
        Args:
            context: The context to use
            func: The function to run
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function
        """
        return context.run(func, *args, **kwargs)
    
    async def run_async_with_context(self, context: contextvars.Context, func: callable, *args: Any, **kwargs: Any) -> Any:
        """
        Run an async function with a specific context.
        
        Args:
            context: The context to use
            func: The async function to run
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function
        """
        return await context.run(func, *args, **kwargs)
    
    def wrap_thread_target(self, target: callable, *args: Any, **kwargs: Any) -> callable:
        """
        Wrap a thread target function to propagate context.
        
        Args:
            target: The target function
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            A wrapped function that propagates context
        """
        # Copy the current context
        context = self.copy_context()
        
        # Create a wrapper function
        def wrapper():
            # Run the target function with the copied context
            return self.run_with_context(context, target, *args, **kwargs)
        
        return wrapper
    
    def wrap_async_task(self, func: callable, *args: Any, **kwargs: Any) -> callable:
        """
        Wrap an async task function to propagate context.
        
        Args:
            func: The async function
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            A wrapped async function that propagates context
        """
        # Copy the current context
        context = self.copy_context()
        
        # Create a wrapper function
        async def wrapper():
            # Run the function with the copied context
            return await self.run_async_with_context(context, func, *args, **kwargs)
        
        return wrapper
    
    def create_thread(self, target: callable, *args: Any, **kwargs: Any) -> threading.Thread:
        """
        Create a thread with propagated context.
        
        Args:
            target: The target function
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            A thread with propagated context
        """
        # Wrap the target function
        wrapped_target = self.wrap_thread_target(target, *args, **kwargs)
        
        # Create a thread with the wrapped target
        return threading.Thread(target=wrapped_target)
    
    def create_task(self, func: callable, *args: Any, **kwargs: Any) -> asyncio.Task:
        """
        Create an async task with propagated context.
        
        Args:
            func: The async function
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            An async task with propagated context
        """
        # Wrap the function
        wrapped_func = self.wrap_async_task(func, *args, **kwargs)
        
        # Create a task with the wrapped function
        return asyncio.create_task(wrapped_func())


class ContextSnapshot:
    """
    Snapshot of the current context.
    
    This snapshot can be used to restore context later.
    """
    
    def __init__(self, propagator: ContextPropagator, context_names: Optional[Set[str]] = None):
        """
        Initialize a new context snapshot.
        
        Args:
            propagator: The context propagator
            context_names: The names of contexts to snapshot
        """
        self._propagator = propagator
        self._context = propagator.copy_context()
        self._context_names = context_names or set()
        self._id = str(uuid.uuid4())
    
    @property
    def id(self) -> str:
        """Get the snapshot ID."""
        return self._id
    
    def restore(self) -> None:
        """Restore the context."""
        # Run a dummy function to restore the context
        self._propagator.run_with_context(self._context, lambda: None)
    
    async def restore_async(self) -> None:
        """Restore the context asynchronously."""
        # Run a dummy function to restore the context
        await self._propagator.run_async_with_context(self._context, lambda: None)
    
    def run(self, func: callable, *args: Any, **kwargs: Any) -> Any:
        """
        Run a function with the snapshot context.
        
        Args:
            func: The function to run
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function
        """
        return self._propagator.run_with_context(self._context, func, *args, **kwargs)
    
    async def run_async(self, func: callable, *args: Any, **kwargs: Any) -> Any:
        """
        Run an async function with the snapshot context.
        
        Args:
            func: The async function to run
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function
        """
        return await self._propagator.run_async_with_context(self._context, func, *args, **kwargs)


# Singleton instance
_default_propagator: Optional[ContextPropagator] = None
_propagator_lock = threading.RLock()


def get_default_propagator() -> ContextPropagator:
    """
    Get the default context propagator.
    
    Returns:
        The default context propagator
    """
    global _default_propagator
    
    with _propagator_lock:
        if _default_propagator is None:
            _default_propagator = ContextPropagator()
        
        return _default_propagator


def create_snapshot(context_names: Optional[Set[str]] = None) -> ContextSnapshot:
    """
    Create a snapshot of the current context.
    
    Args:
        context_names: The names of contexts to snapshot
        
    Returns:
        A snapshot of the current context
    """
    return ContextSnapshot(get_default_propagator(), context_names) 