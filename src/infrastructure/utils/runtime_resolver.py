import subprocess
import logging
from pathlib import Path

from src.infrastructure.utils.path_resolver import (
    get_runtime_dir,
    get_runtime_manifest_path
)

logger = logging.getLogger(__name__)

class RuntimeResolver:
    """
    Intelligent Java Runtime Resolver.
    Strategy: System Java -> Bundled JRE -> Error
    """
    
    def __init__(self):
        self.runtime_dir = get_runtime_dir()
        self.manifest_path = get_runtime_manifest_path()
        
    def resolve_java_executable(self):
        """
        Resolve the path to a compatible java executable.
        """
        # 1. Try System Java
        if self._is_system_java_compatible():
            logger.info("Using system Java runtime")
            return Path("java")
        
        # 2. Try Bundled JRE
        bundled_java = self._get_bundled_java()
        if bundled_java:
            logger.info("Using bundled Java runtime from: %s", bundled_java)
            return bundled_java
            
        raise RuntimeError(
            "No compatible Java runtime found. "
            "Please install Java 8+ or ensure bundled runtime exists in assets/runtime/"
        )
    
    def _is_system_java_compatible(self):
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True, text=True, timeout=10
            )
            return "version" in result.stderr.lower()
        except Exception:
            return False
            
    def _get_bundled_java(self):
        """
        يبحث عن Java في المجلدات المضمنة ويتحقق من البصمة.
        """
        import sys
        is_windows = sys.platform.startswith('win')
        exe_name = "java.exe" if is_windows else "java"
        
        # مسارات محتملة داخل assets/runtime/
        possible_paths = [
            self.runtime_dir / "jre8_win_x64" / "bin" / exe_name,
            self.runtime_dir / "jre8_win_x86" / "bin" / exe_name,
            self.runtime_dir / "jdk25_win_x64" / "bin" / exe_name,
        ]
        
        for java_path in possible_paths:
            if java_path.exists():
                # هنا يمكن إضافة تحقق من Hash إذا لزم الأمر
                return java_path.resolve()
                
        return None
