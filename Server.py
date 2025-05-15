import socket
import threading
import json
import random
import pygame

# Хранилище данных о всех игроках и снарядах
players = {}
bullets = []

# Генерация случайного цвета
def generate_random_color():
    return [random.randint(0, 255) for _ in range(3)]

def handle_client(client_socket, player_id):
    players[player_id] = {
        "x": random.randint(100, 700),
        "y": random.randint(100, 500),
        "dx": 0,
        "dy": -1,
        "last_dx": 0,
        "last_dy": -1,
        "color": generate_random_color(),
        "alive": True
    }


    buffer = ""  # Буфер для неполных сообщений
    try:
        while True:
            # Получаем данные от клиента
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:  # Проверяем, что данные не пустые
                    print("Received empty data from client")
                    break

                # Добавляем полученные данные в буфер
                buffer += data

                # Разделяем сообщения по символу новой строки
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        continue

                    if "action" in data:
                        if data["action"] == "move":
                            players[player_id]["x"] += data.get("dx", 0)
                            players[player_id]["y"] += data.get("dy", 0)

                            # Обновляем текущее и последнее направление
                            players[player_id]["dx"] = data.get("dx", 0)
                            players[player_id]["dy"] = data.get("dy", 0)
                            if data.get("dx", 0) != 0 or data.get("dy", 0) != 0:
                                players[player_id]["last_dx"] = data.get("dx", 0)
                                players[player_id]["last_dy"] = data.get("dy", 0)
                        elif data["action"] == "shoot":
                            # Используем последнее известное направление
                            dx = players[player_id]["last_dx"]
                            dy = players[player_id]["last_dy"]

                            # Нормализуем вектор направления
                            length = (dx ** 2 + dy ** 2) ** 0.5
                            if length > 0:
                                dx /= length
                                dy /= length

                            bullets.append({
                                "x": players[player_id]["x"] + 20,
                                "y": players[player_id]["y"] + 20,
                                "dx": dx * 10,  # Умножаем на скорость
                                "dy": dy * 10,
                                "owner": player_id
                            })

                    # Отправляем текущее состояние игры клиенту
                    try:
                        client_socket.send((json.dumps({
                            "players": players,
                            "bullets": bullets,
                            "my_id": player_id
                        }) + "\n").encode('utf-8'))  # Добавляем разделитель
                    except ConnectionResetError:
                        print("Клиент разорвал соединение.")
                        break
            except ConnectionResetError:
                print("Клиент разорвал соединение.")
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        del players[player_id]
        client_socket.close()

def update_bullet():
    global bullets
    while True:
        # Создаём копии, чтобы не модифицировать коллекции во время итерации
        bullets_copy = bullets[:]
        players_copy = dict(players)  # Копируем текущих игроков

        for bullet in bullets_copy:
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]

            # Проверяем выход за границы экрана
            if not (0 <= bullet["x"] <= 800) or not (0 <= bullet["y"] <= 600):
                print(f"Bullet out of bounds: x={bullet['x']}, y={bullet['y']}")
                if bullet in bullets:
                    bullets.remove(bullet)
                continue  # Пропускаем дальнейшую обработку

            # Проверяем столкновение со всеми игроками
            hit = False
            for player_id, player in list(players_copy.items()):
                distance = ((bullet["x"] - player["x"]) ** 2 + (bullet["y"] - player["y"]) ** 2) ** 0.5
                if distance < 20 and not hit:
                    print(f"Bullet hit player: player_id={player_id}, bullet_owner={bullet['owner']}")

                    if player_id != bullet["owner"]:
                        print(f"Player {player_id} was hit by bullet from {bullet['owner']}")
                        players[player_id]["alive"] = False  # Помечаем как мертвого
                    try:
                        bullets.remove(bullet)
                    except ValueError:
                        pass
                    break


        pygame.time.wait(16)  # ~60 FPS

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 8777))
    server.listen(5)
    print("Сервер запущен на localhost:8777")

    # Запускаем задачу для обновления снарядов
    threading.Thread(target=update_bullet, daemon=True).start()

    while True:
        client_socket, addr = server.accept()
        print(f"Подключился клиент: {addr}")
        player_id = id(client_socket)
        threading.Thread(target=handle_client, args=(client_socket, player_id), daemon=True).start()

if __name__ == "__main__":
    main()