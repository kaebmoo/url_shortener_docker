
---

# URL Shortener with User Management

This project is a URL shortener web application with user management functionalities, built using Flask. It includes features such as user registration, login, email notifications, and URL shortening.

## Features

- **User registration and authentication**: Users can sign up, log in, and manage their profiles. Authentication is handled securely using Flask-Login.
- **Email notifications**: The application supports email notifications for activities like account activation and password reset, using Flask-Mail.
- **URL shortening**: Users can shorten long URLs, which are then stored in the database for later retrieval.
- **Asset pipeline management**: Assets such as CSS and JavaScript files are managed through Flask-Assets.
- **SSL configuration**: SSL is supported for secure connections, configurable via the application's settings.
- **Task queue management with Redis Queue (RQ)**: Background tasks, such as sending emails and processing URLs, are handled asynchronously using Redis Queue.

## Project Structure

- **`assets/`**: Contains CSS and JavaScript assets.
  - **`scripts/`**: JavaScript files used across the application.
    - **`vendor/`**: Third-party JavaScript libraries used in the application.
  - **`styles/`**: CSS files used for styling the application.
    - **`vendor/`**: Third-party CSS libraries for consistent UI/UX.
  
- **`app/`**: Main application folder containing blueprints for different modules.
  - **`account/`**: Manages user account functionalities like registration, login, and profile updates.
  - **`admin/`**: Admin panel routes for managing users and viewing application statistics.
  - **`main/`**: Contains the main application routes, such as the home page and about page.
  - **`url/`**: Handles URL shortening functionalities, including creating and managing shortened URLs.
  
- **`config/`**: Contains configuration files for different environments (development, testing, production).
  
- **`models/`**: Defines the database models using SQLAlchemy, including user and URL models.
  
- **`public/`**: Holds public assets accessible directly from the web.
  - **`styles/`**: Public-facing stylesheets.
  - **`webassets-external/`**: External web assets used in the public-facing part of the application.
  
- **`static/`**: Static files served directly by Flask.
  - **`ckeditor/`**: Includes CKEditor assets, such as plugins and skins for rich text editing.
    - **`plugins/`**: Various CKEditor plugins for additional functionalities like image uploads and special character insertion.
    - **`skins/`**: Visual skins for CKEditor, such as the flat design.
  - **`fonts/`**: Fonts used across the application, including third-party fonts from Semantic UI.
  - **`images/`**: Images used in the application, including those from Semantic UI.
  - **`screenshots/`**: Directory for storing screenshots generated or uploaded within the application.
  - **`styles/`**: Contains additional CSS files for custom styling.
  - **`webassets-external/`**: External assets specifically for the web UI components.
  
- **`templates/`**: Jinja2 templates for rendering HTML pages.
  - **`account/`**: Templates related to user account management, such as login, registration, and password reset.
    - **`email/`**: Email templates for sending HTML emails to users.
  - **`admin/`**: Templates for the admin panel, where administrators can manage the application.
  - **`errors/`**: Templates for error pages (404, 500).
  - **`layouts/`**: Base layout templates for consistent header, footer, and overall page structure.
  - **`macros/`**: Jinja2 macros for reusable HTML components across the templates.
  - **`main/`**: Templates for the main parts of the site, like the homepage and about page.
  - **`partials/`**: Small template fragments used in multiple pages, such as navigation bars or sidebars.
  - **`url/`**: Templates specifically for URL shortening functionalities.

- **`utils/`**: Utility functions that provide additional support across the application, such as saving images and sending emails.

## Installation

### Prerequisites

- Python 3.6+
- Flask
- Flask-Assets
- Flask-Compress
- Flask-Login
- Flask-Mail
- Flask-RQ2
- Flask-SQLAlchemy
- Flask-WTF
- Redis (for task queue management)

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/kaebmoo/url_shortener.git
   cd url_shortener/user_management/app
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   ```bash
   export FLASK_CONFIG=development
   ```

5. Initialize the database:

   ```bash
   flask db upgrade
   ```

6. Run the application:

   ```bash
   flask run
   ```
   
   Or use Gunicorn for production:

   ```bash
   gunicorn manage:app
   ```

   For the task worker:

   ```bash
   python -u manage.py run_worker
   ```

## Configuration

The application can be configured using environment variables or by modifying the `config.py` file. The available configurations are:

- `development`
- `testing`
- `production`

Environment variables to consider:
- `FLASK_ENV`: Set to `development`, `testing`, or `production` to select the appropriate configuration.
- `SECRET_KEY`: A secure secret key for session management.
- `SQLALCHEMY_DATABASE_URI`: The URI for the database connection.

## Usage

After setting up and running the application, you can access it in your web browser at `http://127.0.0.1:5000/`. You can register a new user, log in, and start shortening URLs.

## Task Queue

The application uses Redis Queue (RQ) for background task processing. To start a worker, run the following command in a separate terminal:

```bash
redis-server
rq worker --with-scheduler
```

## SSL Configuration

For production environments, SSL is configured if the platform supports it. Ensure to set `SSL_DISABLE` to `False` in the configuration.

## Acknowledgments

This project is adapted from the [flask-base](https://github.com/hack4impact/flask-base) project by Hack4Impact. 

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/hack4impact/flask-base/blob/master/LICENSE.md) file for details.

## Additional Resources

- [Flask](https://flask.palletsprojects.com/)
- [Redis Queue (RQ)](https://python-rq.org/)
- [Flask-Assets](https://flask-assets.readthedocs.io/en/latest/)
- [Flask-Compress](https://github.com/colour-science/flask-compress)
- [Flask-Login](https://flask-login.readthedocs.io/en/latest/)
- [Flask-Mail](https://pythonhosted.org/Flask-Mail/)
- [Flask-RQ2](https://flask-rq2.readthedocs.io/en/latest/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [Flask-WTF](https://flask-wtf.readthedocs.io/en/stable/)

---
