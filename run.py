from Foodimg2Ing import app
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting server on http://127.0.0.1:{port}")
    app.run(debug=True, host='127.0.0.1', port=port)