import argparse
import sys

from . import __version__
from .config import Config
from .file_utils import normalize_path
from .runner import run_rpm_inspections


def init_arg_parser() -> argparse.ArgumentParser:
    """
    Initializes a command line argument parser.

    Returns:
        Command line arguments parser.
    """
    parser = argparse.ArgumentParser(
        prog='rpmqc',
        description='RPM packages quality control tool'
    )
    parser.add_argument('-c', '--config', help='configuration file path',
                        required=True)
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__}')
    commands = parser.add_subparsers(dest='command', required=True,
                                     title='inspection commands')
    # RPM inspection subcommand
    inspect_rpm_cmd = commands.add_parser('inspect-rpm',
                                          help='inspect an RPM package')
    inspect_rpm_cmd.add_argument('rpm_path', metavar='RPM_PATH', nargs='+',
                                 type=normalize_path,
                                 help='path to RPM(s) under test')
    return parser


def main():
    arg_parser = init_arg_parser()
    args = arg_parser.parse_args(sys.argv[1:])
    cfg = Config(args.config)
    if args.command == 'inspect-rpm':
        run_rpm_inspections(cfg, args.rpm_path)
