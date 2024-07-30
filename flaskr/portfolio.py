from flask import Blueprint, render_template, request, redirect, url_for, g, flash, session
from .utils import login_required
from mysql.connector import Error

portfolio = Blueprint('portfolio', __name__)


@portfolio.route('/create_portfolio', methods=['GET', 'POST'])
@login_required
def create_portfolio():
    if request.method == 'POST':
        # Handle form submission
        title = request.form.get('title')
        description = request.form.get('description')
        artmedium = request.form.get('artmedium')
        user_id = session.get('user_id')

        # Ensure the form data is valid
        if not title or not description or not artmedium or not user_id:
            # Redirect to the form with an error message if data is missing
            return redirect(url_for('portfolio.create_portfolio', error="All fields are required"))

        try:
            cursor = g.db.cursor()
            cursor.execute(
                "INSERT INTO portfolios (title, description, artmedium, user_id) VALUES (%s, %s, %s, %s)",
                (title, description, artmedium, user_id)
            )
            g.db.commit()
            cursor.close()

            # Redirect to the portfolio list or any other appropriate page
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            print(f"Error: {e}")
            # Handle errors, such as database errors
            return redirect(url_for('portfolio.create_portfolio', error="An error occurred while creating the portfolio"))

    if request.method == 'GET':
        return render_template('create_portfolio.html')


@portfolio.route('/edit_portfolio/<int:portfolio_id>', methods=['GET', 'POST'])
@login_required
def edit_portfolio(portfolio_id):
    cursor = g.db.cursor(dictionary=True)

    if request.method == 'POST':
        # Extract data from the form
        title = request.form.get('title')
        description = request.form.get('description')
        artmedium = request.form.get('artmedium')

        try:
            # Update portfolio in the database
            update_query = """
            UPDATE portfolios
            SET title = %s, description = %s, artmedium = %s
            WHERE portfolio_id = %s
            """
            cursor.execute(
                update_query, (title, description, artmedium, portfolio_id))
            g.db.commit()
            flash('Portfolio updated successfully!', 'success')
            # Redirect to dashboard or other page
            return redirect(url_for('main.dashboard'))
        except Error as e:
            print(f"The error '{e}' occurred")
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('portfolio.edit', portfolio_id=portfolio_id))
        finally:
            cursor.close()

    if request.method == 'GET':
        try:
            # Fetch current details of the portfolio
            select_query = "SELECT * FROM portfolios WHERE portfolio_id = %s"
            cursor.execute(select_query, (portfolio_id,))
            portfolio = cursor.fetchone()

            if not portfolio:
                flash('Portfolio not found.', 'error')
                # Redirect if portfolio not found
                return redirect(url_for('main.dashboard'))

            # Fetch all artworks associated with the portfolio
            artworks_query = "SELECT * FROM artworks WHERE portfolio_id = %s"
            cursor.execute(artworks_query, (portfolio_id,))
            artworks = cursor.fetchall()

            return render_template('edit_portfolio.html', portfolio=portfolio, artworks=artworks)
        except Error as e:
            print(f"The error '{e}' occurred")
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('main.dashboard'))
        finally:
            cursor.close()


@portfolio.route('/delete_portfolio/<int:portfolio_id>', methods=['POST'])
@login_required
def delete_portfolio(portfolio_id):
    try:
        cursor = g.db.cursor()

        # Delete all artworks associated with the portfolio
        delete_artworks_query = "DELETE FROM artworks WHERE portfolio_id = %s"
        cursor.execute(delete_artworks_query, (portfolio_id,))

        # Delete the portfolio itself
        delete_portfolio_query = "DELETE FROM portfolios WHERE portfolio_id = %s"
        cursor.execute(delete_portfolio_query, (portfolio_id,))

        g.db.commit()
        flash('Portfolio and associated artworks deleted successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    except Error as e:
        print(f"The error '{e}' occurred")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('portfolio.edit_portfolio', portfolio_id=portfolio_id))

    finally:
        cursor.close()


@portfolio.route('/view_portfolio/<int:portfolio_id>')
def view_portfolio(portfolio_id):
    portfolio = get_portfolio_details(portfolio_id)

    if portfolio:
        return render_template('view_portfolio.html', portfolio=portfolio)
    else:
        # Handle the case where no portfolio is found, e.g., show a 404 page
        return "Portfolio not found", 404


def get_portfolio_details(portfolio_id):
    cursor = g.db.cursor()
    cursor.execute("""
        SELECT portfolios.portfolio_id, portfolios.title, portfolios.description, portfolios.artmedium, users.name as user_name
        FROM portfolios
        JOIN users ON portfolios.user_id = users.user_id
        WHERE portfolios.portfolio_id = %s
    """, (portfolio_id,))
    result = cursor.fetchone()
    if result:
        portfolio_details = dict(
            zip([column[0] for column in cursor.description], result))
    else:
        portfolio_details = None
    cursor.close()
    return portfolio_details


@portfolio.route('/search_portfolios', methods=['GET', 'POST'])
def search_portfolios():
    search_results = []
    query = ''
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            search_results = get_search_results(query)
        else:
            flash('Search query cannot be empty.', 'warning')

    return render_template('search_portfolios.html', portfolios=search_results, query=query)


def get_search_results(query):
    cursor = g.db.cursor(dictionary=True)

    search_terms = query.split()

    sql = """
    SELECT DISTINCT p.*, u.name as user_name, (SELECT GROUP_CONCAT(a.title SEPARATOR ', ') 
            FROM artworks a 
            WHERE a.portfolio_id = p.portfolio_id) as artwork_titles
    FROM portfolios p
    JOIN users u ON p.user_id = u.user_id
    WHERE 1=0
    """

    params = []
    for term in search_terms:
        sql += """ OR p.title LIKE %s
                OR p.description LIKE %s
                OR p.artmedium LIKE %s
                OR u.name LIKE %s"""
        params.extend(['%' + term + '%'] * 4)

    cursor.execute(sql, params)
    results = cursor.fetchall()

    cursor.close()

    return rank_results(results, search_terms)


def rank_results(results, search_terms):
    ranked = []
    for row in results:
        score = calculate_score(row, search_terms)
        ranked.append((score, row))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in ranked]


def calculate_score(row, search_terms):
    score = 0
    for term in search_terms:
        term = term.lower()
        if term in row['title'].lower():
            score += 3
        if term in row['description'].lower():
            score += 2
        if term in row['artmedium'].lower():
            score += 2
        if term in row['user_name'].lower():
            score += 1
        if row['artwork_titles'] and term in row['artwork_titles'].lower():
            score += 1
    return score
