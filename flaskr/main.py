from flask import Blueprint, render_template, session, redirect, url_for, g
from .utils import login_required
main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
@login_required
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    try:
        cursor = g.db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM portfolios WHERE user_id = %s", (user_id,))
        portfolios = cursor.fetchall()
        
        if cursor.nextset() is not None:
            cursor.fetchall()

    except Exception as e:
        print(f"Error: {e}")
        portfolios = []
        
    finally:
        cursor.close()
    
    return render_template('dashboard.html', portfolios=portfolios)

@main.route('/delete/<int:portfolio_id>', methods=['POST'])
@login_required
def delete_portfolio(portfolio_id):
    print(f"Deleting portfolio with ID: {portfolio_id}")
