from __future__ import annotations


class ZeroSysError(Exception):
    """Base exception for all 0sys errors."""


class ConfigError(ZeroSysError):
    """Raised when configuration is invalid or cannot be loaded."""


class ConfigNotFoundError(ConfigError):
    """Raised when configuration file does not exist."""


class ConfigParseError(ConfigError):
    """Raised when configuration file cannot be parsed."""


class ConfigValidationError(ConfigError):
    """Raised when configuration fails schema validation."""


class ConfigVersionError(ConfigError):
    """Raised when configuration version is not supported."""


class BackendError(ZeroSysError):
    """Raised when a backend fails to execute a task."""


class BackendNotFoundError(BackendError):
    """Raised when no backend is registered for a task."""


class PlannerError(ZeroSysError):
    """Raised when the planner cannot build an execution plan."""


class CircularDependencyError(PlannerError):
    """Raised when the task graph contains a cycle."""


class ExecutorError(ZeroSysError):
    """Raised when the executor fails to run a plan."""


class StateError(ZeroSysError):
    """Raised when state storage fails."""


class RollbackError(ZeroSysError):
    """Raised when rollback cannot be performed."""


class WizardError(ZeroSysError):
    """Raised when the interactive wizard fails."""


class ConnectionError(ZeroSysError):
    """Raised when a remote or local connection fails."""


class SecurityError(ZeroSysError):
    """Raised when a security-related operation fails."""
