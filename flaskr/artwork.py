from flask import Flask, request, g, flash, redirect, url_for, render_template, Blueprint
from mysql.connector import Error
from .utils import login_required
import os

artwork = Blueprint('artwork', __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'flaskr/static/uploads')


@artwork.route('/create_artwork/<int:portfolio_id>', methods=['GET', 'POST'])
@login_required
def create_artwork(portfolio_id):

    cursor = g.db.cursor(dictionary=True)

    # Ensure the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    try:
        if request.method == 'POST':
            title = request.form.get('artwork_title')
            description = request.form.get('artwork_description')
            genre = request.form.get('artwork_genre')
            file = request.files.get('artwork_file')

            if file:
                filename = file.filename
                filetype = file.content_type

                # Save the file
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)

                insert_query = """
                INSERT INTO artworks (title, description, genre, filetype, file, portfolio_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (title, description,
                               genre, filetype, filename, portfolio_id))

                g.db.commit()
                flash('Artwork added successfully!', 'success')
                return redirect(url_for('portfolio.edit_portfolio', portfolio_id=portfolio_id))
            else:
                flash('No file selected.', 'error')
                return redirect(url_for('artwork.create_artwork', portfolio_id=portfolio_id))

        if request.method == 'GET':
            return render_template('create_artwork.html', portfolio_id=portfolio_id)

    except Error as e:
        print(f"Database error: {e}")
        flash('An error occurred while accessing the database.', 'error')
        return redirect(url_for('portfolio.edit_portfolio', portfolio_id=portfolio_id))

    finally:
        # Ensure the cursor is closed after all operations
        try:
            cursor.close()
        except Error as e:
            print(f"Error closing cursor: {e}")

    if request.method == 'GET':
        return render_template('create_artwork.html', portfolio_id=portfolio_id)


@artwork.route('/delete_artwork/<int:artwork_id>', methods=['POST'])
@login_required
def delete_artwork(artwork_id):

    cursor = g.db.cursor(dictionary=True)

    try:
        # Fetch the artwork details
        select_query = "SELECT * FROM artworks WHERE artwork_id = %s"
        cursor.execute(select_query, (artwork_id,))
        artwork = cursor.fetchone()

        if not artwork:
            flash('Artwork not found.', 'error')
            return redirect(url_for('main.dashboard'))

        # Delete the file from the server
        file_path = os.path.join(
            'flaskr/static/uploads', artwork.get('file', ''))
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete the artwork from the database
        delete_query = "DELETE FROM artworks WHERE artwork_id = %s"
        cursor.execute(delete_query, (artwork_id,))
        g.db.commit()

        # Check if the artwork deletion was successful
        cursor.execute(select_query, (artwork_id,))
        deleted_artwork = cursor.fetchone()
        if deleted_artwork:
            flash('Failed to delete the artwork.', 'error')
            return redirect(url_for('main.dashboard'))

        # Redirect to the associated portfolio edit page or dashboard
        portfolio_id = artwork.get('portfolio_id')
        if portfolio_id:
            return redirect(url_for('portfolio.edit_portfolio', portfolio_id=portfolio_id))
        else:
            flash('Portfolio ID not found for the artwork.', 'error')
            return redirect(url_for('main.dashboard'))
    except Error as e:
        print(f"The error '{e}' occurred")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))
    finally:
        cursor.close()


@artwork.route('/edit_artwork/<int:artwork_id>', methods=['GET', 'POST'])
@login_required
def edit_artwork(artwork_id):

    cursor = g.db.cursor(dictionary=True)

    if request.method == 'POST':
        # Extract data from the form
        title = request.form.get('artwork_title')
        description = request.form.get('artwork_description')
        genre = request.form.get('artwork_genre')

        try:
            # Update artwork in the database
            update_query = """
            UPDATE artworks
            SET title = %s, description = %s, genre = %s
            WHERE artwork_id = %s
            """
            cursor.execute(
                update_query, (title, description, genre, artwork_id))
            g.db.commit()
            flash('Artwork updated successfully!', 'success')
            # Redirect to dashboard or other page
            return redirect(url_for('portfolio.edit_portfolio', portfolio_id=portfolio_id))
        except Error as e:
            print(f"The error '{e}' occurred")
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('artwork.edit_artwork', artwork_id=artwork_id))
        finally:
            cursor.close()

    if request.method == 'GET':
        cursor = g.db.cursor(dictionary=True)

        try:
            # Fetch the artwork details
            select_query = "SELECT * FROM artworks WHERE artwork_id = %s"
            cursor.execute(select_query, (artwork_id,))
            artwork = cursor.fetchone()

            if not artwork:
                flash('Artwork not found.', 'error')
                return redirect(url_for('portfolio.edit_portfolio', portfolio_id=portfolio_id))

            return render_template('edit_artwork.html', artwork=artwork)
        except Error as e:
            print(f"The error '{e}' occurred")
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('portfolio.edit_portfolio', portfolio_id=portfolio_id))
        finally:
            cursor.close()
