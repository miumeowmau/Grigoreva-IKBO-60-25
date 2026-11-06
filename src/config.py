"""Параметры запуска и журнал команд эмулятора."""

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET


def parse_startup_args(argv=None):
    """Получить пути из параметров запуска."""
    parser = argparse.ArgumentParser(
        description="Графический эмулятор командной оболочки.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--vfs", type=Path, default=Path("prac_vfs.csv"),
        help="путь к файлу VFS",
    )
    parser.add_argument(
        "--log", type=Path, default=Path("session.xml"),
        help="путь к XML-журналу",
    )
    parser.add_argument(
        "--script", type=Path, help="путь к стартовому скрипту",
    )
    args = parser.parse_args(argv)
    inputs = (args.vfs, args.script)
    if any(path and path.resolve() == args.log.resolve() for path in inputs):
        parser.error("Путь к журналу должен отличаться от входных файлов.")
    return args


class XmlJournal:
    """Хранить события команд в XML-файле."""

    def __init__(self, path):
        """Открыть существующий журнал или создать новый."""
        self.path = path
        if path.exists():
            try:
                self.tree = ET.parse(path)
            except ET.ParseError as error:
                raise ValueError("Существующий журнал повреждён.") from error
            if self.tree.getroot().tag != "command_log":
                raise ValueError("Файл не является журналом эмулятора.")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.tree = ET.ElementTree(ET.Element("command_log"))
            self.save()

    def save(self):
        """Записать XML с отступами и кодировкой UTF-8."""
        ET.indent(self.tree)
        self.tree.write(self.path, encoding="utf-8", xml_declaration=True)

    def record(self, command, source, error=None):
        """Записать исходную строку, источник и сообщение об ошибке."""
        event = ET.SubElement(self.tree.getroot(), "event", source=source)
        ET.SubElement(event, "command").text = command
        if error is not None:
            ET.SubElement(event, "error").text = error
        self.save()
