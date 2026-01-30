import sys
import os

# Add the project root directory to sys.path
# This ensures that 'src' can be imported in tests regardless of how pytest is invoked
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
