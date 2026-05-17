# run.py
# This is the entry point - run this file to start the web server

from app import create_app

# Create the Flask app using our factory function
app = create_app()

if __name__ == '__main__':
    # debug=True means:
    # 1. Auto-reloads when you save a file (no need to restart server)
    # 2. Shows detailed error messages in browser
    # ⚠️ Never use debug=True in production (real websites)!
    app.run(debug=True, port=5000)