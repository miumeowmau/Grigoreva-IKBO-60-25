"""Графический интерфейс эмулятора командной оболочки."""

import shlex
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

MAX_CD_ARGUMENTS = 1

def parse_command(text):
    """Разделить введённую команду с учётом кавычек."""
    return shlex.split(text, posix=True)

def execute_command(parts):
    """Вернуть ответ команды и признак завершения приложения."""
    if not parts:
        return "Команда не введена.", False

    name = parts[0]
    arguments = parts[1:]

    if name == "exit":
        if arguments:
            return "Ошибка: exit не принимает аргументы.", False
        return "Завершение работы.", True

    if name not in ("ls", "cd"):
        return f"Ошибка: неизвестная команда «{name}».", False

    if name == "cd" and len(arguments) > MAX_CD_ARGUMENTS:
        return "Ошибка: cd принимает не более одного пути.", False

    response = (
        f"Команда-заглушка: {name}\n"
        f"Аргументы: {arguments!r}"
    )
    return response, False

def handle_input(window, entry, output):
    """Обработать ввод и при необходимости закрыть приложение."""
    command = entry.get()
    if not command.strip():
        return

    should_exit = False

    try:
        parts = parse_command(command)
        response, should_exit = execute_command(parts)
    except ValueError as error:
        response = f"Ошибка разбора: {error}"

    output.configure(state="normal")
    output.insert(tk.END, f"> {command}\n{response}\n")
    output.configure(state="disabled")
    output.see(tk.END)
    entry.delete(0, tk.END)

    if should_exit:
        window.destroy()
        return

    entry.focus_set()

def create_interface(window):
    """Добавить область вывода и элементы ввода."""
    output = ScrolledText(
        window,
        state="disabled",
        font=("Consolas", 12),
    )

    input_panel = tk.Frame(window)
    input_panel.pack(side="bottom", fill="x", padx=10, pady=(0, 10))

    output.pack(fill="both", expand=True, padx=10, pady=10)

    entry = tk.Entry(input_panel, font=("Consolas", 12))
    entry.pack(side="left", fill="x", expand=True)

    def submit_command(event=None):
        """Передать ввод основному обработчику."""
        handle_input(window, entry, output)

    button = tk.Button(
        input_panel,
        text="Отправить",
        command=submit_command,
        width=10,
        height=2,
    )
    button.pack(side="right", padx=(10, 0))

    entry.bind("<Return>", submit_command)
    entry.focus_set()

def main():
    """Создать окно и запустить обработку событий."""
    window = tk.Tk()
    window.title("Эмулятор оболочки - VFS: prac_vfs")
    window.geometry("800x500")
    window.minsize(600, 400)
    create_interface(window)
    window.mainloop()


if __name__ == "__main__":
    main()