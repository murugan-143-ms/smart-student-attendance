import os
from flask import Flask, render_template, session
from config import Config
from db import check_backend_availability, get_active_info

from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.student_routes import student_bp
from routes.faculty_routes import faculty_bp
from routes.attendance_routes import attendance_bp
from routes.performance_routes import performance_bp
from routes.analytics_routes import analytics_bp
from routes.reports_routes import reports_bp
from routes.dbms_showcase_routes import dbms_bp
from routes.settings_routes import settings_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure backend initialized
    check_backend_availability()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(dbms_bp)
    app.register_blueprint(settings_bp)

    @app.context_processor
    def inject_global_context():
        return {
            'app_title': 'Smart Student Attendance & Performance Analytics',
            'college_name': 'Department of Computer Science & Engineering',
            'current_user': session.get('full_name'),
            'current_role': session.get('role'),
            'db_status': get_active_info()
        }

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html', error=str(e)), 500

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*70)
    print(" Smart Student Attendance and Performance Analytics System")
    print(f" Web Server Running at: http://127.0.0.1:{port}")
    print(" Default Admin Credentials: Username: admin | Password: admin123")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=port, debug=True)

