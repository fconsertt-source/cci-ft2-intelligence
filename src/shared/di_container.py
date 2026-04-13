# src/composition_root/di_container.py
from typing import Dict, Type, Any, Optional, Callable
import inspect


class DIContainer:
    """حاوية بسيطة لحقن الاعتمادية مع دعم التسجيل التلقائي والمصانع"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}

    def register(self, interface: Type, implementation: Type):
        """Register an implementation for an interface."""
        self._services[interface] = implementation

    def register_instance(self, interface: Type, instance: Any):
        """Register a singleton instance."""
        self._services[interface] = instance

    def register_factory(self, interface: Type, factory: Callable) -> None:
        """تسجيل مصنع للخدمة"""
        self._factories[interface] = factory

    def is_registered(self, interface: Type) -> bool:
        """التحقق من تسجيل خدمة أو مصنع"""
        return interface in self._services or interface in self._factories

    def get_all_registered(self) -> list:
        """الحصول على جميع الواجهات المسجلة"""
        return list(self._services.keys()) + list(self._factories.keys())

    def resolve(self, interface: Type) -> Any:
        """Resolve an implementation for the interface."""
        if interface not in self._services and interface not in self._factories:
            raise KeyError(f"No registration for {interface}")

        if interface in self._factories:
            return self._factories[interface]()

        impl = self._services[interface]
        if inspect.isclass(impl):
            # Auto-inject dependencies if constructor has parameters
            init_sig = inspect.signature(impl.__init__)
            params = {}
            for param_name, param in init_sig.parameters.items():
                if param_name == 'self':
                    continue
                if param.annotation != inspect.Parameter.empty:
                    params[param_name] = self.resolve(param.annotation)
            return impl(**params)
        else:
            # Instance
            return impl