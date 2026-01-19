"""
Tests for Task 1.1: Backend Project Structure Setup
Tests acceptance criteria from docs/tasks.md
"""

import os
import sys


def test_fastapi_imports():
    """Test that FastAPI app imports successfully"""
    try:
        # Temporarily disable config validation for import test
        os.environ.setdefault("SENTRY_AUTH_TOKEN", "test")
        os.environ.setdefault("SENTRY_ORG", "test")
        os.environ.setdefault("SENTRY_PROJECT", "test")
        os.environ.setdefault("OPENAI_API_KEY", "test")
        os.environ.setdefault("SLACK_BOT_TOKEN", "test")
        os.environ.setdefault("SLACK_SIGNING_SECRET", "test")
        os.environ.setdefault("APP_PASSWORD", "test")

        from main import app
        assert app is not None
        assert app.title == "LogLens API"
        assert app.version == "0.1.0"
        print("✓ FastAPI app imports successfully")
        return True
    except Exception as e:
        print(f"✗ FastAPI import failed: {e}")
        return False


def test_config_loads_env_vars():
    """Test that config loads environment variables"""
    try:
        # Set all required environment variables
        os.environ["SENTRY_AUTH_TOKEN"] = "test_token"
        os.environ["SENTRY_ORG"] = "test_org"
        os.environ["SENTRY_PROJECT"] = "test_project"
        os.environ["OPENAI_API_KEY"] = "test_key"
        os.environ["SLACK_BOT_TOKEN"] = "test_bot_token"
        os.environ["SLACK_SIGNING_SECRET"] = "test_secret"
        os.environ["APP_PASSWORD"] = "test_password"

        from config import Config
        config = Config()

        assert config.SENTRY_AUTH_TOKEN == "test_token"
        assert config.SENTRY_ORG == "test_org"
        assert config.OPENAI_API_KEY == "test_key"
        print("✓ Config loads environment variables correctly")
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def test_config_raises_error_on_missing_vars():
    """Test that config raises error when environment variables are missing"""
    try:
        # Clear environment variables
        env_backup = os.environ.copy()
        for key in ["SENTRY_AUTH_TOKEN", "SENTRY_ORG", "SENTRY_PROJECT",
                    "OPENAI_API_KEY", "SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET",
                    "APP_PASSWORD"]:
            os.environ.pop(key, None)

        # Force reload of config module
        if 'config' in sys.modules:
            del sys.modules['config']

        try:
            from config import Config
            Config()
            print("✗ Config should raise error for missing variables")
            os.environ.update(env_backup)
            return False
        except ValueError as e:
            if "Missing required environment variables" in str(e):
                print("✓ Config raises error for missing variables")
                os.environ.update(env_backup)
                return True
            else:
                print(f"✗ Wrong error message: {e}")
                os.environ.update(env_backup)
                return False
    except Exception as e:
        print(f"✗ Missing vars test failed: {e}")
        return False


def test_directory_structure():
    """Test that all required directories and files exist"""
    required_files = [
        "main.py",
        "config.py",
        "requirements.txt",
        "sentry_client.py",
        "analyzer.py",
        "slack_bot.py",
    ]

    required_dirs = [
        "docs",
    ]

    all_exist = True

    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")
            all_exist = False

    for dir in required_dirs:
        if os.path.isdir(dir):
            print(f"✓ {dir}/ directory exists")
        else:
            print(f"✗ {dir}/ directory missing")
            all_exist = False

    # Check root level files
    root_files = ["../.env.example", "../.gitignore"]
    for file in root_files:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")
            all_exist = False

    return all_exist


if __name__ == "__main__":
    print("\n=== Running Task 1.1 Setup Tests ===\n")

    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    results = []

    print("--- Test: Directory Structure ---")
    results.append(test_directory_structure())

    print("\n--- Test: FastAPI Imports ---")
    results.append(test_fastapi_imports())

    print("\n--- Test: Config Loads Variables ---")
    results.append(test_config_loads_env_vars())

    print("\n--- Test: Config Validates Variables ---")
    results.append(test_config_raises_error_on_missing_vars())

    print("\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed! Task 1.1 acceptance criteria met.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        sys.exit(1)
