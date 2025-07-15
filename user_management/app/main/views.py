from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_wtf.csrf import CSRFError
from flask_login import current_user, login_required
import requests
from urllib.parse import urlparse
import asyncio

from app.models import EditableHTML
from app.main.forms import URLActionForm
from app.utils import generate_qr_code, convert_to_localtime, capture_screenshot, validate_and_correct_url, validate_url
from app.apicall import get_user_urls, get_url_scan_status

main = Blueprint('main', __name__)

# Custom error handler for CSRF token expiration
@main.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('errors/400.html'), 400

def convert_scan_results_to_localtime(scan_results):
    if isinstance(scan_results, tuple):
        # Assume the first element of the tuple is the list of scan results
        scan_results_list = scan_results[0]
    else:
        scan_results_list = scan_results

    for index, result in enumerate(scan_results_list):
        # print(f"Processing item {index}: {result} (type: {type(result)})")
        if isinstance(result, dict) and 'timestamp' in result:
            # original_timestamp = result['timestamp']
            result['timestamp'] = convert_to_localtime(result['timestamp'])
            # print(f"Converted {original_timestamp} to {result['timestamp']}")
        else:
            print(f"Item {index} does not have a timestamp or is not a dictionary.")


@main.route('/generate_qr_code')
@login_required
def generate_qr_code_endpoint():
    data = request.args.get('data')
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    qr_code_base64 = generate_qr_code(data)
    return jsonify({'qr_code': qr_code_base64})

@main.route('/')
def index():
    app_path = current_app.config['APP_PATH']
    app_host_name = current_app.config['APP_HOST']
    shortener_host = current_app.config['SHORTENER_HOST']
    shortener_host_name = current_app.config['SHORTENER_HOST_NAME']

    if current_user.is_authenticated:
        
        # user_urls = get_user_urls()
        # url_count = len(user_urls)

        # จัดเรียงลิสต์ตาม 'created_at' โดยให้วันที่ใหม่ที่สุดมาก่อน
        # sorted_user_urls = sorted(user_urls, key=lambda x: x['created_at'], reverse=True)
        
        return render_template('main/index.html', app_path=app_path, shortener_host=shortener_host, shortener_host_name=shortener_host_name, app_host_name=app_host_name)
    return render_template('main/index.html', app_path=app_path, shortener_host=current_app.config['SHORTENER_HOST'], app_host_name=app_host_name, shortener_host_name=shortener_host_name)

@main.route("/capture_screenshot", methods=["POST"])
def capture_screenshot_route():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    url = validate_and_correct_url(url)
    if validate_url(url):
        try:
            screenshot_path, destination_url, status = asyncio.run(capture_screenshot(url))
        except Exception as e:
            print(f"An error occurred: {e}")
            return jsonify({"error": "Unable to capture screenshot."}), 500
    else:
        return jsonify({"error": "Invalid URL provided"}), 400
    
    return jsonify({"screenshot_path": screenshot_path, "url": destination_url})

@main.route("/preview_url", methods=["GET"])
def preview_url():
    app_path = current_app.config['APP_PATH']

    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    url = validate_and_correct_url(url)
    if not validate_url(url):
        return jsonify({"error": "Invalid URL provided"}), 400
    
    return render_template("main/preview.html", url=url, app_path=app_path)

'''@main.route("/preview_url_", methods=["GET"])
def preview_url_():
    url = request.args.get("url")  # รับ URL ผ่าน query parameter
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    url = validate_and_correct_url(url)  # ตรวจสอบและแก้ไข URL
    if validate_url(url):
        try:
            screenshot_path, destination_url, status = asyncio.run(capture_screenshot(url))
        except Exception as e:
            print(f"An error occurred: {e}")
            screenshot_path = None
    else:
        return jsonify({"error": "Invalid URL provided"}), 400
    
    if not screenshot_path:
        return jsonify({"error": "Unable to capture screenshot. The page took too long to load."}), 500
    
    # Render HTML template and pass the screenshot path and URL to it
    return render_template("main/preview.html", screenshot=screenshot_path, url=destination_url)'''

@main.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    app_path = current_app.config['APP_PATH']
    app_host_name = current_app.config['APP_HOST']
    shortener_host = current_app.config['SHORTENER_HOST']
    shortener_host_name = current_app.config['SHORTENER_HOST_NAME']

    url_action_form = URLActionForm()
    scan_results = None  # Initialize scan_results to None
    # Initialize scan_results_list to a default value
    scan_results_list = []

    user_urls = get_user_urls()
    url_count = len(user_urls)
    # จัดเรียงลิสต์ตาม 'created_at' โดยให้วันที่ใหม่ที่สุดมาก่อน
    ## sorted_user_urls = sorted(user_urls, key=lambda x: x['created_at'], reverse=True)

    # Convert 'created_at' and 'updated_at' to local time
    for url in user_urls:
        url['created_at'] = convert_to_localtime(url['created_at'])
        url['updated_at'] = convert_to_localtime(url['updated_at'])

    # print("Form data:", request.form)  # Debug print

    if url_action_form.validate_on_submit() and 'url_secret_key' in request.form:
        url_secret_key = request.form['url_secret_key']
        api_key = current_user.uid
        target_url = request.form['target_url']

        if 'submit_info' in request.form:
            scan_results = get_url_scan_status(secret_key=url_secret_key, api_key=api_key, target_url=target_url, scan_type=None)
            if scan_results is None:
                flash('Failed to retrieve scan status', 'danger')
            else:
                # Convert timestamps to local time
                # Ensure scan_results is not None and is a tuple
                if scan_results is not None and isinstance(scan_results, tuple):
                    # Convert timestamps to local time
                    convert_scan_results_to_localtime(scan_results)

                    # Access the first element of scan_results
                    scan_results_list = scan_results[0]
                else:
                    # Handle the case where scan_results is None or not a tuple
                    scan_results_list = []

                # Added: Attach the scan results to the URL
                # Optimize attaching scan results to the URL
                matching_url = next((url for url in user_urls if url['secret_key'] == url_secret_key), None)
                if matching_url:
                    matching_url['scan_results'] = scan_results
        
        elif 'submit_delete' in request.form:
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
                'X-API-KEY': current_user.uid
            }
            response = requests.delete(f'{shortener_host}/admin/{url_action_form.url_secret_key.data}', headers=headers)
            if response.status_code == 200:
                flash('URL deleted successfully', 'success')
            else:
                flash('Failed to delete URL', 'danger')
            
            return redirect(url_for('main.user'))
    
    return render_template('main/user.html', user_urls=user_urls, app_path=app_path, shortener_host=shortener_host, shortener_host_name=shortener_host_name, app_host_name=app_host_name, url_count=url_count, url_action_form=url_action_form, scan_results=scan_results_list)

@main.route('/vip', methods=['GET', 'POST'])
@login_required
def vip():
    url_action_form = URLActionForm()
    scan_results = None  # Initialize scan_results to None
    # Initialize scan_results_list to a default value
    scan_results_list = []
    
    app_path = current_app.config['APP_PATH']
    app_host_name = current_app.config['APP_HOST']
    shortener_host = current_app.config['SHORTENER_HOST']
    shortener_host_name = current_app.config['SHORTENER_HOST_NAME']

    user_urls = get_user_urls()
    url_count = len(user_urls)

    # จัดเรียงลิสต์ตาม 'created_at' โดยให้วันที่ใหม่ที่สุดมาก่อน
    ## sorted_user_urls = sorted(user_urls, key=lambda x: x['created_at'], reverse=True)
    ## ให้การจัดเรียงเป็นหน้าที่ทางฝั่ง html แทน
    ## sorted_user_urls = user_urls

    # Convert 'created_at' and 'updated_at' to local time
    for url in user_urls:
        url['created_at'] = convert_to_localtime(url['created_at'])
        url['updated_at'] = convert_to_localtime(url['updated_at'])

    if url_action_form.validate_on_submit() and 'url_secret_key' in request.form:
        url_secret_key = request.form['url_secret_key']
        api_key = current_user.uid
        target_url = request.form['target_url']

        # print("Request form data:", request.form)

        if 'submit_info' in request.form:
            scan_results = get_url_scan_status(secret_key=url_secret_key, api_key=api_key, target_url=target_url, scan_type=None)
            if scan_results is None:
                flash('Failed to retrieve scan status', 'danger')
            else:
                # Convert timestamps to local time
                 # Ensure scan_results is not None and is a tuple
                if scan_results is not None and isinstance(scan_results, tuple):
                    # Convert timestamps to local time
                    convert_scan_results_to_localtime(scan_results)

                    # Access the first element of scan_results
                    scan_results_list = scan_results[0]
                else:
                    # Handle the case where scan_results is None or not a tuple
                    scan_results_list = []


                # Added: Attach the scan results to the URL
                # Optimize attaching scan results to the URL
                matching_url = next((url for url in user_urls if url['secret_key'] == url_secret_key), None)
                if matching_url:
                    matching_url['scan_results'] = scan_results

        elif 'submit_delete' in request.form:            
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
                'X-API-KEY': current_user.uid
            }
            response = requests.delete(f'{shortener_host}/admin/{url_action_form.url_secret_key.data}', headers=headers)
            if response.status_code == 200:
                flash('URL deleted successfully', 'success')
            else:
                flash('Failed to delete URL', 'danger')
            return redirect(url_for('main.vip'))

    return render_template('main/vip.html', user_urls=user_urls, app_path=app_path, shortener_host=shortener_host, shortener_host_name=shortener_host_name, app_host_name=app_host_name, url_count=url_count, url_action_form=url_action_form, scan_results=scan_results_list)

@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)
