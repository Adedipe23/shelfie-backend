import logging
from typing import List

from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


async def send_email_notification(
    email: str,
    subject: str,
    message: str,
) -> None:
    """
    Send an email notification.

    In a real application, this would use an email service like SendGrid or SMTP.
    For now, we'll just log the email details.

    Args:
        email: Recipient email address
        subject: Email subject
        message: Email message body
    """
    logger.info(f"Sending email to {email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Message: {message}")
    # In a real application, you would send the email here
    logger.info(f"Email sent to {email}")


def send_low_stock_notifications(
    background_tasks: BackgroundTasks,
    emails: List[str],
    product_name: str,
    current_stock: int,
) -> None:
    """
    Send low stock notifications to multiple recipients.

    Args:
        background_tasks: FastAPI BackgroundTasks
        emails: List of recipient email addresses
        product_name: Name of the product with low stock
        current_stock: Current stock level
    """
    subject = f"Low Stock Alert: {product_name}"
    message = (
        f"The stock level for {product_name} is low. Current stock: {current_stock}"
    )

    for email in emails:
        background_tasks.add_task(
            send_email_notification,
            email=email,
            subject=subject,
            message=message,
        )
