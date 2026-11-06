"""Проверки параметров, XML и выполнения стартового скрипта."""

import sys
import tkinter as tk
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from tkinter.scrolledtext import ScrolledText
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import XmlJournal, parse_startup_args
from main import run_startup_script


class StageTwoTests(unittest.TestCase):
    """Проверить результаты работы на временных файлах."""

    def setUp(self):
        """Создать отдельный каталог для файлов каждого теста."""
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.log = self.directory / "logs" / "test.xml"

    def run_script(self, content):
        """Выполнить скрипт с настоящим виджетом вывода Tk."""
        script = self.directory / "script.txt"
        script.write_text(content, encoding="utf-8-sig")
        window = tk.Tk()
        window.withdraw()
        try:
            output = ScrolledText(window, state="disabled")
            run_startup_script(window, output, script, XmlJournal(self.log))
            return output.get("1.0", tk.END)
        finally:
            window.destroy()

    def test_path_options(self):
        """Сохранить пути с пробелами и настройки по умолчанию."""
        defaults = parse_startup_args([])
        self.assertEqual(defaults.vfs.stem, "prac_vfs")
        self.assertIsNone(defaults.script)
        args = parse_startup_args([
            "--vfs", "study vfs.csv", "--log", "log dir/run.xml",
            "--script", "script dir/start.txt",
        ])
        self.assertEqual(args.vfs, Path("study vfs.csv"))
        self.assertEqual(args.log, Path("log dir/run.xml"))
        self.assertEqual(args.script, Path("script dir/start.txt"))

    def test_script_stops_on_command_error(self):
        """Не выполнять строки после первой ошибки команды."""
        output = self.run_script('ls "a & b"\ncd one two\nls never\n')
        self.assertIn('> ls "a & b"', output)
        self.assertIn("Аргументы: ['a & b']", output)
        self.assertIn("Скрипт остановлен на строке 2.", output)
        self.assertNotIn("ls never", output)
        events = ET.parse(self.log).findall("event")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].findtext("command"), 'ls "a & b"')
        self.assertEqual(events[1].get("source"), "script")
        self.assertIn("не более одного пути", events[1].findtext("error"))

    def test_script_stops_on_parse_error(self):
        """Зарегистрировать ошибку разбора и остановить скрипт."""
        output = self.run_script('cd "docs\nls never\n')
        self.assertIn("Ошибка разбора:", output)
        self.assertNotIn("ls never", output)
        self.assertIsNotNone(ET.parse(self.log).find("event/error"))

    def test_journal_keeps_previous_events(self):
        """Дополнить прежний XML, сохранив специальные символы."""
        XmlJournal(self.log).record('ls "a & <b>"', "interactive")
        XmlJournal(self.log).record("ls next", "script")
        events = ET.parse(self.log).findall("event")
        self.assertEqual(events[0].findtext("command"), 'ls "a & <b>"')
        self.assertEqual(events[1].findtext("command"), "ls next")
