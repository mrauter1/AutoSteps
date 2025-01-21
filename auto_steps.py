import os
import re
import shutil
import importlib
from functools import wraps

from coder import generate_code_from_llm  # Import code generation logic from coder.py
from log import Logger

logger = Logger.get_logger()

###################################################################
# FRAMEWORK SETUP (directory creation)
###################################################################

def ensure_steps_directories():
    """
    Ensure we have 'steps/' and 'steps/ver/' for versioning.
    """
    if not os.path.exists("steps"):
        os.makedirs("steps")
    ver_dir = os.path.join("steps", "ver")
    if not os.path.exists(ver_dir):
        os.makedirs(ver_dir)

# Initialize the framework at import time
ensure_steps_directories()

###################################################################
# STEP DECORATOR & SUPPORT
###################################################################

def step(auto_implement=False, description=None):
    """
    Decorator factory for creating workflow steps.
    If 'auto_implement' is True, we attempt to auto-generate code for missing/stub steps.
    """
    def decorator(func):
        return step_decorator(func, auto_implement, description)
    return decorator

def step_decorator(func, auto_implement=False, description=None):
    @wraps(func)
    def wrapper(*args, **kwargs):
        step_name = func.__name__
        logger.info(f"STEP START: {step_name} with args={args}, kwargs={kwargs}")

        step_path = os.path.join("steps", f"{step_name}.py")
        if file_is_missing_or_stub(step_path):
            logger.info(f"Step '{step_name}' is missing or a stub.")
            if not auto_implement:
                raise NotImplementedError(f"Step '{step_name}' is stub/missing; auto_implement=False.")
            if os.path.exists(step_path):
                version_file(step_name)
            write_new_implementation(func, step_name, step_path, description)

        step_func = load_step_function(step_name)
        result = step_func(*args, **kwargs)
        logger.info(f"STEP END: {step_name} -> {result}")
        return result
    return wrapper

def file_is_missing_or_stub(file_path):
    if not os.path.isfile(file_path):
        return True
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if len(content) < 5:
        return True
    content_no_ws = "".join(content.split())
    if content_no_ws == "pass":
        return True
    if "raiseNotImplementedError" in content_no_ws:
        return True
    return False

def version_file(step_name):
    ver_dir = os.path.join("steps", "ver")
    os.makedirs(ver_dir, exist_ok=True)
    current_file = os.path.join("steps", f"{step_name}.py")
    next_version = get_next_version_number(step_name)
    versioned_file = os.path.join(ver_dir, f"{step_name}_v{next_version}.py")
    shutil.copy2(current_file, versioned_file)
    logger.info(f"[Versioning] Copied {current_file} -> {versioned_file}")

def get_next_version_number(step_name):
    ver_dir = os.path.join("steps", "ver")
    existing_versions = []
    if os.path.exists(ver_dir):
        for fname in os.listdir(ver_dir):
            match = re.match(rf"^{step_name}_v(\d+)\.py$", fname)
            if match:
                existing_versions.append(int(match.group(1)))
    return max(existing_versions) + 1 if existing_versions else 1

def write_new_implementation(func, step_name, step_path, description):
    logger.info(f"Writing new implementation for step '{step_name}'")
    new_code = generate_code_from_llm(func, step_name, description)
    with open(step_path, "w", encoding="utf-8") as f:
        f.write(new_code)

def load_step_function(step_name):
    mod = importlib.import_module(f"steps.{step_name}")
    return getattr(mod, step_name)
