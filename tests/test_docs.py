import re
import shlex
from pathlib import Path
from typing import Protocol, cast

from openlp_vault.cli import cli


class Parameter(Protocol):
    opts: list[str]
    secondary_opts: list[str]


class Command(Protocol):
    params: list[Parameter]


class CommandGroup(Command, Protocol):
    commands: dict[str, Command]


ROOT = Path(__file__).parents[1]
CLI = cast(CommandGroup, cli)
DOC_NAMES = {"architecture.md", "drive_setup.md", "usage.md"}
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
BASH_BLOCK = re.compile(r"```bash\n(.*?)```", re.DOTALL)


def markdown_files() -> list[Path]:
    return [
        ROOT / "README.md",
        ROOT / "README.es.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "CONTRIBUTING.es.md",
        *sorted((ROOT / "docs").rglob("*.md")),
    ]


def test_each_document_has_an_english_and_spanish_version():
    assert {path.name for path in (ROOT / "docs" / "en").glob("*.md")} == DOC_NAMES
    assert {path.name for path in (ROOT / "docs" / "es").glob("*.md")} == DOC_NAMES
    assert (ROOT / "README.md").is_file()
    assert (ROOT / "README.es.md").is_file()
    assert (ROOT / "CONTRIBUTING.md").is_file()
    assert (ROOT / "CONTRIBUTING.es.md").is_file()

    document_pairs = [
        (ROOT / "README.md", ROOT / "README.es.md"),
        (ROOT / "CONTRIBUTING.md", ROOT / "CONTRIBUTING.es.md"),
        *((ROOT / "docs" / "en" / name, ROOT / "docs" / "es" / name) for name in DOC_NAMES),
    ]
    for english, spanish in document_pairs:
        english_levels = [
            len(line) - len(line.lstrip("#"))
            for line in english.read_text(encoding="utf-8").splitlines()
            if line.startswith("#")
        ]
        spanish_levels = [
            len(line) - len(line.lstrip("#"))
            for line in spanish.read_text(encoding="utf-8").splitlines()
            if line.startswith("#")
        ]
        assert english_levels == spanish_levels


def test_all_relative_markdown_links_exist():
    for document in markdown_files():
        for target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            linked_path = (document.parent / target.split("#", 1)[0]).resolve()
            assert linked_path.exists(), f"{document.relative_to(ROOT)} links to missing {target}"


def test_documented_cli_commands_and_options_exist():
    root_options = {
        option
        for parameter in CLI.params
        for option in (*parameter.opts, *parameter.secondary_opts)
    } | {"--help"}

    for document in markdown_files():
        text = document.read_text(encoding="utf-8")
        for block in BASH_BLOCK.findall(text):
            for command_line in re.sub(r"\\\n\s*", " ", block).splitlines():
                tokens = shlex.split(command_line)
                if "openlp-vault" not in tokens:
                    continue
                arguments = tokens[tokens.index("openlp-vault") + 1 :]
                command_name = next((item for item in arguments if not item.startswith("-")), None)
                if command_name is None:
                    allowed_options = root_options
                else:
                    assert command_name in CLI.commands, (
                        f"{document.relative_to(ROOT)} documents unknown command {command_name}"
                    )
                    command = CLI.commands[command_name]
                    allowed_options = root_options | {
                        option
                        for parameter in command.params
                        for option in (*parameter.opts, *parameter.secondary_opts)
                    }
                for option in (item for item in arguments if item.startswith("--")):
                    assert option in allowed_options, (
                        f"{document.relative_to(ROOT)} documents unknown option {option}"
                    )
