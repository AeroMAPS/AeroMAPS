import logging
import os
import os.path as pth
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, RawDescriptionHelpFormatter


MAIN_NOTEBOOK_NAME = pth.join(pth.dirname(__file__), "app.ipynb")


class Main:
    """
    Class for managing command line and doing associated actions
    """

    def __init__(self):
        class _CustomFormatter(RawDescriptionHelpFormatter, ArgumentDefaultsHelpFormatter):
            pass

        self.parser = ArgumentParser(
            description="AeroMAPS main program", formatter_class=_CustomFormatter
        )

    @staticmethod
    def _run(args):
        """Run AeroMAPS locally or with server configuration."""
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

    # ENTRY POINT ==================================================================================
    def run(self):
        """Main function."""
        subparsers = self.parser.add_subparsers(title="sub-commands")

        # sub-command for running AeroMAPS -------------------------------------
        parser_run = subparsers.add_parser(
            "run",
            help="run AeroMAPS",
            description="run AeroMAPS",
        )

        parser_run.add_argument(
            "--server",
            action="store_true",
            help="to be used if ran on server",
        )
        parser_run.set_defaults(func=self._run)

        # Parse ------------------------------------------------------------------------------------
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
