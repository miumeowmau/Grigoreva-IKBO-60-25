"""Графический интерфейс эмулятора командной оболочки."""

import shlex
import sys
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from typing import NamedTuple

from config import XmlJournal, parse_startup_args

MAX_CD_ARGUMENTS = 1


class CommandResult(NamedTuple):
    """Ответ команды, признак выхода и сообщение об ошибке."""

    text: str
    should_exit: bool = False
    error: str | None = None


def failure(message):
    """Подготовить сообщение для окна и журнала."""
    return CommandResult(message, error=message)


def parse_command(text):
    """Разделить введённую команду с учётом кавычек."""
    return shlex.split(text, posix=True)

def execute_command(parts):
    """Вернуть ответ команды и признак завершения приложения."""
    if not parts:
        return failure("Команда не введена.")

    name = parts[0]
    arguments = parts[1:]

    if name == "exit":
        if arguments:
            return failure("Ошибка: exit не принимает аргументы.")
        return CommandResult("Завершение работы.", should_exit=True)

    if name not in ("ls", "cd"):
        return failure(f"Ошибка: неизвестная команда «{name}».")

    if name == "cd" and len(arguments) > MAX_CD_ARGUMENTS:
        return failure("Ошибка: cd принимает не более одного пути.")

    response = (
        f"Команда-заглушка: {name}\n"
        f"Аргументы: {arguments}"
    )
    return CommandResult(response)


def process_line(command, journal, source):
    """Выполнить одну строку и записать результат в журнал."""
    try:
        result = execute_command(parse_command(command))
    except ValueError as error:
        result = failure(f"Ошибка разбора: {error}")
    try:
        journal.record(command, source, result.error)
    except OSError as error:
        message = f"Ошибка записи журнала: {error}"
        return CommandResult(
            f"{result.text}\n{message}", result.should_exit, message
        )
    return result


def append_output(output, text):
    """Показать текст в области вывода."""
    output.configure(state="normal")
    output.insert(tk.END, f"{text}\n")
    output.configure(state="disabled")
    output.see(tk.END)


def handle_input(window, entry, output, journal):
    """Обработать интерактивный ввод."""
    command = entry.get()
    if not command.strip():
        return
    entry.delete(0, tk.END)
    result = process_line(command, journal, "interactive")
    append_output(output, f"> {command}\n{result.text}")

    if result.should_exit:
        window.destroy()
        return

    entry.focus_set()


def run_startup_script(window, output, path, journal):
    """Показать диалог скрипта и остановиться при первой ошибке."""
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as error:
        append_output(output, f"Ошибка чтения скрипта {path}: {error}")
        return
    for number, command in enumerate(lines, start=1):
        if not command.strip():
            continue
        result = process_line(command, journal, "script")
        append_output(output, f"> {command}\n{result.text}")
        if result.error is not None:
            append_output(output, f"Скрипт остановлен на строке {number}.")
            break
        if result.should_exit:
            window.destroy()
            return


def create_interface(window, journal):
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
        handle_input(window, entry, output, journal)

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
    return output


def main():
    """Прочитать настройки и запустить эмулятор."""
    args = parse_startup_args()
    print(f"Путь к VFS: {args.vfs}")
    print(f"Путь к журналу: {args.log}")
    print(f"Стартовый скрипт: {args.script}")
    try:
        journal = XmlJournal(args.log)
    except (OSError, ValueError) as error:
        print(f"Ошибка открытия журнала: {error}", file=sys.stderr)
        return 1

    window = tk.Tk()
    window.title(f"Эмулятор оболочки - VFS: {args.vfs.stem}")
    window.geometry("800x500")
    window.minsize(400, 200)
    output = create_interface(window, journal)
    if args.script is not None:
        window.after_idle(run_startup_script, window, output, args.script,
                          journal)
    window.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
