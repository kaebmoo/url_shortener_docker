from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.url.forms import URLShortenForm
import requests
from flask_wtf.csrf import CSRFError
from qrcodegen import QrCode
from PIL import Image
import io
import base64

from app.models import EditableHTML
from app.utils import generate_qr_code

shorten = Blueprint('shorten', __name__)

# Custom error handler for CSRF token expiration
@shorten.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('errors/400.html'), 400
    # return render_template('errors/403.html', reason=e.description), 400

def get_user_url_count():
    app_path = current_app.config['APP_PATH']
    app_host_name = current_app.config['APP_HOST']
    shortener_host = current_app.config['SHORTENER_HOST']

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-KEY': current_user.uid  # ใส่ API key ของคุณ ยกเลิกการใช้การอ่านจาก session 
    }

    try:
        
        response = requests.get(shortener_host + '/user/url_count', headers=headers)
        data = response.json()
        if response.status_code == 200:
            url_count = data.get('url_count', 0)
            return url_count
        else:
            return 'Failed to retrieve URL count.'
    except requests.exceptions.ConnectionError:
        return 'Failed to connect to the server. Please try again later.'
    except requests.exceptions.RequestException as req_err:
        return f'An error occurred: {req_err}'
    
@shorten.route('/generate_qr_code')
def generate_qr_code_endpoint():
    data = request.args.get('data')
    if data:
        qr_code = generate_qr_code(data)
        return jsonify({'qr_code': qr_code})
    return jsonify({'error': 'Missing data parameter'}), 400

@shorten.route('/admin/<secret_key>', methods=['DELETE'])
@login_required
def delete_url(secret_key):
    app_path = current_app.config['APP_PATH']
    app_host_name = current_app.config['APP_HOST']
    shortener_host = current_app.config['SHORTENER_HOST']
    
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-KEY': current_user.uid  # Assuming you are passing the API key in the session
    }
    try:
        response = requests.delete(f'{shortener_host}/admin/{secret_key}', headers=headers)
        if response.status_code == 200:
            flash('URL deleted successfully', 'success')
        else:
            flash('Failed to delete URL', 'danger')

        return redirect(url_for('shorten.shorten_url'))
    except:
        flash('Failed to delete URL', 'danger')
        return redirect(url_for('shorten.shorten_url'))

@shorten.route('/admin/<secret_key>', methods=['GET'])
@login_required
def get_url_info(secret_key):
    app_path = current_app.config['APP_PATH']
    app_host_name = current_app.config['APP_HOST']
    shortener_host = current_app.config['SHORTENER_HOST']
    
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-KEY': current_user.uid  # Assuming you are passing the API key in the session
    }
    try:
        response = requests.get(f'{shortener_host}/admin/{secret_key}', headers=headers)
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'title': data.get('title', ''),
                'favicon_url': data.get('favicon_url')
            })
        else:
            return jsonify({'error': f"Failed to retrieve data from FastAPI, status code: {response.status_code}"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@shorten.route('/shorten', methods=['GET', 'POST'])
@login_required
def shorten_url():
    app_path = current_app.config['APP_PATH']
    app_host_name = current_app.config['APP_HOST']
    shortener_host = current_app.config['SHORTENER_HOST']

    url_data = None
    message = None  # กำหนดค่าเริ่มต้น
    short_url = None  # กำหนดค่าเริ่มต้น
    qr_code_base64 = None
    url_count = get_user_url_count()
    # สร้างข้อความแจ้งจำนวน URL ที่สร้างแล้ว ทั้งภาษาไทยและภาษาอังกฤษ
    url_count_message_th = f"คุณได้สร้าง URL แล้วทั้งหมด {url_count} รายการ"
    url_count_message_en = f"You have created a total of {url_count} URLs"
    
    api_key = current_user.uid

    form = URLShortenForm()
    if form.validate_on_submit():
        original_url = form.original_url.data
        custom_key = form.custom_key.data if current_user.is_vip_or_admin() else None  # Check if user is VIP or admin 

        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'X-API-KEY': current_user.uid   # ใส่ API key ของคุณ 
        }

        # Check URL count for the user
        try:
            response = requests.get(shortener_host + '/user/url_count', headers=headers)
            info = response.json()
            if response.status_code == 200:
                url_count = info.get('url_count', 0)
                url_count_message_en = f"You have created a total of {url_count} URLs"
                if url_count >= 50 and not current_user.is_vip_or_admin():
                    flash('You have reached the limit of 50 URLs. Please upgrade to VIP Plan for unlimited access.', 'warning')
                    return render_template('url/shorten.html', form=form, shortener_host=shortener_host, url_data=url_data, qr_code_base64=qr_code_base64, url_count_message=url_count_message_en)
            else:
                flash('Failed to retrieve URL count.', 'danger')
                return render_template('url/shorten.html', form=form, shortener_host=shortener_host, url_data=url_data, qr_code_base64=qr_code_base64, url_count_message=url_count_message_en)
        except requests.exceptions.ConnectionError:
            flash('Failed to connect to the server. Please try again later.', 'error')
            return render_template('url/shorten.html', form=form, shortener_host=shortener_host, url_data=url_data, qr_code_base64=qr_code_base64, url_count_message=url_count_message_en)
        except requests.exceptions.RequestException as req_err:
            flash(f'An error occurred: {req_err}', 'error')
            return render_template('url/shorten.html', form=form, shortener_host=shortener_host, url_data=url_data, qr_code_base64=qr_code_base64, url_count_message=url_count_message_en)

        data = {
            'target_url': original_url
        }
        if custom_key:  # Only add custom key if it exists
            data['custom_key'] = custom_key
        try:
            response = requests.post(shortener_host + '/url', headers=headers, json=data)
            url_data = response.json()
            if response.status_code == 200:
                short_url = url_data.get('url', 'No URL returned')
                message = url_data.get('message', 'Successfully created')
                flash(f'{message}: {short_url}', 'success')
                qr_code_base64 = generate_qr_code(short_url)

                if isinstance(url_count, (int, float)):
                    url_count += 1
                else:
                    url_count = int(url_count) + 1

                url_count_message_en = f"You have created a total of {url_count} URLs"

                # if 'persistent_messages' not in session:
                #     session['persistent_messages'] = []
                # session['persistent_messages'] = message
                # session.modified = True  # เพื่อให้แน่ใจว่า session ถูกบันทึก
            elif response.status_code == 409:
                # status_code 409 "A short link for this website already exists."
                short_url = url_data.get('url', 'No URL returned')
                message = url_data.get('message','')
                qr_code_base64 = generate_qr_code(short_url)
                flash(f'{message}', 'warning')
            elif response.status_code == 400:
                message = url_data.get('detail', '')
                flash('Error 400 Bad Request', 'error')
            else:
                message = url_data.get('detail', '')
                flash('Failed to shorten URL.', 'danger')
        except requests.exceptions.ConnectionError:
            flash('Failed to connect to the server. Please try again later.', 'error')
        except requests.exceptions.HTTPError as http_err:
            flash(f'HTTP error occurred: {http_err}', 'error')
        except requests.exceptions.RequestException as req_err:
            flash(f'An error occurred: {req_err}', 'error')
        except Exception as e:
            flash(f'An unexpected error occurred: {e}', 'error')
        ## return redirect(url_for('main.shorten'))
    # persistent_messages = session.get('persistent_messages', [])
    # return render_template('url/shorten.html', form=form, shortener_host=shortener_host, message=message, short_url=short_url, qr_code_base64=qr_code_base64, url_count_message=url_count_message_en)
    return render_template('url/shorten.html', form=form, shortener_host=shortener_host, url_data=url_data, qr_code_base64=qr_code_base64, url_count_message=url_count_message_en, api_key=api_key)
    
    
