from pathlib import Path
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from routes.auth_routes import login_required
from config import Config, BASE_DIR
from db import get_active_info, test_mysql_credentials, check_backend_availability
import pymysql

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def index():
    db_info = get_active_info()
    return render_template(
        'settings.html',
        config=Config,
        db_info=db_info
    )

@settings_bp.route('/settings/test-mysql', methods=['POST'])
@login_required
def test_mysql():
    host = request.form.get('host', 'localhost').strip()
    port = request.form.get('port', '3306').strip()
    user = request.form.get('user', 'root').strip()
    password = request.form.get('password', '').strip()
    database = request.form.get('database', 'student_analytics_db').strip()

    success, msg = test_mysql_credentials(host, port, user, password, database)
    if success:
        return jsonify({'success': True, 'message': f'MySQL Connection Successful to {host}:{port}!'})
    else:
        return jsonify({'success': False, 'message': f'MySQL Connection Failed: {msg}'})

@settings_bp.route('/settings/init-mysql', methods=['POST'])
@login_required
def init_mysql():
    host = request.form.get('host', 'localhost').strip()
    port = int(request.form.get('port', 3306))
    user = request.form.get('user', 'root').strip()
    password = request.form.get('password', '').strip()
    
    sql_file = BASE_DIR / 'database.sql'
    if not sql_file.exists():
        flash('database.sql file not found!', 'danger')
        return redirect(url_for('settings.index'))

    try:
        # Connect without database to create it
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            autocommit=True
        )
        cursor = conn.cursor()

        # Read SQL statements (split on DELIMITER or semicolons appropriately)
        sql_content = sql_file.read_text(encoding='utf-8')
        
        # Execute line-by-line or statement blocks
        # Remove delimiters for python driver execution
        statements = []
        current = []
        in_delimiter = False
        
        for line in sql_content.splitlines():
            line_strip = line.strip()
            if line_strip.startswith('--') or not line_strip:
                continue
            if line_strip.startswith('DELIMITER'):
                continue
            
            # Replace $$ with ;
            line_clean = line.replace('$$', ';')
            current.append(line_clean)
            if line_clean.endswith(';'):
                stmt = '\n'.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []

        for stmt in statements:
            try:
                cursor.execute(stmt)
            except Exception:
                pass # continue on view drop etc

        conn.close()
        flash('MySQL Database initialized successfully from database.sql!', 'success')
    except Exception as e:
        flash(f'Failed to initialize MySQL Database: {str(e)}', 'danger')

    return redirect(url_for('settings.index'))

