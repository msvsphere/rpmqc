import functools
import sys
import textwrap
from typing import Optional, Union

import yaml

__all__ = ['ReporterTap']


class ReporterTap:

    def __init__(self, tests_count: Optional[int] = None, offset: int = 0,
                 description: Optional[str] = None, tap_version: int = 14):
        self._i = 0
        self._tests_count = tests_count
        self._offset = offset
        self._description = description
        self._tap_version = tap_version
        self._output = sys.stdout
        self.failed_count = 0
        self.passed_count = 0
        self.skipped_count = 0

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
        self.failed_count += 1
        self._render(False, description, payload)

    @counter
    def passed(self, description: str,
               payload: Union[dict, 'ReporterTap', None] = None):
        self.passed_count += 1
        self._render(True, description, payload)

    @counter
    def skipped(self, description: str,
                payload: Union[dict, 'ReporterTap', None] = None,
                reason: Optional[str] = None):
        self.skipped_count += 1
        self._render(True, description, payload, skip=True, reason=reason)

    def init_subtest(self, description: Optional[str] = None) -> 'ReporterTap':
        self._output.write(f'{self._indent}# Subtest')
        if description:
            self._output.write(f': {description}')
        self._output.write('\n')
        return ReporterTap(offset=self._offset + 4, description=description)

    def end_subtest(self, subtest: 'ReporterTap'):
        if subtest.failed_count:
            self.failed(subtest._description)
        else:
            self.passed(subtest._description)

    def _render(self, success: bool, description: str,
                payload: Union[dict, 'ReporterTap', None] = None,
                skip: bool = False, reason: Optional[str] = None):
        # print the test plan row if we know the final tests count
        if self._i == 1 and self._tests_count is not None:
            self.print_plan(self._tests_count)
        status = 'ok' if success else 'not ok'
        self._output.write(f'{self._indent}{status} {self._i} - {description}')
        if skip:
            self._output.write(' # SKIP')
            if reason:
                self._output.write(f' {reason}')
        self._output.write('\n')
        if payload:
            yaml_str = yaml.dump(payload, explicit_start=True,
                                 explicit_end=True, indent=2)
            yaml_str = textwrap.indent(yaml_str, '  ' + self._indent)
            self._output.write(yaml_str)

    def print_plan(self, tests_count: Optional[int] = None):
        if tests_count is None:
            tests_count = self._i
        self._output.write(f'{self._indent}1..{tests_count}\n')

    def print_header(self):
        self._output.write(f'TAP version {self._tap_version}\n')

    def print_summary(self):
        counters = ((self.passed_count, 'Passed'),
                    (self.skipped_count, 'Skipped'),
                    (self.failed_count, 'Failed'))
        for counter, label in counters:
            if not counter:
                continue
            self._output.write(f'{self._indent}# {label} {counter} of '
                               f'{self._i} tests\n')

    @property
    def _indent(self) -> str:
        return ' ' * self._offset
