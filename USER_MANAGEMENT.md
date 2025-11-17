# User Management System

This document describes the new email-based user management system for the Business Simulation Game.

## Overview

The system now implements a secure, email-based authentication flow with the following features:

- **Email-based authentication** - All users are identified by their email address
- **Invitation system** - Professors can invite participants via email
- **Password reset** - Users can reset their passwords via email
- **First-time login setup** - Users set their username on first login
- **Professor self-registration** - Professors can register directly
- **Participant invitation-only** - Students must be invited by a professor

## User Roles

### Professor
- Can self-register with email and password
- Has full access to game management
- Can invite and manage participants
- Can view all participants and their status

### Participant (Student)
- Cannot self-register
- Must be invited by a professor via email
- Sets password via invitation link
- Chooses username on first login
- Can participate in games

## Authentication Flow

### For Professors

1. Navigate to `/auth/register`
2. Enter username, email, and password
3. Account is created as a professor
4. Can immediately login and access professor dashboard

### For Participants

1. Professor invites participant via `/professor/participants/invite`
2. Participant receives invitation email with a secure link
3. Participant clicks link and sets their password
4. Participant logs in with email/password
5. On first login, participant is prompted to set a username
6. Participant can now access the student dashboard

## Password Reset Flow

1. User navigates to `/auth/request-reset`
2. Enters their email address
3. Receives password reset email with secure link (valid for 1 hour)
4. Clicks link and sets new password
5. Can login with new password

## Email Configuration

The system requires email configuration to send invitation and password reset emails.

### Environment Variables

Set the following environment variables (or update `config.py`):

```bash
# Email Server Configuration
MAIL_SERVER=smtp.gmail.com          # Your SMTP server
MAIL_PORT=587                        # SMTP port (usually 587 for TLS)
MAIL_USE_TLS=true                    # Enable TLS
MAIL_USERNAME=your-email@gmail.com   # SMTP username
MAIL_PASSWORD=your-app-password      # SMTP password
MAIL_DEFAULT_SENDER=noreply@businesssim.com  # From address
APP_URL=http://localhost:5000        # Application URL
```

### Gmail Setup Example

If using Gmail:

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password as `MAIL_PASSWORD`

### Development Mode

For development/testing, you can use a local mail server or console output:

```bash
# Install a development mail server
pip install aiosmtpd

# Run it
python -m aiosmtpd -n -c aiosmtpd.handlers.Debugging -l localhost:1025
```

Then configure:
```bash
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=false
```

## Database Migration

### For New Installations

Simply run the seed script:

```bash
python seed_data.py
```

This will create:
- Demo professor account (professor@example.com, password: password)
- Demo student accounts (student@example.com, alice@example.com, bob@example.com)

### For Existing Installations

If you have an existing database, you'll need to:

1. **Backup your database** first!
2. Delete the old database file: `rm data/business_sim.db`
3. Run the application to create new tables: `python run.py`
4. Run the seed script: `python seed_data.py`

Note: This will lose existing data. For production, use a proper migration tool like Flask-Migrate.

## API Changes

### Player Model

New fields:
- `email` (required, unique)
- `email_verified` (boolean)
- `last_login` (datetime)
- `verification_token` (string)
- `verification_token_expiry` (datetime)
- `password_reset_token` (string)
- `password_reset_token_expiry` (datetime)
- `needs_username_setup` (boolean)

Changed fields:
- `username` - Now nullable (set on first login)
- `password_hash` - Now nullable (set via invitation)

### New Routes

#### Authentication
- `GET/POST /auth/login` - Login with email or username
- `GET/POST /auth/register` - Professor registration only
- `GET/POST /auth/set-password/<token>` - Set password from invitation
- `GET/POST /auth/setup-username` - First-time username setup
- `GET/POST /auth/request-reset` - Request password reset
- `GET/POST /auth/reset-password/<token>` - Reset password
- `GET /auth/logout` - Logout

#### Professor Participant Management
- `GET /professor/participants` - View all participants
- `GET/POST /professor/participants/invite` - Invite new participant
- `POST /professor/participants/<id>/resend-invitation` - Resend invitation
- `POST /professor/participants/<id>/delete` - Delete participant

## Security Features

- **Secure tokens** - Using `secrets.token_urlsafe()` for all tokens
- **Token expiration** - Invitation tokens expire in 24 hours, reset tokens in 1 hour
- **Password hashing** - Using Werkzeug's password hashing
- **Email enumeration protection** - Password reset always shows success message
- **HTTPS recommended** - Use HTTPS in production
- **Session-based auth** - Secure session management

## Templates

New templates created:
- `auth/set_password.html` - Set password from invitation
- `auth/setup_username.html` - First-time username setup
- `auth/request_reset.html` - Request password reset
- `auth/reset_password.html` - Reset password form
- `professor/participants.html` - Participant management
- `professor/invite_participant.html` - Invite participant form
- `email/invitation.html` - Invitation email (HTML)
- `email/invitation.txt` - Invitation email (text)
- `email/password_reset.html` - Password reset email (HTML)
- `email/password_reset.txt` - Password reset email (text)
- `email/welcome.html` - Welcome email (HTML)
- `email/welcome.txt` - Welcome email (text)

Updated templates:
- `auth/login.html` - Now accepts email or username
- `auth/register.html` - Now requires email, professor-only
- `professor/dashboard.html` - Added participant management link

## Testing the System

### Test Professor Account
- Email: professor@example.com
- Password: password

### Test Student Accounts
- Email: student@example.com, alice@example.com, bob@example.com
- Password: password

### Test Invitation Flow

1. Login as professor
2. Navigate to "Manage Participants"
3. Click "Invite New Participant"
4. Enter a test email
5. Check your email for the invitation
6. Click the link and set password
7. Login and set username

### Test Password Reset

1. Navigate to login page
2. Click "Forgot your password?"
3. Enter your email
4. Check your email for reset link
5. Click link and set new password
6. Login with new password

## Troubleshooting

### Emails not sending

- Check `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` are set correctly
- Check firewall/network allows SMTP connections
- Check email provider allows SMTP (some require app passwords)
- Check application logs for error messages

### "Email already registered" error

- Each email must be unique
- Check if the email is already in the database
- Use the professor participants page to view all registered emails

### Token expired

- Invitation tokens expire after 24 hours
- Password reset tokens expire after 1 hour
- Professor can resend invitation from participants page

### Can't login after setting password

- Make sure you set a username on first login
- Try using your email address instead of username
- Check that email verification completed successfully

## Future Enhancements

Potential improvements:
- Email verification for professors
- Two-factor authentication
- Password strength requirements
- Account lockout after failed attempts
- Audit logging
- Classroom/section management
- Bulk invitation import (CSV)
- User roles and permissions
- OAuth/SSO integration

## Support

For issues or questions, please refer to the main project documentation or contact your system administrator.
