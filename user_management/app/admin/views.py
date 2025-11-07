import datetime
from flask import (
    Flask, Blueprint, abort, flash, redirect, render_template, request, 
    url_for, jsonify, send_file, make_response, current_app, Response, stream_with_context
)

from flask_login import current_user, login_required, LoginManager, UserMixin, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm

import csv
import json
from io import StringIO, BytesIO
import os
from sqlalchemy.exc import IntegrityError
from dateutil.parser import parse as parse_date
import uuid

from rq import Queue
from flask_sqlalchemy import SQLAlchemy
from flask_sse import sse

from app import db, rq as flask_rq
from app.admin.forms import (
    ChangeAccountTypeForm,
    ChangeUserEmailForm,
    ChangeUserPhoneForm,
    InviteUserForm,
    NewUserForm,
    AddURLForm,
    ImportForm,
)
from app.decorators import admin_required
from app.email import send_email
from app.models import EditableHTML, Role, User, URL
from app.apicall import deactivate_api_key, register_api_key

from email_validator import validate_email, EmailNotValidError
import phonenumbers
import time

admin = Blueprint('admin', __name__)

# Use flask-rq2's get_queue which handles Redis connection properly
def get_queue():
    return flask_rq.get_queue()

current_dir = os.path.dirname(os.path.abspath(__file__))

@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    return render_template('admin/index.html')

@admin.route('/blacklist', methods=['GET', 'POST'])
@login_required
@admin_required
def blacklist():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    highlight = request.args.get('highlight')
    highlight = int(highlight) if highlight and highlight.isdigit() else None
    
    # เปลี่ยนการเรียงลำดับเป็นตามวันที่อย่างเดียว
    db.session.expire_all()
    # urls = URL.query.order_by(URL.date_added.desc()).paginate(page=page, per_page=per_page)
    urls = URL.query.order_by(URL.date_added.desc(), URL.id.asc()).paginate(page=page, per_page=per_page)

    # print(str(URL.query.order_by(URL.date_added.desc()).statement))

    
    form = AddURLForm()
    import_form = ImportForm()
    return render_template('admin/blacklist.html', urls=urls, form=form, import_form=import_form, highlight=highlight)

@admin.route('/blacklist/add', methods=['POST'])
@login_required
@admin_required
def blacklist_add_url():
    form = AddURLForm()
    if form.validate_on_submit():
        url = form.url.data
        category = form.category.data
        reason = form.reason.data
        source = form.source.data

        existing_url = URL.query.filter_by(url=url).first()
        if existing_url:
            flash('URL already exists', 'error')
            return redirect(url_for('admin.blacklist'))
        
        new_url = URL(url=url, category=category, reason=reason, source=source, date_added=db.func.current_date())
        db.session.add(new_url)
        db.session.commit()
        
        flash('URL added successfully', 'success')
        return redirect(url_for('admin.blacklist'))
    else:
        flash('Invalid input', 'error')
        return redirect(url_for('admin.blacklist'))

@admin.route('/blacklist/remove/<int:id>')
@login_required
@admin_required
def blacklist_remove_url(id):
    url = db.session.get(URL, id)
    if url is None:
        abort(404)
    db.session.delete(url)
    db.session.commit()

    flash('URL removed successfully', 'success')
    return redirect(url_for('admin.blacklist'))

@admin.route('/blacklist/toggle/<int:id>')
@login_required
@admin_required
def blacklist_toggle_status(id):
    url = db.session.get(URL, id)
    if url is None:
        abort(404)
    url.status = not url.status
    db.session.commit()

    # รับเฉพาะค่า page
    page = request.args.get('page', 1, type=int)
    
    flash('Status updated successfully', 'success')
    # ส่งเฉพาะ page และ highlight กลับไป
    return redirect(url_for('admin.blacklist', page=page, highlight=id))

@admin.route('/blacklist/search', methods=['GET'])
@login_required
@admin_required
def blacklist_search():
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    urls = URL.query.filter(
        (URL.url.like(f'%{query}%')) |
        (URL.category.like(f'%{query}%')) |
        (URL.reason.like(f'%{query}%')) |
        (URL.source.like(f'%{query}%'))
    ).paginate(page=page, per_page=per_page)
    form = AddURLForm()
    import_form = ImportForm()
    return render_template('admin/blacklist.html', urls=urls, query=query, form=form, import_form=import_form)

@admin.route('/blacklist/export/<format>', methods=['GET'])
@login_required
@admin_required
def blacklist_export_data(format):
    urls = URL.query.all()
    if format == 'csv':
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['url', 'category', 'date_added', 'reason', 'source', 'status'])
        for url in urls:
            cw.writerow([url.url, url.category, url.date_added, url.reason, url.source, url.status])
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=urls.csv"
        output.headers["Content-type"] = "text/csv"
        flash('CSV exported successfully', 'success')
        return output
    elif format == 'json':
        data = [{'url': url.url, 'category': url.category, 'date_added': str(url.date_added), 
                 'reason': url.reason, 'source': url.source, 'status': url.status} for url in urls]
        output = BytesIO(json.dumps(data, indent=2).encode('utf-8'))
        flash('JSON exported successfully', 'success')
        return send_file(output, mimetype='application/json', as_attachment=True, download_name='urls.json')
    else:
        flash('Invalid format', 'error')
        return redirect(url_for('admin.blacklist'))


@admin.route('/blacklist/import', methods=['POST'])
@login_required
@admin_required
def blacklist_import_data():
    form = ImportForm()
    if form.validate_on_submit():
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('admin.blacklist'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('admin.blacklist'))
        
        try:
            count = 0
            if file and file.filename.endswith('.csv'):
                stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)
                total_rows = sum(1 for row in csv_reader)
                stream.seek(0)
                csv_reader = csv.DictReader(stream)

                for row in csv_reader:
                    existing_url = URL.query.filter_by(url=row['url']).first()
                    if existing_url:
                        continue
                    url = URL(url=row['url'], category=row['category'], 
                            date_added=parse_date(row['date_added']).date(), 
                            reason=row['reason'], source=row['source'], status=row['status'] in ['1', 'True'])
                    db.session.add(url)
                    count += 1
                    # คำนวณเปอร์เซ็นต์
                    percent = int((count / total_rows) * 100)
                    if count % 100 == 0:
                        # time.sleep(0.2)
                        sse.publish({"message": percent, "count": count, "total_rows": total_rows}, type='progress')

                db.session.commit()
                sse.publish({"message": "complete", "count": count, "total_rows": total_rows}, type='progress')
                ## ให้ฝั่ง client เรียกแทน ไม่รู้อันไหนดีกว่ากัน
                ## return redirect(url_for('admin.blacklist'))
            elif file and file.filename.endswith('.json'):
                data = json.load(file)
                total_rows = len(data)
                for item in data:
                    existing_url = URL.query.filter_by(url=item['url']).first()
                    if existing_url:
                        continue
                    url = URL(url=item['url'], category=item['category'], 
                            date_added=parse_date(item['date_added']).date(), 
                            reason=item['reason'], source=item['source'], status=item['status'])
                    db.session.add(url)
                    count += 1
                    percent = int((count / total_rows) * 100)
                    if count % 100 == 0:
                        sse.publish({"message": percent, "count": count, "total_rows": total_rows}, type='progress')

                db.session.commit()
                sse.publish({"message": "complete", "count": count, "total_rows": total_rows}, type='progress')
                ## ให้ฝั่ง client เรียกแทน ไม่รู้อันไหนดีกว่ากัน
                ## return redirect(url_for('admin.blacklist'))
            else:
                sse.publish({"message": "error: Invalid file format"}, type='progress')
                flash('Invalid file format', 'error')
                return redirect(url_for('admin.blacklist'))
                
        except IntegrityError:
            db.session.rollback()
            sse.publish({"message": "error: An error occurred while importing data"}, type='progress')
            flash('An error occurred while importing data', 'error')
            return redirect(url_for('admin.blacklist'))
            
        except Exception as e:
            sse.publish({"message": f"error:{str(e)}"}, type='progress')
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('admin.blacklist'))

    return redirect(url_for('admin.blacklist'))


@admin.route('/new-user', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        uid = uuid.uuid4().hex
        user = User(
            confirmed=True,
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            uid=uid,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        register_api_key(uid, role_id=form.role.data.id)  # Use role_id as the ID
        flash('User {} successfully created'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        uid = uuid.uuid4().hex
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            uid=uid)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user.id,
            token=token,
            _external=True)
        get_queue().enqueue(
            send_email,
            recipient=user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=user,
            invite_link=invite_link,
        )
        flash('User {} successfully invited'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/users')
@login_required
@admin_required
def registered_users():
    """View all registered users."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template(
        'admin/registered_users.html', users=users, roles=roles)


@admin.route('/user/<int:user_id>')
@admin.route('/user/<int:user_id>/info')
@login_required
@admin_required
def user_info(user_id):
    """View a user's profile."""
    user = User.query.filter_by(id=user_id).first()
    try:
        validate_email(user.email, check_deliverability=False)
        email_or_phone = user.email
        is_email = True
    except EmailNotValidError:
        # Handle invalid email
        # It is the UID in the email, it is the user who registered with the phone number. 
        # bring phone number information to display instead.
        phone_number = phonenumbers.parse(user.phone_number, "TH")
        phone_number = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.NATIONAL)
        email_or_phone = phone_number
        is_email = False
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user, email_or_phone=email_or_phone, is_email=is_email, form=None)


@admin.route('/user/<int:user_id>/change-email', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_email(user_id):
    """Change a user's email."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    form = ChangeUserEmailForm()
    if form.validate_on_submit():
        user.email = form.email.data
        db.session.add(user)
        db.session.commit()
        flash('Email for user {} successfully changed to {}.'.format(
            user.full_name(), user.email), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form, is_email=True)

@admin.route('/user/<int:user_id>/change-phone', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_phone(user_id):
    """Change a user's email."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    form = ChangeUserPhoneForm()
    if form.validate_on_submit():
        user.phone_number = form.phone_number.data
        db.session.add(user)
        db.session.commit()
        flash('Phone for user {} successfully changed to {}.'.format(
            user.full_name(), user.email), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form, is_email=False)

@admin.route(
    '/user/<int:user_id>/change-account-type', methods=['GET', 'POST'])
@login_required
@admin_required
def change_account_type(user_id):
    """Change a user's account type."""
    if current_user.id == user_id:
        flash('You cannot change the type of your own account. Please ask '
              'another administrator to do this.', 'error')
        return redirect(url_for('admin.user_info', user_id=user_id))

    user = User.query.get(user_id)
    if user is None:
        abort(404)
    form = ChangeAccountTypeForm()
    if form.validate_on_submit():
        user.role = form.role.data
        db.session.add(user)
        db.session.commit()
        # must send to fastapi api_key, role_id
        api_key = user.uid
        role_id = user.role.id
        message, status = register_api_key(api_key, role_id)
        if status == 200:
            pass
        else:
            flash(message, 'error')
        # 
        flash('Role for user {} successfully changed to {}.'.format(
            user.full_name(), user.role.name), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)

@admin.route('/user/<int:user_id>/apikey-delete')
@login_required
@admin_required
def delete_api_key(user_id):
    user = User.query.filter_by(id=user_id).first()
    api_key = user.uid
    # call fastapi for deactivate api_key
    message, status = deactivate_api_key(api_key)
    flash(message + ': {}'.format(status), 'info')
    return redirect(url_for('admin.registered_users'))


# สร้าง form เพื่อจะลบผู้ใช้งาน
@admin.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)

# ถ้ายืนยัน ก็จะส่งมาให้ลบออก
@admin.route('/user/<int:user_id>/_delete')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if current_user.id == user_id:
        flash('You cannot delete your own account. Please ask another '
              'administrator to do this.', 'error')
    else:
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            flash('User not found. The user may have already been deleted.', 'error')
        else:
            try:    
                db.session.delete(user)
                db.session.commit()
                flash('Successfully deleted user %s.' % user.full_name(), 'success')
            except Exception as e:
                db.session.rollback()  # ย้อนกลับการเปลี่ยนแปลงถ้าเกิดข้อผิดพลาด
                flash('An error occurred while trying to delete the user. Please try again.', 'error')
    return redirect(url_for('admin.registered_users'))


@admin.route('/_update_editor_contents', methods=['POST'])
@login_required
@admin_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.query.filter_by(
        editor_name=editor_name).first()
    if editor_contents is None:
        editor_contents = EditableHTML(editor_name=editor_name)
    editor_contents.value = edit_data

    db.session.add(editor_contents)
    db.session.commit()

    return 'OK', 200

@admin.route('/delete-unconfirmed-users', methods=['POST'])
@login_required
@admin_required
def delete_unconfirmed_users():
    # Define the threshold (e.g., users unconfirmed for more than 7 days)
    threshold_date = datetime.utcnow() - datetime.timedelta(days=7)
    unconfirmed_users = User.query.filter(
        User.confirmed == False,
        User.created_at < threshold_date
    ).all()
    
    for user in unconfirmed_users:
        db.session.delete(user)
    db.session.commit()