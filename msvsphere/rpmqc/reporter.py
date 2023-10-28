import abc
import functools
import sys
import textwrap
from typing import Optional, Union

import yaml

__all__ = ['ReporterTap']


class ReporterTap:

    def __init__(self, tests_count: Optional[int] = None,
                 tap_version: int = 14):
        self._i = 0
        self._tests_count = tests_count
        self._tap_version = tap_version
        self._output = sys.stdout

    def counter(fn):
        @functools.wraps(fn)
        def wrap(self, *args, **kwargs):
            self._i += 1
            if self._tests_count is not None and self._tests_count < self._i:
                raise Exception('executed more tests than planned')
            return fn(self, *args, **kwargs)
        return wrap

    @counter
    def failed(self, description: str,
               payload: Union[dict, 'ReporterTap', None] = None):
        self._render(False, description, payload)

    @counter
    def passed(self, description: str,
               payload: Union[dict, 'ReporterTap', None] = None):
        self._render(True, description, payload)

    def _render(self, success: bool, description: str,
                payload: Union[dict, 'ReporterTap', None] = None):
        # print the test plan row if we know the final tests count
        if self._i == 1 and self._tests_count is not None:
            self.print_plan(self._tests_count)
        status = 'ok' if success else 'not ok'
        self._output.write(f'{status} {self._i} - {description}')
        self._output.write('\n')
        if payload:
            yaml_str = yaml.dump(payload, explicit_start=True,
                                 explicit_end=True, indent=2)
            yaml_str = textwrap.indent(yaml_str, '  ')
            self._output.write(yaml_str)

    def print_plan(self, tests_count: Optional[int] = None):
        if tests_count is None:
            tests_count = self._i
        self._output.write(f'1..{tests_count}')

    def print_version(self):
        self._output.write(f'TAP version {self._tap_version}\n')
