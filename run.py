# -*- coding: utf-8 -*-
from app import create_app, db

app = create_app()

# Force create all tables including new columns
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)