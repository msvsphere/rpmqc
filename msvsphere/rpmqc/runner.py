from contextlib import closing
from typing import Iterable, List

import rpm

from .config import Config
from .inspectors.pkg_base_inspector import PkgBaseInspector
from .reporter import ReporterTap
from .rpm_package import RPMPackage

__all__ = ['run_rpm_inspections']


def load_inspections(cfg: Config) -> List[PkgBaseInspector]:
    """
    Initializes RPM package inspectors.

    Args:
        cfg: Configuration object.

    Returns:
        List of RPM package inspectors.
    """
    # TODO: use dynamical loading via pkgutil
    inspections = []
    from .inspectors.pkg_signature_inspector import PkgSignatureInspectorInspector
    from .inspectors.pkg_tags_inspector import PkgTagsInspectorInspector
    inspections.append(PkgSignatureInspectorInspector(cfg))
    inspections.append(PkgTagsInspectorInspector(cfg))
    return inspections


def run_rpm_inspections(cfg: Config, rpm_paths: Iterable):
    ts = rpm.TransactionSet('', rpm._RPMVSF_NOSIGNATURES)
    inspectors = load_inspections(cfg)
    for rpm_path in rpm_paths:
        with closing(rpm.fd(rpm_path, 'r')) as fd:
            hdr = ts.hdrFromFdno(fd)
            pkg = RPMPackage(fd, hdr, rpm_path)
            reporter = ReporterTap()
            for inspector in inspectors:
                inspector.inspect(pkg, reporter)
