import socket
import threading
import json
import pygame

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Переменные игрока
player_id = None
player_x, player_y = 400, 300
space_pressed = False
def connect_to_server():
    global player_id
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(("localhost", 8777))
    except ConnectionRefusedError:
        print("Не удалось подключиться к серверу. Убедитесь, что сервер запущен.")
        return

    # Последнее известное направление движения
    last_dx, last_dy = 0, -1  # По умолчанию дуло смотрит вверх

    buffer = ""  # Буфер для неполных сообщений
    try:
        while True:
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    client_socket.close()
                    return

            keys = pygame.key.get_pressed()
            dx, dy = 0, 0

            # Определяем направление движения
            if keys[pygame.K_w]:  # Движение вверх
                dy = -1
            elif keys[pygame.K_s]:  # Движение вниз
                dy = 1
            elif keys[pygame.K_a]:  # Движение влево
                dx = -1
            elif keys[pygame.K_d]:  # Движение вправо
                dx = 1

            # Нормализуем направление движения
            length = (dx ** 2 + dy ** 2) ** 0.5
            if length > 0:
                dx /= length
                dy /= length

            # Обновляем последнее известное направление
            if dx != 0 or dy != 0:
                last_dx, last_dy = dx, dy

            # Отправляем данные на сервер
            action = {
                "action": "move",
                "dx": dx * 5,  # Умножаем на скорость
                "dy": dy * 5
            }
            try:
                client_socket.send((json.dumps(action) + "\n").encode('utf-8'))  # Добавляем разделитель
            except ConnectionResetError:
                print("Сервер разорвал соединение.")
                break

            # Стрельба по нажатию пробела
            if keys[pygame.K_SPACE] and not space_pressed:
                space_pressed = True
                shoot_action = {"action": "shoot"}
                try:
                    client_socket.send((json.dumps(shoot_action) + "\n").encode('utf-8'))
                except ConnectionResetError:
                    print("Сервер разорвал соединение.")
                    break
            elif not keys[pygame.K_SPACE]:
                space_pressed = False

            # Получаем обновления от сервера
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:  # Проверяем, что данные не пустые
                    print("Received empty data from server")
                    break

                # Добавляем полученные данные в буфер
                buffer += data

                # Разделяем сообщения по символу новой строки
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    try:
                        state = json.loads(message)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        continue

                    screen.fill((0, 0, 0))
                    # Проверяем, жив ли игрок

                    # Отрисовка игроков
                    for pid, player in state["players"].items():
                        # Проверяем, жив ли игрок
                        if not player.get("alive", True):
                            continue  # Пропускаем отрисовку
                        # Тело танка
                        pygame.draw.rect(screen, player["color"], (player["x"], player["y"], 40, 40))

                        # Дуло танка
                        barrel_length = 20  # Длина дула

                        # Направление дула
                        barrel_dx = player["dx"]
                        barrel_dy = player["dy"]

                        # Если танк не движется, используем последнее направление этого игрока
                        if barrel_dx == 0 and barrel_dy == 0:
                            # Берём последнее направление из last_dx/last_dy только для текущего игрока
                            if pid == player_id:
                                barrel_dx, barrel_dy = last_dx, last_dy
                            else:
                                # Или просто оставляем предыдущее значение из данных сервера
                                barrel_dx = player.get("last_dx", 0)
                                barrel_dy = player.get("last_dy", -1)

                        # Нормализуем вектор направления дула
                        barrel_length_vector = (barrel_dx ** 2 + barrel_dy ** 2) ** 0.5
                        if barrel_length_vector > 0:
                            barrel_dx /= barrel_length_vector
                            barrel_dy /= barrel_length_vector

                        pygame.draw.line(
                            screen,
                            (255, 255, 255),  # Цвет дула
                            (player["x"] + 20, player["y"] + 20),  # Центр танка
                            (
                                player["x"] + 20 + barrel_dx * barrel_length,
                                player["y"] + 20 + barrel_dy * barrel_length
                            ),
                            5  # Толщина дула
                        )

                    # Отрисовка снарядов
                    for bullet in state["bullets"]:
                        pygame.draw.circle(screen, (255, 255, 0), (int(bullet["x"]), int(bullet["y"])), 5)

                    pygame.display.flip()
                    clock.tick(60)
            except ConnectionResetError:
                print("Сервер разорвал соединение.")
                break
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    connect_to_server()