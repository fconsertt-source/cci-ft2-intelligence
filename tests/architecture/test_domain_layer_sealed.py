import ast
import os

def test_domain_does_not_import_external_layers():
    """
    Ensure domain layer does not import external layers.
    This prevents architecture violations.
    """
    domain_dirs = [
        "src/domain/",
        "src/domain/services/",
        "src/domain/entities/",
        "src/domain/value_objects/",
        "src/domain/enums/"
    ]
    
    for dir_path in domain_dirs:
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith('.py') and not filename.startswith('__'):
                    filepath = os.path.join(dir_path, filename)
                    
                    with open(filepath, "r") as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module:
                                # Check for external layer imports
                                if node.module.startswith(('src.application', 'src.infrastructure', 'src.presentation', 'src.shared')):
                                    raise AssertionError(f"Domain file '{filepath}' imports external layer: {node.module}")
                        
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name.startswith(('src.application', 'src.infrastructure', 'src.presentation', 'src.shared')):
                                    raise AssertionError(f"Domain file '{filepath}' imports external layer: {alias.name}")

    # Success
    assert True
