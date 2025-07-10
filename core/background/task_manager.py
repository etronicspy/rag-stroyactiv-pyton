"""
Task Manager для управления background tasks и async processing.
Этап 8.6: Task management для async processing и background jobs.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from core.logging import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """Статус задачи."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Информация о задаче."""
    id: str
    name: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """Продолжительность выполнения задачи в секундах."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_running(self) -> bool:
        """Проверить, выполняется ли задача."""
        return self.status == TaskStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """Проверить, завершена ли задача."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]


class TaskManager:
    """
    Менеджер для управления background tasks и async processing.
    Поддерживает создание, отслеживание и управление асинхронными задачами.
    """
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = logger
        
        # Активные задачи
        self.tasks: Dict[str, asyncio.Task] = {}
        self.task_info: Dict[str, TaskInfo] = {}
        
        # Статистика
        self.stats = {
            'total_tasks': 0,
            'active_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0
        }
        
        # Cleanup задача
        self.cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = 300  # 5 минут
        
    async def start(self) -> None:
        """Запустить Task Manager."""
        try:
            self.logger.info("Starting Task Manager")
            
            # Запускаем cleanup задачу
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("Task Manager started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting Task Manager: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Остановить Task Manager."""
        try:
            self.logger.info("Stopping Task Manager")
            
            # Отменяем cleanup задачу
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Отменяем все активные задачи
            await self.cancel_all_tasks()
            
            self.logger.info("Task Manager stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping Task Manager: {str(e)}")
            raise
    
    async def create_task(
        self,
        task_id: str,
        task_name: str,
        coro: Awaitable[Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Создать новую задачу.
        
        Args:
            task_id: Уникальный идентификатор задачи
            task_name: Название задачи
            coro: Корутина для выполнения
            metadata: Дополнительные метаданные
            
        Returns:
            True если задача создана успешно
        """
        try:
            # Проверяем лимиты
            if len(self.tasks) >= self.max_concurrent_tasks:
                self.logger.warning(f"Max concurrent tasks reached: {len(self.tasks)}")
                return False
            
            # Проверяем уникальность ID
            if task_id in self.tasks:
                self.logger.warning(f"Task with ID {task_id} already exists")
                return False
            
            # Создаем информацию о задаче
            task_info = TaskInfo(
                id=task_id,
                name=task_name,
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Создаем задачу
            task = asyncio.create_task(
                self._run_task(task_id, coro)
            )
            
            # Сохраняем задачу
            self.tasks[task_id] = task
            self.task_info[task_id] = task_info
            
            # Обновляем статистику
            self.stats['total_tasks'] += 1
            self.stats['active_tasks'] += 1
            
            self.logger.info(f"Created task {task_id}: {task_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating task {task_id}: {str(e)}")
            return False
    
    async def _run_task(self, task_id: str, coro: Awaitable[Any]) -> Any:
        """
        Выполнить задачу с отслеживанием статуса.
        
        Args:
            task_id: Идентификатор задачи
            coro: Корутина для выполнения
            
        Returns:
            Результат выполнения задачи
        """
        task_info = self.task_info[task_id]
        
        try:
            # Обновляем статус на "running"
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = datetime.utcnow()
            
            self.logger.debug(f"Starting task {task_id}: {task_info.name}")
            
            # Выполняем задачу
            result = await coro
            
            # Обновляем статус на "completed"
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.utcnow()
            task_info.result = result
            
            # Обновляем статистику
            self.stats['active_tasks'] -= 1
            self.stats['completed_tasks'] += 1
            
            self.logger.info(f"Completed task {task_id} in {task_info.duration:.2f}s")
            return result
            
        except asyncio.CancelledError:
            # Задача отменена
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.utcnow()
            
            self.stats['active_tasks'] -= 1
            self.stats['cancelled_tasks'] += 1
            
            self.logger.warning(f"Task {task_id} was cancelled")
            raise
            
        except Exception as e:
            # Ошибка выполнения
            task_info.status = TaskStatus.FAILED
            task_info.completed_at = datetime.utcnow()
            task_info.error_message = str(e)
            
            self.stats['active_tasks'] -= 1
            self.stats['failed_tasks'] += 1
            
            self.logger.error(f"Task {task_id} failed: {str(e)}")
            raise
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Отменить задачу.
        
        Args:
            task_id: Идентификатор задачи
            
        Returns:
            True если задача отменена успешно
        """
        try:
            if task_id not in self.tasks:
                self.logger.warning(f"Task {task_id} not found")
                return False
            
            task = self.tasks[task_id]
            
            if task.done():
                self.logger.warning(f"Task {task_id} is already completed")
                return False
            
            # Отменяем задачу
            task.cancel()
            
            self.logger.info(f"Cancelled task {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False
    
    async def cancel_all_tasks(self) -> int:
        """
        Отменить все активные задачи.
        
        Returns:
            Количество отмененных задач
        """
        try:
            cancelled_count = 0
            
            for task_id, task in self.tasks.items():
                if not task.done():
                    task.cancel()
                    cancelled_count += 1
            
            # Ждем завершения всех задач
            if self.tasks:
                await asyncio.gather(*self.tasks.values(), return_exceptions=True)
            
            self.logger.info(f"Cancelled {cancelled_count} tasks")
            return cancelled_count
            
        except Exception as e:
            self.logger.error(f"Error cancelling all tasks: {str(e)}")
            return 0
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """
        Получить информацию о задаче.
        
        Args:
            task_id: Идентификатор задачи
            
        Returns:
            Информация о задаче или None
        """
        return self.task_info.get(task_id)
    
    def get_all_tasks(self) -> List[TaskInfo]:
        """
        Получить информацию о всех задачах.
        
        Returns:
            Список информации о задачах
        """
        return list(self.task_info.values())
    
    def get_active_tasks(self) -> List[TaskInfo]:
        """
        Получить информацию об активных задачах.
        
        Returns:
            Список активных задач
        """
        return [
            task_info for task_info in self.task_info.values()
            if task_info.status == TaskStatus.RUNNING
        ]
    
    def get_completed_tasks(self) -> List[TaskInfo]:
        """
        Получить информацию о завершенных задачах.
        
        Returns:
            Список завершенных задач
        """
        return [
            task_info for task_info in self.task_info.values()
            if task_info.is_completed
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику задач.
        
        Returns:
            Словарь со статистикой
        """
        return {
            **self.stats,
            'active_task_ids': list(self.tasks.keys()),
            'max_concurrent_tasks': self.max_concurrent_tasks
        }
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Ждать завершения задачи.
        
        Args:
            task_id: Идентификатор задачи
            timeout: Таймаут ожидания в секундах
            
        Returns:
            Результат выполнения задачи
        """
        try:
            if task_id not in self.tasks:
                raise ValueError(f"Task {task_id} not found")
            
            task = self.tasks[task_id]
            
            if timeout:
                result = await asyncio.wait_for(task, timeout=timeout)
            else:
                result = await task
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for task {task_id}")
            raise
        except Exception as e:
            self.logger.error(f"Error waiting for task {task_id}: {str(e)}")
            raise
    
    async def _cleanup_loop(self) -> None:
        """Цикл очистки завершенных задач."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_completed_tasks()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}")
    
    async def _cleanup_completed_tasks(self) -> None:
        """Очистить завершенные задачи."""
        try:
            # Найти задачи для очистки (старше 1 часа)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            tasks_to_remove = []
            for task_id, task_info in self.task_info.items():
                if (task_info.is_completed and 
                    task_info.completed_at and 
                    task_info.completed_at < cutoff_time):
                    tasks_to_remove.append(task_id)
            
            # Удалить задачи
            for task_id in tasks_to_remove:
                if task_id in self.tasks:
                    del self.tasks[task_id]
                if task_id in self.task_info:
                    del self.task_info[task_id]
            
            if tasks_to_remove:
                self.logger.debug(f"Cleaned up {len(tasks_to_remove)} completed tasks")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up completed tasks: {str(e)}")
    
    @asynccontextmanager
    async def task_context(
        self,
        task_id: str,
        task_name: str,
        coro: Awaitable[Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Контекстный менеджер для создания и управления задачей.
        
        Args:
            task_id: Идентификатор задачи
            task_name: Название задачи
            coro: Корутина для выполнения
            metadata: Дополнительные метаданные
        """
        created = await self.create_task(task_id, task_name, coro, metadata)
        
        if not created:
            raise RuntimeError(f"Failed to create task {task_id}")
        
        try:
            yield self.get_task_info(task_id)
        finally:
            # Задача автоматически очистится через cleanup loop
            pass


# Singleton instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """
    Получить singleton instance Task Manager.
    
    Returns:
        Singleton instance TaskManager
    """
    global _task_manager
    
    if _task_manager is None:
        _task_manager = TaskManager()
    
    return _task_manager


async def initialize_task_manager() -> None:
    """Инициализировать Task Manager."""
    task_manager = get_task_manager()
    await task_manager.start()


async def shutdown_task_manager() -> None:
    """Остановить Task Manager."""
    task_manager = get_task_manager()
    await task_manager.stop() 