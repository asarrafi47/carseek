from app import app, init_db, init_cars_table

if __name__ == '__main__':
    init_db()
    init_cars_table()  # <-- ADD THIS
    app.run(host='0.0.0.0', port=5000, debug=True)
