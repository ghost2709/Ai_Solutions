from website import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)  # Set debug=True for development; use False in production