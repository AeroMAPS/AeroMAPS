import logging
import os
from importlib.resources import files
from pathlib import Path
import shutil
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, RawDescriptionHelpFormatter


MAIN_NOTEBOOK_NAME = (Path(__file__).parent.parent / "gui/gui.ipynb").resolve()
TUTORIAL_NOTEBOOKS_DIR = (Path(__file__).parent.parent / "notebooks").resolve()


class Main:
    """
    Class for managing command line and doing associated actions

    Examples
    --------
    In a terminal, run the following command to download the tutorial notebooks:
    ```python
    >>> aeromaps notebooks
    ```

    In a terminal, run the following command to launch a local graphical user interface:
    ```python
    >>> aeromaps gui
    ```
    """

    def __init__(self):
        class _CustomFormatter(RawDescriptionHelpFormatter, ArgumentDefaultsHelpFormatter):
            pass

        self.parser = ArgumentParser(
            description="AeroMAPS main program", formatter_class=_CustomFormatter
        )

    @staticmethod
    def _gui(args):
        """Run AeroMAPS graphical user interface locally or with server configuration."""
        machine = "server" if args.server else "local"
        print(MAIN_NOTEBOOK_NAME)
        if machine == "server":
            command = (
                "voila "
                "--port=8080 "
                "--no-browser "
                "--MappingKernelManager.cull_idle_timeout=7200 "
                """--VoilaConfiguration.file_whitelist="['.*\.(png|jpg|gif|xlsx|ico|pdf|json)']" """
            )
        else:
            command = (
                "voila "
                """--VoilaConfiguration.file_whitelist="['.*\.(png|jpg|gif|xlsx|ico|pdf|json)']" """
            )

        os.system(command + str(MAIN_NOTEBOOK_NAME))

    @staticmethod
    def _notebooks(args=None):
        """
        Creates notebooks/ and resources/ folders with pre-configured Jupyter notebooks tutorials and default resources.
        """

        src_dir = files("aeromaps") / "notebooks" / "tutorials"
        dest_dir = Path.cwd() / "notebooks"
        dest_dir.mkdir(exist_ok=True)

        for item in src_dir.iterdir():
            target = dest_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy(item, target)

        print(f"Tutorial notebooks added in: {dest_dir}")

        src_dir = files("aeromaps") / "resources"
        dest_dir = Path.cwd() / "resources"
        dest_dir.mkdir(exist_ok=True)

        IGNORED = {"climate_data", "cost_data", "energy_data"}

        for item in src_dir.iterdir():
            if item.name in IGNORED:
                continue
            target = dest_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy(item, target)

        print(f"Resources added in: {dest_dir}")

    def run(self):
        subparsers = self.parser.add_subparsers(title="sub-commands")

        # sub-command for running AeroMAPS GUI
        parser_gui = subparsers.add_parser(
            "gui",
            help="run AeroMAPS graphical user interface",
            description="run AeroMAPS graphical user interface",
        )

        parser_gui.add_argument(
            "--server",
            action="store_true",
            help="to be used if ran on server",
        )
        parser_gui.set_defaults(func=self._gui)

        # sub-command for download AeroMAPS tutorial notebooks
        parser_notebooks = subparsers.add_parser(
            "notebooks",
            help="download notebooks",
            description="download notebooks",
        )
        parser_notebooks.set_defaults(func=self._notebooks)

        # Parse
        args = self.parser.parse_args()
        try:
            args.func(args)
        except AttributeError:
            self.parser.print_help()


def main():
    log_format = "%(levelname)-8s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)
    Main().run()


if __name__ == "__main__":
    main()
