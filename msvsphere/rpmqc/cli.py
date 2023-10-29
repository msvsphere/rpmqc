from enum import IntEnum
import argparse
import sys
import traceback

from . import __version__
from .config import Config
from .file_utils import normalize_path
from .runner import run_repo_inspections, run_rpm_inspections


class ExitCodes(IntEnum):

    """
    The program exit codes (pytest-compatible).

    References:
        https://pytest.org/en/latest/reference/reference.html#pytest.ExitCode
    """

    PASSED = 0               # all tests were successful
    FAILED = 1               # some tests failed
    INTERRUPTED = 2          # the program was terminated by a user
    INTERNAL_ERROR = 3       # unexpected error happened
    USAGE_ERROR = 4          # command line arguments/config error
    NO_TESTS_FOUND = 5       # no tests were found


class ArgParser(argparse.ArgumentParser):

    """
    ArgumentParser implementation that uses a custom exit code on usage error.
    """

    def error(self, message: str):
        self.print_usage(sys.stderr)
        self.exit(ExitCodes.USAGE_ERROR, f'{self.prog}: {message}\n')


def init_arg_parser() -> ArgParser:
    """
    Initializes a command line argument parser.

    Returns:
        Command line arguments parser.
    """
    parser = ArgParser(prog='rpmqc',
                       description='RPM packages quality control tool')
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__}')
    commands = parser.add_subparsers(dest='command', required=True,
                                     title='inspection commands')
    # repository inspection subcommand
    inspect_repo_cmd = commands.add_parser(
        'inspect-repo', help='inspect a YUM/DNF repository',
        description='Runs inspections for the entire YUM/DNF repository'
    )
    inspect_repo_cmd.add_argument('-c', '--config', required=True,
                                  help='configuration file path')
    inspect_repo_cmd.add_argument('repo_path', metavar='REPO_PATH',
                                  type=normalize_path,
                                  help='path to a repository under test')
    # RPM inspection subcommand
    inspect_rpm_cmd = commands.add_parser(
        'inspect-rpm', help='inspect an RPM package',
        description='Runs inspections for a specified RPM package'
    )
    inspect_rpm_cmd.add_argument('-c', '--config', required=True,
                                 help='configuration file path')
    inspect_rpm_cmd.add_argument('rpm_path', metavar='RPM_PATH', nargs='+',
                                 type=normalize_path,
                                 help='path to RPM(s) under test')
    return parser


def main():
    arg_parser = init_arg_parser()
    args = arg_parser.parse_args(sys.argv[1:])
    cfg = Config(args.config)
    success = False
    try:
        if args.command == 'inspect-repo':
            success = run_repo_inspections(cfg, args.repo_path)
        elif args.command == 'inspect-rpm':
            success = run_rpm_inspections(cfg, args.rpm_path)
    except KeyboardInterrupt:
        sys.stderr.write('rpmqc: interrupted by user\n')
        sys.exit(ExitCodes.INTERRUPTED)
    except Exception:
        traceback.print_exc()
        sys.exit(ExitCodes.INTERNAL_ERROR)
    sys.exit(ExitCodes.PASSED if success else ExitCodes.FAILED)
