#!/usr/bin/env python3
"""
Validation script for Task 2: Data models and database setup.
Tests all implemented functionality to ensure requirements are met.
"""

import sys
import logging
import tempfile
import os
import numpy as np
from pathlib import Path
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.models.occupation import Occupation
from app.models.search import SearchRe