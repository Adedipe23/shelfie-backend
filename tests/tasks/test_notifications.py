"""
Tests for notification tasks.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest
from fastapi import BackgroundTasks

from app.tasks.notifications import (
    send_email_notification,
    send_low_stock_notifications,
)


@pytest.mark.tasks
@pytest.mark.asyncio
async def test_send_email_notification():
    """Test sending email notification."""
    email = "test@example.com"
    subject = "Test Subject"
    message = "Test message body"

    # Mock the logger to capture log messages
    with patch("app.tasks.notifications.logger") as mock_logger:
        await send_email_notification(email, subject, message)

        # Verify all expected log calls were made
        expected_calls = [
            (f"Sending email to {email}",),
            (f"Subject: {subject}",),
            (f"Message: {message}",),
            (f"Email sent to {email}",),
        ]

        # Check that logger.info was called with expected messages
        assert mock_logger.info.call_count == 4
        for i, expected_call in enumerate(expected_calls):
            actual_call = mock_logger.info.call_args_list[i]
            assert actual_call[0] == expected_call


@pytest.mark.tasks
@pytest.mark.asyncio
async def test_send_email_notification_with_special_characters():
    """Test sending email notification with special characters."""
    email = "test+special@example.com"
    subject = "Test Subject with émojis 🚀"
    message = "Test message with special chars: àáâãäå"

    with patch("app.tasks.notifications.logger") as mock_logger:
        await send_email_notification(email, subject, message)

        # Verify the function handles special characters correctly
        assert mock_logger.info.call_count == 4

        # Check that the special characters are preserved in log messages
        calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert f"Sending email to {email}" in calls
        assert f"Subject: {subject}" in calls
        assert f"Message: {message}" in calls
        assert f"Email sent to {email}" in calls


@pytest.mark.tasks
def test_send_low_stock_notifications_single_email():
    """Test sending low stock notifications to a single email."""
    # Create a mock BackgroundTasks
    background_tasks = MagicMock(spec=BackgroundTasks)

    emails = ["manager@example.com"]
    product_name = "Test Product"
    current_stock = 5

    # Call the function
    send_low_stock_notifications(background_tasks, emails, product_name, current_stock)

    # Verify add_task was called once
    assert background_tasks.add_task.call_count == 1

    # Verify the task was added with correct parameters
    call_args = background_tasks.add_task.call_args
    assert call_args[0][0] == send_email_notification  # First arg is the function

    # Check keyword arguments
    kwargs = call_args[1]
    assert kwargs["email"] == "manager@example.com"
    assert kwargs["subject"] == f"Low Stock Alert: {product_name}"
    assert (
        kwargs["message"]
        == f"The stock level for {product_name} is low. Current stock: {current_stock}"
    )


@pytest.mark.tasks
def test_send_low_stock_notifications_multiple_emails():
    """Test sending low stock notifications to multiple emails."""
    background_tasks = MagicMock(spec=BackgroundTasks)

    emails = ["manager1@example.com", "manager2@example.com", "admin@example.com"]
    product_name = "Critical Product"
    current_stock = 2

    send_low_stock_notifications(background_tasks, emails, product_name, current_stock)

    # Verify add_task was called for each email
    assert background_tasks.add_task.call_count == len(emails)

    # Verify each call has the correct email
    for i, email in enumerate(emails):
        call_args = background_tasks.add_task.call_args_list[i]
        kwargs = call_args[1]
        assert kwargs["email"] == email
        assert kwargs["subject"] == f"Low Stock Alert: {product_name}"
        assert (
            kwargs["message"]
            == f"The stock level for {product_name} is low. Current stock: {current_stock}"
        )


@pytest.mark.tasks
def test_send_low_stock_notifications_empty_email_list():
    """Test sending low stock notifications with empty email list."""
    background_tasks = MagicMock(spec=BackgroundTasks)

    emails = []
    product_name = "Test Product"
    current_stock = 0

    send_low_stock_notifications(background_tasks, emails, product_name, current_stock)

    # Verify add_task was not called
    assert background_tasks.add_task.call_count == 0


@pytest.mark.tasks
def test_send_low_stock_notifications_zero_stock():
    """Test sending low stock notifications with zero stock."""
    background_tasks = MagicMock(spec=BackgroundTasks)

    emails = ["urgent@example.com"]
    product_name = "Out of Stock Product"
    current_stock = 0

    send_low_stock_notifications(background_tasks, emails, product_name, current_stock)

    # Verify the message includes zero stock
    call_args = background_tasks.add_task.call_args
    kwargs = call_args[1]
    assert "Current stock: 0" in kwargs["message"]


@pytest.mark.tasks
def test_send_low_stock_notifications_message_format():
    """Test the format of low stock notification messages."""
    background_tasks = MagicMock(spec=BackgroundTasks)

    emails = ["test@example.com"]
    product_name = "Widget ABC-123"
    current_stock = 15

    send_low_stock_notifications(background_tasks, emails, product_name, current_stock)

    call_args = background_tasks.add_task.call_args
    kwargs = call_args[1]

    # Verify subject format
    expected_subject = f"Low Stock Alert: {product_name}"
    assert kwargs["subject"] == expected_subject

    # Verify message format
    expected_message = (
        f"The stock level for {product_name} is low. Current stock: {current_stock}"
    )
    assert kwargs["message"] == expected_message


@pytest.mark.tasks
def test_send_low_stock_notifications_with_special_product_name():
    """Test low stock notifications with special characters in product name."""
    background_tasks = MagicMock(spec=BackgroundTasks)

    emails = ["test@example.com"]
    product_name = "Café Latté & Espresso™"
    current_stock = 3

    send_low_stock_notifications(background_tasks, emails, product_name, current_stock)

    call_args = background_tasks.add_task.call_args
    kwargs = call_args[1]

    # Verify special characters are preserved
    assert product_name in kwargs["subject"]
    assert product_name in kwargs["message"]


@pytest.mark.tasks
@pytest.mark.asyncio
async def test_send_email_notification_logging_levels():
    """Test that email notification uses correct logging level."""
    email = "test@example.com"
    subject = "Test"
    message = "Test message"

    # Mock the logger and verify info level is used
    with patch("app.tasks.notifications.logger") as mock_logger:
        await send_email_notification(email, subject, message)

        # Verify only info level was used (not debug, warning, error, etc.)
        assert mock_logger.info.called
        assert not mock_logger.debug.called
        assert not mock_logger.warning.called
        assert not mock_logger.error.called


@pytest.mark.tasks
def test_notifications_module_logger():
    """Test that the notifications module has correct logger configuration."""
    from app.tasks.notifications import logger

    # Verify logger is configured correctly
    assert logger.name == "app.tasks.notifications"
    assert isinstance(logger, logging.Logger)
