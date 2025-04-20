from flask import Blueprint, render_template, session, redirect, url_for, flash

dashboard_bp = Blueprint('dashboard_bp', __name__, template_folder='templates')

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("please log in to continue.",)
        return redirect(url_for('login'))
    return render_template('dashboard.html', username = session.get('username'))

