import socket
import threading
from tkinter import *
from tkinter.scrolledtext import ScrolledText

# Подключение к серверу
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('127.0.0.1', 9090))

# Имя пользователя
CLIENT_NAME = input("Введите ваше имя: ")

root = Tk()
root.title(f"Чат - {CLIENT_NAME}")

chat_log = ScrolledText(root, state='disabled')
chat_log.pack(padx=5, pady=5)

message_input = Entry(root)
message_input.pack(padx=5, pady=5, fill=X)

def send_message(event=None):
    message = message_input.get()
    if message:
        full_message = f"{CLIENT_NAME}: {message}"
        client_socket.send(full_message.encode('utf-8'))
        message_input.delete(0, END)
        add_message(f"Вы: {message}")

def add_message(message):
    chat_log.config(state='normal')
    chat_log.insert(END, message + "\n")
    chat_log.config(state='disabled')
    chat_log.see(END)

message_input.bind("<Return>", send_message)

def receive_messages():
    while True:
        try:
            data = client_socket.recv(65535)
            if not data:
                break
            add_message(data.decode('utf-8'))
        except:
            break

threading.Thread(target=receive_messages, daemon=True).start()

root.mainloop()