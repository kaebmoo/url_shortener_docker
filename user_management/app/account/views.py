""" User management: register new user, password, email, phone, register confirm """

from flask import Blueprint, flash, redirect, render_template, request, url_for, session, current_app
from flask_login import current_user, login_required, login_user, logout_user

from rq import Queue
# from flask_rq import get_queue <-- deprecated

from app import db
from app.account.forms import (
    ChangeEmailForm, ChangePhoneForm, ChangePasswordForm, 
    CreatePasswordForm, LoginForm, RegistrationFormSelect, 
    RegistrationForm, PhoneNumberForm, RequestResetPasswordForm, 
    ResetPasswordForm, OTPForm, 
)
from app.email import send_email
from app.models import User
# from app.utils import generate_otp
from app.sms import send_otp
from app.apicall import register_api_key, create_jwt_token, create_refresh_token

# Import OTPService
from app.otp_service import OTPService

from werkzeug.security import check_password_hash, generate_password_hash
import uuid
from email_validator import validate_email, EmailNotValidError
import phonenumbers

from redis import Redis

account = Blueprint('account', __name__)

# Create a Redis connection (adjust the parameters accordingly) RQ_DEFAULT_HOST RQ_DEFAULT_PORT
redis_connection = Redis(host='127.0.0.1', port=6379, db=0)

# Create a queue using the Redis connection
queue = Queue(connection=redis_connection)
# Configure the connection to the queue (e.g., Redis)
## queue = Queue(connection='redis://localhost:6379')  # Replace with your actual connection details

# get_queue() is deprecated use queue instead.

# Create an instance of OTPService
otp_service = OTPService()

@account.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user."""
    form = LoginForm()
    if form.validate_on_submit():
        login_method = request.form.get('login_method')
        if login_method == 'email':
            user = User.query.filter_by(email=form.email.data).first()
        else:
            user = User.query.filter_by(phone_number=form.phone_number.data).first()

        if user is not None and user.password_hash is not None and \
                user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash('You are now logged in. Welcome back!', 'success')
            # เก็บค่า uid, email, phone, หรืออื่น อื่น ใน session
            session['uid'] = user.uid
            access_token = create_jwt_token()
            session['access_token'] = access_token

            return redirect(request.args.get('next') or url_for('main.index'))
        else:
            flash('Invalid email, phone or password.', 'error')
    return render_template('account/login.html', form=form)

@account.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationFormSelect()
    if form.validate_on_submit():
        registration_type = form.registration_type.data
        if registration_type == 'email':
            return redirect(url_for('account.register_email'))
        else:
            return redirect(url_for('account.register_phone'))
    return render_template('account/register_select.html', form=form)

@account.route('/register_email', methods=['GET', 'POST'])
def register_email():
    """Register a new user, and send them a confirmation email."""
    form = RegistrationForm()
    if form.validate_on_submit():
        uid = uuid.uuid4().hex
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number = '',
            email=form.email.data,
            uid = uid,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        confirm_link = url_for('account.confirm', token=token, _external=True)

        queue.enqueue(
            send_email,
            recipient=user.email,
            subject='Confirm Your Account',
            template='account/email/confirm',
            user=user,
            confirm_link=confirm_link)
        flash(f'A confirmation link has been sent to {user.email}.', 'warning')
        return redirect(url_for('main.index'))
    return render_template('account/register.html', form=form)

@account.route('/register_phone', methods=['GET', 'POST'])
def register_phone():
    """Register a new user by phone, and send them a confirmation OTP."""
    form = PhoneNumberForm()
    if form.validate_on_submit():
        # add user here
        # Generate a unique user ID
        uid = uuid.uuid4().hex

        # Create the user with 'confirmed=False'
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data,
            email=uid,  # Placeholder email if not using email
            uid=uid,
            password=form.password.data,  # Ensure password hashing is handled in the model
            confirmed=False
        )
        db.session.add(user)
        db.session.commit()

        # otp = generate_otp()
        # Generate OTP using OTPService
        otp = otp_service.generate_otp(form.phone_number.data, expiration=90)
        queue.enqueue(send_otp, phone_number=form.phone_number.data, otp=otp) # send_otp(phone_number, otp)

        # Store the phone number in session to identify the user in the next step
        session['phone_number'] = form.phone_number.data

        flash('An OTP has been sent to your phone number. Please enter it to confirm your account.', 'warning')

        return redirect(url_for('account.verify_otp'))
    return render_template('account/register_phone.html', form=form)


@account.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@account.route('/manage', methods=['GET', 'POST'])
@account.route('/manage/info', methods=['GET', 'POST'])
@login_required
def manage():
    """Display a user's account information."""
    try:
        validate_email(current_user.email, check_deliverability=False)
        email_or_phone = current_user.email
        is_email = True
    except EmailNotValidError:
        # Handle invalid email
        # It is the UID in the email, it is the user who registered with the phone number. 
        # bring phone number information to display instead.
        phone_number = phonenumbers.parse(current_user.phone_number, "TH")
        phone_number = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.NATIONAL)
        email_or_phone = phone_number
        is_email = False
    return render_template('account/manage.html', user=current_user, email_or_phone=email_or_phone, is_email=is_email, form=None)


@account.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Respond to existing user's request to reset their password."""
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_password_reset_token()
            reset_link = url_for(
                'account.reset_password', token=token, _external=True)
            queue.enqueue(
                send_email,
                recipient=user.email,
                subject='Reset Your Password',
                template='account/email/reset_password',
                user=user,
                reset_link=reset_link,
                next=request.args.get('next'))
        flash(f'A password reset link has been sent to {form.email.data}.', 'warning')
        return redirect(url_for('account.login'))
    return render_template('account/reset_password.html', form=form)


@account.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset an existing user's password."""
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('Invalid email address.', 'form-error')
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.new_password.data):
            flash('Your password has been updated.', 'form-success')
            return redirect(url_for('account.login'))
        else:
            flash('The password reset link is invalid or has expired.',
                  'form-error')
            return redirect(url_for('main.index'))
    return render_template('account/reset_password.html', form=form)


@account.route('/manage/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change an existing user's password."""
    form = ChangePasswordForm()
    try:
        validate_email(current_user.email, check_deliverability=False)
        is_email = True
    except EmailNotValidError:
        # Handle invalid email
        # It is the UID in the email, it is the user who registered with the phone number. 
        # bring phone number information to display instead.
        is_email = False
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.', 'form-success')
            return redirect(url_for('main.index'))
        else:
            flash('Original password is invalid.', 'form-error')
    return render_template('account/manage.html', form=form, is_email=is_email)


@account.route('/manage/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    """Respond to existing user's request to change their email."""
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            change_email_link = url_for(
                'account.change_email', token=token, _external=True)
            queue.enqueue(
                send_email,
                recipient=new_email,
                subject='Confirm Your New Email',
                template='account/email/change_email',
                # current_user is a LocalProxy, we want the underlying user
                # object
                user=current_user._get_current_object(),
                change_email_link=change_email_link)
            flash('A confirmation link has been sent to {}.'.format(new_email),
                  'warning')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.', 'form-error')
    return render_template('account/manage.html', form=form, is_email=True)

@account.route('/manage/change-phone', methods=['GET', 'POST'])
@login_required
def change_phone_request():
    """Respond to existing user's request to change their phone number."""
    form = ChangePhoneForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            session['user_id'] = current_user.id
            new_phone = form.phone_number.data
            session['new_phone_number'] = new_phone

            # send otp to confirm new phone number
            # otp = generate_otp()
            # Generate OTP using OTPService
            otp = otp_service.generate_otp(new_phone, expiration=90)

            session['otp'] = otp
            queue.enqueue(send_otp, phone_number=new_phone, otp=otp)
            
            flash(f'A confirmation OTP has been sent to {new_phone}.','warning')
            return redirect(url_for('account.confirm_phone_change'))
        else:
            flash('Invalid password.', 'form-error')
    return render_template('account/manage.html', form=form, is_email=False)

@account.route('/manage/change-email/<token>', methods=['GET', 'POST'])
@login_required
def change_email(token):
    """Change existing user's email with provided token."""
    if current_user.change_email(token):
        flash('Your email address has been updated.', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'error')
    return redirect(url_for('main.index'))


@account.route('/confirm-account')
@login_required
def confirm_request():
    """Respond to new user's request to confirm their account."""
    token = current_user.generate_confirmation_token()
    confirm_link = url_for('account.confirm', token=token, _external=True)
    queue.enqueue(
        send_email,
        recipient=current_user.email,
        subject='Confirm Your Account',
        template='account/email/confirm',
        # current_user is a LocalProxy, we want the underlying user object
        user=current_user._get_current_object(),
        confirm_link=confirm_link)
    flash('A new confirmation link has been sent to {}.'.format(
        current_user.email), 'warning')
    return redirect(url_for('main.index'))

@account.route('/confirm-otp')
@login_required
def otp_request():
    """Respond to new user's request for a new OTP."""
    phone_number = session.get('phone_number')

    if not phone_number:
        flash('Session expired. Please start the registration process again.', 'error')
        return redirect(url_for('account.register_phone'))
    
    # Generate new OTP using OTPService
    otp = otp_service.generate_otp(phone_number, expiration=90)

    # Enqueue sending the OTP via SMS
    queue.enqueue(send_otp, phone_number=phone_number, otp=otp)

    flash(f'A new otp has been sent to {phone_number}.', 'warning')
    
    return redirect(url_for('account.verify_otp'))


@account.route('/confirm-account/<token>')
@login_required
def confirm(token):
    """Confirm new user's account with provided token."""
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm_account(token):
        flash('Your account has been confirmed.', 'success')
        # send uid as api_key to fastapi here. email register confirmed.
        register_api_key(current_user.uid, current_user.role_id)
    else:
        flash('The confirmation link is invalid or has expired.', 'error')
    return redirect(url_for('main.index'))

@account.route('/confirm_phone_change', methods=['GET', 'POST'])
def confirm_phone_change():
    """Respond to existing user's request to change their phone number."""
    form = OTPForm()
    
    new_phone_number = session.get('new_phone_number')
    # ใช้ otp_service เพื่อดึงเวลาที่เหลือสำหรับ OTP นี้
    time_remaining = int(otp_service.get_time_remaining(new_phone_number))
    
    if form.validate_on_submit():
        entered_otp = form.otp.data

        if not new_phone_number:
            flash('Session expired. Please try changing your phone number again.', 'error')
            return redirect(url_for('account.change_phone_request'))
        
        # Use OTPService to confirm the OTP
        if otp_service.confirm_otp(new_phone_number, entered_otp):
            # OTP is valid; update the user's phone number
            current_user.phone_number = new_phone_number
            db.session.commit()
            
            # Clean up session data
            session.pop('new_phone_number', None)
            
            flash('Your phone number has been successfully updated.', 'success')
            return redirect(url_for('account.manage'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'error')
    return render_template('account/verify_otp.html', form=form, time_remaining=time_remaining)

# for register user by phone
@account.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    """Confirm new user's account (register by phone) with provided otp."""
    form = OTPForm()
    # ดึงหมายเลขโทรศัพท์จาก session หรือจากผู้ใช้
    phone_number = session.get('phone_number')

    # ใช้ otp_service เพื่อดึงเวลาที่เหลือสำหรับ OTP นี้
    time_remaining = int(otp_service.get_time_remaining(phone_number))
    
    if time_remaining <= 0:
        flash('Your OTP has expired. Please request a new OTP.', 'warning')
        return redirect(url_for('account.otp_request'))
    
    if form.validate_on_submit():
        entered_otp = form.otp.data

        if not phone_number:
            flash('Session expired. Please start the registration process again.', 'error')
            return redirect(url_for('account.register_phone'))
        
        # Use OTPService to confirm the OTP
        if otp_service.confirm_otp(phone_number, entered_otp):
            # OTP is valid; retrieve the user from the database
            user = User.query.filter_by(phone_number=phone_number).first()
            if user is None:
                flash('User not found. Please register again.', 'error')
                return redirect(url_for('account.register_phone'))
            
            # Activate the user's account
            user.confirmed = True
            db.session.commit()
            
            # Log in the user
            login_user(user)

            # Clean up session data
            session.pop('phone_number', None)
            flash('Your phone number has been verified and your account is activated.', 'success')

            # Send API key or perform any additional setup
            register_api_key(user.uid, user.role_id)

            return redirect(url_for('main.index'))  # Adjust to your dashboard route
        else:
            flash('Invalid or Expired OTP.', 'error')
            # if invalid ask user -> need to regen otp?
            
    return render_template('account/verify_otp.html', form=form, time_remaining=time_remaining)


@account.route(
    '/join-from-invite/<int:user_id>/<token>', methods=['GET', 'POST'])
def join_from_invite(user_id, token):
    """
    Confirm new user's account with provided token and prompt them to set
    a password.
    """
    if current_user is not None and current_user.is_authenticated:
        flash('You are already logged in.', 'error')
        return redirect(url_for('main.index'))

    new_user = User.query.get(user_id)
    if new_user is None:
        return redirect(404)

    if new_user.password_hash is not None:
        flash('You have already joined.', 'error')
        return redirect(url_for('main.index'))

    if new_user.confirm_account(token):
        form = CreatePasswordForm()
        if form.validate_on_submit():
            new_user.password = form.password.data
            db.session.add(new_user)
            db.session.commit()
            # send api_key, role_id to fastapi
            register_api_key(new_user.uid, new_user.role_id)
            #
            flash('Your password has been set. After you log in, you can '
                  'go to the "Your Account" page to review your account '
                  'information and settings.', 'success')
            return redirect(url_for('account.login'))
        return render_template('account/join_invite.html', form=form)
    else:
        flash('The confirmation link is invalid or has expired. Another '
              'invite email with a new link has been sent to you.', 'error')
        token = new_user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user_id,
            token=token,
            _external=True)
        queue.enqueue(
            send_email,
            recipient=new_user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=new_user,
            invite_link=invite_link)
    return redirect(url_for('main.index'))


'''@account.before_app_request
def before_request():
    """Force user to confirm email before accessing login-required routes."""
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint[:8] != 'account.' \
            and request.endpoint != 'static':
        return redirect(url_for('account.unconfirmed'))'''
    
@account.before_app_request
def before_request():
    """Force user to confirm phone number or email before accessing login-required routes."""
    if current_user.is_authenticated:
        # Check if user is confirmed
        if not current_user.confirmed:
            if request.endpoint is not None \
                    and request.endpoint[:8] != 'account.' \
                    and request.endpoint != 'static':

                # ตรวจสอบว่าผู้ใช้ลงทะเบียนด้วยอีเมลหรือหมายเลขโทรศัพท์
                if current_user.email and current_user.email != current_user.uid:
                    # ผู้ใช้ลงทะเบียนด้วยอีเมล ให้รีไดเร็กไปยังหน้า unconfirmed
                    flash('Please confirm your account with the link sent to your email.', 'warning')
                    return redirect(url_for('account.unconfirmed'))

                # ผู้ใช้ลงทะเบียนด้วยหมายเลขโทรศัพท์
                phone_number = session.get('phone_number')
                if phone_number:
                    # ใช้ OTPService เพื่อคำนวณเวลาที่เหลือของ OTP
                    time_remaining = otp_service.get_time_remaining(phone_number)
                    if time_remaining is None or time_remaining <= 0:
                        # ถ้า OTP หมดอายุ ให้รีไดเร็กไปขอ OTP ใหม่
                        flash('Your OTP has expired. A new OTP has been generated and sent.', 'warning')
                        return redirect(url_for('account.otp_request'))

                    # ถ้า OTP ยังไม่หมดอายุ ให้ผู้ใช้ยืนยัน OTP
                    flash(f'Please confirm your account with the OTP sent to your phone. Time remaining: {int(time_remaining)} seconds.', 'warning')
                    return redirect(url_for('account.verify_otp'))

                # ถ้าไม่มี phone_number ใน session ให้เริ่มต้นกระบวนการลงทะเบียนใหม่
                flash('Session expired. Please start the registration process again.', 'error')
                return redirect(url_for('account.register_phone'))



@account.route('/unconfirmed')
def unconfirmed():
    """Catch users with unconfirmed emails."""
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('account/unconfirmed.html')


