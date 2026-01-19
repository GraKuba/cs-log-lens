"""
Tests for knowledge base files (Task 1.2)
"""
import os
from pathlib import Path


def test_workflow_file_exists():
    """Test that workflow.md exists and is readable"""
    workflow_path = Path(__file__).parent / "docs" / "workflow.md"
    assert workflow_path.exists(), "workflow.md should exist"
    assert workflow_path.is_file(), "workflow.md should be a file"

    # Test readability
    content = workflow_path.read_text()
    assert len(content) > 0, "workflow.md should not be empty"


def test_known_errors_file_exists():
    """Test that known_errors.md exists and is readable"""
    known_errors_path = Path(__file__).parent / "docs" / "known_errors.md"
    assert known_errors_path.exists(), "known_errors.md should exist"
    assert known_errors_path.is_file(), "known_errors.md should be a file"

    # Test readability
    content = known_errors_path.read_text()
    assert len(content) > 0, "known_errors.md should not be empty"


def test_workflow_contains_expected_sections():
    """Test that workflow.md contains expected sections"""
    workflow_path = Path(__file__).parent / "docs" / "workflow.md"
    content = workflow_path.read_text()

    # Check for expected sections
    assert "# Expected User Flows" in content, "Should have main heading"
    assert "## Checkout Flow" in content, "Should have Checkout Flow section"
    assert "## Login Flow" in content, "Should have Login Flow section"
    assert "### Expected Behaviors" in content, "Should have Expected Behaviors sections"

    # Check for key behaviors from tech spec
    assert "Session timeout" in content, "Should document session timeout"
    assert "Payment tokens" in content, "Should document payment token behavior"


def test_known_errors_contains_expected_sections():
    """Test that known_errors.md contains expected sections"""
    known_errors_path = Path(__file__).parent / "docs" / "known_errors.md"
    content = known_errors_path.read_text()

    # Check for expected sections
    assert "# Known Error Patterns" in content, "Should have main heading"
    assert "## Template" in content, "Should have Template section"
    assert "## Example Entry" in content, "Should have Example Entry section"

    # Check for template fields
    assert "**Sentry Error:**" in content, "Should have Sentry Error field"
    assert "**Root Cause:**" in content, "Should have Root Cause field"
    assert "**User Impact:**" in content, "Should have User Impact field"
    assert "**Resolution:**" in content, "Should have Resolution field"
    assert "**Customer Response:**" in content, "Should have Customer Response field"

    # Check for example entry
    assert "Payment Token Expired" in content, "Should have example error"
    assert "PaymentTokenExpiredError" in content, "Should have example Sentry error"


def test_files_are_properly_formatted():
    """Test that files are properly formatted markdown"""
    workflow_path = Path(__file__).parent / "docs" / "workflow.md"
    known_errors_path = Path(__file__).parent / "docs" / "known_errors.md"

    workflow_content = workflow_path.read_text()
    known_errors_content = known_errors_path.read_text()

    # Check that files start with headers
    assert workflow_content.startswith("#"), "workflow.md should start with header"
    assert known_errors_content.startswith("#"), "known_errors.md should start with header"

    # Check for proper line breaks (not excessive)
    assert "\n\n\n\n" not in workflow_content, "workflow.md should not have excessive line breaks"
    assert "\n\n\n\n" not in known_errors_content, "known_errors.md should not have excessive line breaks"


if __name__ == "__main__":
    # Run tests
    test_workflow_file_exists()
    test_known_errors_file_exists()
    test_workflow_contains_expected_sections()
    test_known_errors_contains_expected_sections()
    test_files_are_properly_formatted()

    print("✅ All knowledge base tests passed!")
