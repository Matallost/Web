import socket
import threading

clients = []

def handle_client(conn):
    while True:
        try:
            data = conn.recv(65535)
            if not data:
                break
            print(f"Получено: {data.decode('utf-8')}")
            for client in clients:
                if client != conn:
                    client.sendall(data)
        except:
            break
    clients.remove(conn)
    conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 9090))
    server.listen(2)
    print("Сервер запущен на порту 9090...")

    while True:
        conn, addr = server.accept()
        print(f"Подключен: {addr}")
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    start_server()