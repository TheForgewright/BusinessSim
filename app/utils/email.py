"""
Email utility functions
"""
from flask import current_app, render_template
from flask_mail import Message
from app import mail
from threading import Thread


def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, text_body, html_body):
    """
    Send email with both text and HTML bodies

    Args:
        subject: Email subject line
        recipients: List of recipient email addresses
        text_body: Plain text email body
        html_body: HTML email body
    """
    msg = Message(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=recipients if isinstance(recipients, list) else [recipients]
    )
    msg.body = text_body
    msg.html = html_body

    # Send asynchronously to avoid blocking
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_invitation_email(player, token):
    """
    Send invitation email to a new participant

    Args:
        player: Player object
        token: Verification token for setting password
    """
    app_url = current_app.config['APP_URL']
    set_password_url = f"{app_url}/auth/set-password/{token}"

    subject = "Invitation to Business Simulation Game"
    text_body = render_template(
        'email/invitation.txt',
        player=player,
        set_password_url=set_password_url
    )
    html_body = render_template(
        'email/invitation.html',
        player=player,
        set_password_url=set_password_url
    )

    send_email(subject, player.email, text_body, html_body)


def send_password_reset_email(player, token):
    """
    Send password reset email

    Args:
        player: Player object
        token: Password reset token
    """
    app_url = current_app.config['APP_URL']
    reset_url = f"{app_url}/auth/reset-password/{token}"

    subject = "Password Reset Request - Business Simulation Game"
    text_body = render_template(
        'email/password_reset.txt',
        player=player,
        reset_url=reset_url
    )
    html_body = render_template(
        'email/password_reset.html',
        player=player,
        reset_url=reset_url
    )

    send_email(subject, player.email, text_body, html_body)


def send_welcome_email(player):
    """
    Send welcome email after successful registration

    Args:
        player: Player object
    """
    subject = "Welcome to Business Simulation Game"
    text_body = render_template('email/welcome.txt', player=player)
    html_body = render_template('email/welcome.html', player=player)

    send_email(subject, player.email, text_body, html_body)
