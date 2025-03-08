from flask import current_app, render_template, request
from flask_mail import Message
from app import mail


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    msg = Message(
        'Reset Your Password',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email]
    )

    reset_url = f"{request.url_root}auth/reset-password/{token}"
    
    msg.body = f'''To reset your password click on the following link:

{reset_url}

If you did not request a password reset, simply ignore this message.
'''
    
    msg.html = f'''
<p>To reset your password click on the following link:</p>
<p><a href="{reset_url}">Click here to reset your password</a></p>
<p>If you did not request a password reset, simply ignore this message.</p>
'''
    
    mail.send(msg) 