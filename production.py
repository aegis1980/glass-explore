from glass_explore.app import app

# Reference the underlying Flask app for WSGI servers such as Gunicorn.
server = app.server 

# Run flask app
if __name__ == "__main__": 
    app.run(debug=False, host='0.0.0.0', port=8050)
