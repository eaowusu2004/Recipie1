from Foodimg2Ing import app
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"\n==================================================")
    print(f"  Recipe App running at: http://127.0.0.1:{port}")
    print(f"==================================================\n")
    app.run(host='127.0.0.1', port=port, debug=False)