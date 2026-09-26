from Foodimg2Ing import app
import os
import socket


def find_free_port(starting_port=5001):
    port = starting_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
        port += 1
    return starting_port


if __name__ == '__main__':
    default_port = int(os.environ.get('PORT', 5001))
    port = find_free_port(default_port)
    print(f"\n==================================================")
    print(f"  Recipe App running at: http://127.0.0.1:{port}")
    print(f"==================================================\n")
    app.run(debug=True, host='127.0.0.1', port=port)