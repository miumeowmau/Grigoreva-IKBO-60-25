"""Графический интерфейс эмулятора командной оболочки."""

import tkinter as tk
from tkinter.scrolledtext import ScrolledText


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
        """Показать введённую строку в области вывода."""
        command = entry.get()
        if not command.strip():
            return

        output.configure(state="normal")
        output.insert(tk.END, f"> {command}\n")
        output.configure(state="disabled")
        output.see(tk.END)
        entry.delete(0, tk.END)
        entry.focus_set()

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