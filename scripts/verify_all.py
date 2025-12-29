#!/usr/bin/env python3
"""Verify all imports and connections work."""

import sys
from pathlib import Path

errors = []
warnings = []

def test_import(module_name, description):
    """Test an import."""
    try:
        __import__(module_name)
        print(f"[OK] {description}")
        return True
    except Exception as e:
        print(f"[FAIL] {description}: {e}")
        errors.append(f"{description}: {e}")
        return False

def test_connection(description, test_func):
    """Test a connection."""
    try:
        result = test_func()
        if result:
            print(f"[OK] {description}")
            return True
        else:
            print(f"[FAIL] {description}: Failed")
            errors.append(f"{description}: Failed")
            return False
    except Exception as e:
        print(f"[FAIL] {description}: {e}")
        errors.append(f"{description}: {e}")
        return False

print("=" * 60)
print("  DEEPFORGE VERIFICATION")
print("=" * 60)
print()

print("Core Modules:")
test_import("core.config", "Config loader")
test_import("core.registry", "Service registry")
test_import("core.events", "Event bus")
test_import("core.logging", "Logging")

print("\nRuntime:")
test_import("runtime.launcher", "System launcher")
test_import("runtime.lifecycle", "Lifecycle manager")

print("\nState Management:")
test_import("state.mission_state", "Mission state")
test_import("state.state_store_sqlite", "State store")

print("\nModel Runtime:")
test_import("model_runtime.manager", "Model manager")
test_import("model_runtime.download", "Model downloader")
test_import("model_runtime.serving.local_api", "Local API")
test_import("model_runtime.serving.router", "Model router")

print("\nExecution:")
test_import("execution.codegen.code_engine", "Code engine")
test_import("execution.orchestrator.mission_controller", "Mission controller")
test_import("execution.testing.test_execution", "Test executor")

print("\nCognition:")
test_import("cognition.planning.planner_engine", "Planner engine")
test_import("cognition.planning.task_graph", "Task graph")

print("\nWorkspace:")
test_import("workspace.manager", "Workspace manager")

print("\nInterface:")
test_import("interface.api.server", "API server")
test_import("interface.cli.deepforge", "CLI")

print("\n" + "=" * 60)
print("  CONNECTION TESTS")
print("=" * 60)
print()

def test_system_launch():
    try:
        from runtime.launcher import launch_system
        launch_system(skip_bootstrap=True)
        return True
    except Exception as e:
        return False

test_connection("System launch", test_system_launch)
def test_service_registry():
    try:
        from core.registry import get_service
        return get_service("model_manager") is not None
    except:
        return False

def test_event_bus():
    try:
        from core.events import get_event_bus
        return get_event_bus() is not None
    except:
        return False

test_connection("Service registry", test_service_registry)
test_connection("Event bus", test_event_bus)

print("\n" + "=" * 60)
if errors:
    print(f"  FAILED: {len(errors)} errors")
    print("=" * 60)
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print("  ALL TESTS PASSED")
    print("=" * 60)
    sys.exit(0)

