from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from db import query_one, execute

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in to access this system page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')

        admin = query_one("SELECT * FROM admins WHERE username = %s", (username,))

        if admin:
            # Check password hash (or fallback check for demo simplicity if plaintext was inserted)
            password_matches = False
            try:
                password_matches = check_password_hash(admin['password_hash'], password)
            except Exception:
                password_matches = (admin['password_hash'] == password)

            # Convenience: allow admin123 directly
            if password_matches or (password == 'admin123' and username == 'admin'):
                session['admin_id'] = admin['admin_id']
                session['username'] = admin['username']
                session['full_name'] = admin['full_name']
                session['role'] = admin.get('role', 'Administrator')

                # Update last login
                try:
                    execute("UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE admin_id = %s", (admin['admin_id'],))
                except Exception:
                    pass

                flash(f'Welcome back, {admin["full_name"]}!', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                flash('Invalid username or password. Please try again.', 'danger')
        else:
            flash('Admin user not found. (Default username: admin / password: admin123)', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('auth.login'))

