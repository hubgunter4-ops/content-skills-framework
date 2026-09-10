"""Public exception types for the framework contracts and runtime."""
from __future__ import annotations


class FrameworkError(Exception):
    """Base class for expected framework errors."""


class ContractError(FrameworkError, ValueError):
    """A request, result, metadata record, or schema violates a contract."""


class InvalidRequestError(ContractError):
    """The normalized or execution request is invalid."""


class InvalidResultError(ContractError):
    """A tool returned a result that does not satisfy its output contract."""


class ToolNotFoundError(FrameworkError):
    """No registered tool matches the requested identifier."""


class ToolConflictError(FrameworkError):
    """More than one tool claims the same qualified identifier."""


class CapabilityDeniedError(FrameworkError):
    """A tool requested a capability that the execution policy denies."""


class ProviderUnavailableError(FrameworkError):
    """An optional provider is disabled or unavailable."""


class ExecutionTimeoutError(FrameworkError):
    """A tool exceeded its execution deadline."""


class QuotaExceededError(FrameworkError):
    """An execution exceeded a configured resource quota."""


class CircuitOpenError(FrameworkError):
    """Execution was blocked because the tool circuit is open."""


class WorkerCrashedError(FrameworkError):
    """An isolated worker terminated unexpectedly."""
