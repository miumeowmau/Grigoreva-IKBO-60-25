import json
from pathlib import Path
from urllib.parse import urlsplit


def check_repository(repository, test_mode, config_dir):
    """Проверяет URL репозитория или путь к тестовому файлу."""
    if test_mode:
        if not (config_dir / repository).is_file():
            raise ValueError("repository: тестовый файл не найден")
    else:
        url = urlsplit(repository)
        if url.scheme not in ("http", "https") or not url.hostname:
            raise ValueError("repository: укажи адрес HTTP или HTTPS")


def main():
    """Читает, проверяет и выводит настройки."""
    config_path = Path(__file__).parent.parent / "config.json"

    try:
        with config_path.open(encoding="utf-8") as file:
            config = json.load(file)

        if not isinstance(config, dict):
            raise ValueError("В config.json нужен объект в фигурных скобках")

        text_keys = ("package_name", "repository", "version", "output_file")
        for key in text_keys:
            value = config.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key}: укажи непустую строку")

        if not isinstance(config.get("test_mode"), bool):
            raise ValueError("test_mode: укажи true или false")

        if not isinstance(config.get("filter"), str):
            raise ValueError("filter: укажи строку")

        if not config["output_file"].endswith(".svg"):
            raise ValueError("output_file: имя должно заканчиваться на .svg")

        check_repository(
            config["repository"], config["test_mode"], config_path.parent
        )

        for key, value in config.items():
            print(f"{key} = {value}")

    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()