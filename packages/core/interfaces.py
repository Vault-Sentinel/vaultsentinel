"""Plugin interfaces for VaultSentinel."""

from abc import ABC, abstractmethod
from typing import Iterable, Protocol, Dict, Any, Optional
from dataclasses import dataclass
from .models import Finding, ScanRun


@dataclass
class DetectionContext:
    """Context for detection operations."""
    repo: str
    commit_sha: str
    file_path: str
    content: str
    metadata: Dict[str, Any] = None


class Detector(Protocol):
    """Interface for secret detectors."""
    
    name: str
    
    @abstractmethod
    def detect(self, context: DetectionContext) -> Iterable[Finding]:
        """Detect secrets in the given context."""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if the detector is enabled."""
        pass


class Connector(Protocol):
    """Interface for data connectors."""
    
    name: str
    
    @abstractmethod
    def connect(self) -> bool:
        """Test connection to the data source."""
        pass
    
    @abstractmethod
    def fetch_changes(self, since: Optional[str] = None) -> Iterable[DetectionContext]:
        """Fetch changes from the data source."""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if the connector is enabled."""
        pass


class RemediationHandler(Protocol):
    """Interface for remediation handlers."""
    
    name: str
    
    @abstractmethod
    def can_handle(self, finding: Finding) -> bool:
        """Check if this handler can remediate the finding."""
        pass
    
    @abstractmethod
    def remediate(self, finding: Finding) -> Dict[str, Any]:
        """Attempt to remediate the finding."""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if the handler is enabled."""
        pass


class PluginRegistry:
    """Registry for managing plugins."""
    
    def __init__(self):
        self._detectors: Dict[str, Detector] = {}
        self._connectors: Dict[str, Connector] = {}
        self._remediation_handlers: Dict[str, RemediationHandler] = {}
    
    def register_detector(self, detector: Detector) -> None:
        """Register a detector plugin."""
        self._detectors[detector.name] = detector
    
    def register_connector(self, connector: Connector) -> None:
        """Register a connector plugin."""
        self._connectors[connector.name] = connector
    
    def register_remediation_handler(self, handler: RemediationHandler) -> None:
        """Register a remediation handler plugin."""
        self._remediation_handlers[handler.name] = handler
    
    def get_detectors(self) -> Dict[str, Detector]:
        """Get all registered detectors."""
        return {name: detector for name, detector in self._detectors.items() 
                if detector.is_enabled()}
    
    def get_connectors(self) -> Dict[str, Connector]:
        """Get all registered connectors."""
        return {name: connector for name, connector in self._connectors.items() 
                if connector.is_enabled()}
    
    def get_remediation_handlers(self) -> Dict[str, RemediationHandler]:
        """Get all registered remediation handlers."""
        return {name: handler for name, handler in self._remediation_handlers.items() 
                if handler.is_enabled()}
    
    def get_remediation_handler_for_finding(self, finding: Finding) -> Optional[RemediationHandler]:
        """Get the appropriate remediation handler for a finding."""
        for handler in self._remediation_handlers.values():
            if handler.is_enabled() and handler.can_handle(finding):
                return handler
        return None


# Global registry instance
_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """Get the global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def register_detector(detector: Detector) -> Detector:
    """Decorator to register a detector."""
    get_registry().register_detector(detector)
    return detector


def register_connector(connector: Connector) -> Connector:
    """Decorator to register a connector."""
    get_registry().register_connector(connector)
    return connector


def register_remediation_handler(handler: RemediationHandler) -> RemediationHandler:
    """Decorator to register a remediation handler."""
    get_registry().register_remediation_handler(handler)
    return handler
