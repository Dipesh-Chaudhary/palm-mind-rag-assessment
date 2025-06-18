import smtplib
from email.message import EmailMessage
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import Booking
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def schedule_interview(
    db: AsyncSession,
    full_name: str,
    email: str,
    interview_date: str,
    interview_time: str
) -> str:
    """
    Saves booking information to the database and sends a confirmation email.
    """
    logger.info(f"Attempting to book interview for {full_name} at {email}")

    # 1. Save booking details to PostgreSQL
    try:
        new_booking = Booking(
            full_name=full_name,
            email=email,  # Fixed indentation
            interview_date=interview_date,
            interview_time=interview_time
        )
        db.add(new_booking)
        await db.commit()
        await db.refresh(new_booking)
        logger.info(f"Successfully saved booking {new_booking.id} to database.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error while booking interview: {e}")
        return f"Failed to save booking to database: {e}"

    # 2. Send confirmation email
    try:
        msg = EmailMessage()
        email_content = (
            f"Dear {full_name},\n\n"
            f"This email confirms your interview slot with Palm Mind Technology.\n\n"
            f"Date: {interview_date}\n"
            f"Time: {interview_time}\n\n"
            f"We look forward to speaking with you.\n\n"
            f"Best regards,\n"
            f"The Palm Mind Technology HR Team"
        )
        msg.set_content(email_content)
        msg["Subject"] = "Interview Confirmation - Palm Mind Technology"
        msg["From"] = settings.SMTP_SENDER_EMAIL

        msg["To"] = email

        # Use a try-except block for SMTP operations
        try:
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_SENDER_EMAIL, settings.SMTP_SENDER_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Successfully sent confirmation email to {email}")
            return "Interview booked successfully. A confirmation email has been sent."
        except smtplib.SMTPException as smtp_error:
            logger.error(f"SMTP error while sending confirmation: {smtp_error}")
            return f"Booking saved, but failed to send confirmation email: {smtp_error}"

    except Exception as e:
        logger.error(f"General error while sending confirmation: {e}")
        return f"Booking saved, but failed to send confirmation email: {e}"
