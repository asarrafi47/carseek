from app import app, init_db

if __name__ == '__main__':
    init_db()  # Add this line to initialize the database
    app.run(host='0.0.0.0', port=5000, debug=True)
