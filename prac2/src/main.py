import json
import lzma
import subprocess
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen


def check_repository(repository, test_mode, config_dir):
    """Проверяет URL репозитория или путь к тестовому файлу."""
    if test_mode:
        if not (config_dir / repository).is_file():
            raise ValueError("repository: тестовый файл не найден")
    else:
        url = urlsplit(repository)
        if url.scheme not in ("http", "https") or not url.hostname:
            raise ValueError("repository: укажи адрес HTTP или HTTPS")


def load_repository(config, config_dir):
    """Читает тестовый граф или индекс Ubuntu."""
    if config["test_mode"]:
        path = config_dir / config["repository"]
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    with urlopen(config["repository"], timeout=15) as response:
        archive = response.read()
    index = lzma.decompress(archive).decode("utf-8")

    root = config["package_name"]
    version = config["version"]
    repository = {}

    for block in index.split("\n\n"):
        fields = {}
        for line in block.splitlines():
            key, separator, value = line.partition(": ")
            if separator:
                fields[key] = value

        package = fields.get("Package")
        if not package or package in repository:
            continue
        if package == root and fields.get("Version") != version:
            continue

        repository[package] = dependency_names(fields)

    if root not in repository:
        raise ValueError("Пакет указанной версии не найден в индексе")
    return repository


def dependency_names(fields):
    """Возвращает имена пакетов из Depends и Pre-Depends."""
    names = []
    for key in ("Pre-Depends", "Depends"):
        value = fields.get(key, "").replace("|", ",")
        for item in value.split(","):
            words = item.split()
            if not words:
                continue

            name = words[0].split(":")[0]
            if name not in names:
                names.append(name)
    return names


def bfs(repository, level, graph, excluded):
    """Обходит граф по уровням."""
    if not level:
        return

    next_level = []
    for package in level:
        for dependency in repository.get(package, []):
            if excluded and excluded in dependency:
                continue

            graph[package].append(dependency)
            if dependency not in graph:
                graph[dependency] = []
                next_level.append(dependency)

    bfs(repository, next_level, graph, excluded)


def build_graph(repository, root, excluded):
    """Строит граф зависимостей выбранного пакета."""
    if root not in repository:
        raise ValueError("Пакет не найден в репозитории")
    if excluded and excluded in root:
        return {}

    graph = {root: []}
    bfs(repository, [root], graph, excluded)
    return graph


def plantuml_text(graph):
    """Преобразует вершины и связи графа в текст PlantUML."""
    lines = ["@startuml", "!pragma layout smetana", "left to right direction"]
    aliases = {}

    for number, package in enumerate(graph):
        alias = f"p{number}"
        aliases[package] = alias
        lines.append(f'rectangle "{package}" as {alias}')

    for package, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(f"{aliases[package]} --> {aliases[dependency]}")

    lines.append("@enduml")
    return "\n".join(lines)


def save_graph(graph, config, config_dir):
    """Записывает файл PlantUML и создаёт из него SVG."""
    if not graph:
        raise ValueError("Фильтр исключил начальный пакет")

    svg_path = config_dir / config["output_file"]
    puml_path = svg_path.with_suffix(".puml")
    puml_path.write_text(plantuml_text(graph), encoding="utf-8")

    jar_path = config_dir / "plantuml.jar"
    command = ["java", "-jar", str(jar_path), "-tsvg", str(puml_path)]
    subprocess.run(command, check=True)
    print(f"Граф сохранён в {svg_path}")


def main():
    """Читает настройки, строит и сохраняет граф."""
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

        repository = load_repository(config, config_path.parent)
        graph = build_graph(
            repository, config["package_name"], config["filter"]
        )

        save_graph(graph, config, config_path.parent)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()
