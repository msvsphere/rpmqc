import re

import rpm

from .pkg_base_inspector import *

__all__ = ['PkgTagsInspector']


class PkgTagsInspector(PkgBaseInspector):

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def inspect(self, pkg: RPMPackage, reporter: ReporterTap):
        for tag_name, tag_id, expected in self._iter_tags():
            value = pkg.hdr[tag_id]
            if isinstance(expected, re.Pattern):
                rslt = expected.match(value)
                expected_str = f'regex:{expected.pattern}'
            else:
                rslt = (value == expected)
                expected_str = expected
            test_case = f'{tag_name} RPM tag value is {expected_str}'
            if rslt:
                reporter.passed(test_case)
            else:
                reporter.failed(test_case, {
                    'message': f'unexpected {tag_name} RPM tag value',
                    'got': value,
                    'expected': expected_str
                })

    def _iter_tags(self):
        tags_cfg = self.cfg.data.get('package', {}).get('tags', {})
        for tag_name, expected in tags_cfg.items():
            tag_id = getattr(rpm, f'RPMTAG_{tag_name.upper()}')
            yield tag_name, tag_id, expected
