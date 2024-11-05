import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Set the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Use a non-interactive backend for Matplotlib
plt.switch_backend('Agg')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def perform_analysis(users_file, books_file, ratings_file):
    # Read the uploaded CSV files into pandas DataFrames
    users = pd.read_csv(users_file, delimiter=';', encoding='ISO-8859-1', on_bad_lines='skip')
    books = pd.read_csv(books_file, delimiter=';', encoding='ISO-8859-1', on_bad_lines='skip')
    ratings = pd.read_csv(ratings_file, delimiter=';', encoding='ISO-8859-1', on_bad_lines='skip')

    # Ensure the static directory exists
    static_folder = os.path.join(app.root_path, 'static')
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)

    # Age Distribution
    plt.figure(figsize=(12, 8))
    users['Age'].hist(bins=range(0, 101, 10), color='skyblue', edgecolor='black')
    plt.title('Age Distribution of Users', fontsize=18)
    plt.xlabel('Age', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.grid(axis='y', linestyle='--')
    plt.tight_layout()
    age_dist_path = os.path.join(static_folder, 'age_distribution.png')
    plt.savefig(age_dist_path)
    plt.close()

    # Rating Distribution
    plt.figure(figsize=(12, 8))
    sns.histplot(ratings['Book-Rating'], kde=True, bins=10, color='purple')
    plt.title('Rating Distribution', fontsize=18)
    plt.xlabel('Rating', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.grid(axis='y', linestyle='--')
    plt.tight_layout()
    rating_dist_path = os.path.join(static_folder, 'rating_distribution.png')
    plt.savefig(rating_dist_path)
    plt.close()

    # Top 10 Most Rated Books
    ratings_per_book = ratings.groupby('ISBN')['Book-Rating'].count().reset_index()
    ratings_per_book = pd.merge(ratings_per_book, books[['ISBN', 'Book-Title']], on='ISBN', how='left')
    ratings_per_book.columns = ['ISBN', 'Rating Count', 'Book-Title']
    top_10_ratings_per_book = ratings_per_book.sort_values('Rating Count', ascending=False).head(10)

    plt.figure(figsize=(14, 10))
    sns.barplot(x='Rating Count', y='Book-Title', data=top_10_ratings_per_book, palette='magma', orient='h')
    plt.title('Top 10 Most Rated Books', fontsize=18)
    plt.xlabel('Rating Count', fontsize=14)
    plt.ylabel('Book Title', fontsize=14)
    plt.grid(axis='x', linestyle='--')
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    top_rated_books_path = os.path.join(static_folder, 'top_rated_books.png')
    plt.savefig(top_rated_books_path)
    plt.close()

    # Top 10 Books by Average Rating
    min_ratings = 5  # Minimum number of ratings required to consider the book
    books_with_enough_ratings = ratings_per_book[ratings_per_book['Rating Count'] >= min_ratings]
    avg_rating_per_book = ratings.groupby('ISBN')['Book-Rating'].mean().reset_index()
    avg_rating_per_book = pd.merge(avg_rating_per_book, books_with_enough_ratings[['ISBN', 'Book-Title']], on='ISBN',
                                   how='inner')
    avg_rating_per_book.columns = ['ISBN', 'Average Rating', 'Book-Title']
    top_10_avg_ratings_per_book = avg_rating_per_book.sort_values('Average Rating', ascending=False).head(10)

    plt.figure(figsize=(14, 10))
    sns.barplot(x='Average Rating', y='Book-Title', data=top_10_avg_ratings_per_book, palette='coolwarm', orient='h')
    plt.title('Top 10 Books by Average Rating', fontsize=18)
    plt.xlabel('Average Rating', fontsize=14)
    plt.ylabel('Book Title', fontsize=14)
    plt.grid(axis='x', linestyle='--')
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    top_avg_rated_books_path = os.path.join(static_folder, 'top_avg_rated_books.png')
    plt.savefig(top_avg_rated_books_path)
    plt.close()

    return {
        'age_distribution': 'age_distribution.png',
        'rating_distribution': 'rating_distribution.png',
        'top_rated_books': 'top_rated_books.png',
        'top_avg_rated_books': 'top_avg_rated_books.png'
    }


@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'users_file' not in request.files or 'books_file' not in request.files or 'ratings_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        users_file = request.files['users_file']
        books_file = request.files['books_file']
        ratings_file = request.files['ratings_file']

        if users_file.filename == '' or books_file.filename == '' or ratings_file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if allowed_file(users_file.filename) and allowed_file(books_file.filename) and allowed_file(
                ratings_file.filename):
            users_filename = secure_filename(users_file.filename)
            books_filename = secure_filename(books_file.filename)
            ratings_filename = secure_filename(ratings_file.filename)

            users_filepath = os.path.join(app.config['UPLOAD_FOLDER'], users_filename)
            books_filepath = os.path.join(app.config['UPLOAD_FOLDER'], books_filename)
            ratings_filepath = os.path.join(app.config['UPLOAD_FOLDER'], ratings_filename)

            users_file.save(users_filepath)
            books_file.save(books_filepath)
            ratings_file.save(ratings_filepath)

            # Perform the analysis
            chart_paths = perform_analysis(users_filepath, books_filepath, ratings_filepath)

            return render_template('results.html', charts=chart_paths)
        else:
            flash('Allowed file types are csv')
            return redirect(request.url)
    return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True)
