from flask import Flask, render_template, request, send_file, abort, Blueprint, g   
from xhtml2pdf import pisa
import io

pdf = Blueprint('pdf', __name__)


@pdf.route('/download/<int:portfolio_id>', methods=['GET'])
def download(portfolio_id):
    # Fetch portfolio data from the database
    portfolio = get_portfolio_from_db(portfolio_id)  # Implement this function

    if not portfolio:
        abort(404, "Portfolio not found")

    # Render the HTML template with portfolio data
    html = render_template('portfolio_pdf.html', portfolio=portfolio)

    # Convert HTML to PDF
    pdf_content = convert_html_to_pdf(html)

    if not pdf_content:
        abort(500, "PDF generation failed")

    # Create a response object with the PDF file
    response = make_pdf_response(pdf_content, f"portfolio_{portfolio_id}.pdf")
    return response


def convert_html_to_pdf(html):
    pdf = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html.encode('utf-8')), dest=pdf)

    if pisa_status.err:
        return None

    pdf.seek(0)
    return pdf


def make_pdf_response(pdf, filename):
    return send_file(pdf, as_attachment=True, download_name=filename, mimetype='application/pdf')


def get_portfolio_from_db(portfolio_id):
    cursor = g.db.cursor(dictionary=True)
    try:
        # Fetch portfolio details
        cursor.execute("""
            SELECT p.portfolio_id, p.title, p.description, p.artmedium, u.name as user_name
            FROM portfolios p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.portfolio_id = %s
        """, (portfolio_id,))
        portfolio = cursor.fetchone()

        if not portfolio:
            return None

        # Fetch all artworks associated with the portfolio
        cursor.execute("""
            SELECT * FROM artworks
            WHERE portfolio_id = %s
        """, (portfolio_id,))
        artworks = cursor.fetchall()

        # Combine portfolio and artworks
        portfolio['artworks'] = artworks
        return portfolio
    except Error as e:
        print(f"The error '{e}' occurred")
        return None
    finally:
        cursor.close()
