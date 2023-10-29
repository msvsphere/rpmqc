from contextlib import closing
import os.path
from typing import Iterable, List

import createrepo_c
import rpm

from .config import Config
from .inspectors.pkg_base_inspector import PkgBaseInspector
from .reporter import ReporterTap
from .rpm_package import RPMPackage

__all__ = ['run_repo_inspections', 'run_rpm_inspections']


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
    from .inspectors.pkg_signature_inspector import PkgSignatureInspector
    from .inspectors.pkg_ima_inspector import PkgIMASignatureInspector
    from .inspectors.pkg_tags_inspector import PkgTagsInspector
    inspections.append(PkgSignatureInspector(cfg))
    inspections.append(PkgIMASignatureInspector(cfg))
    inspections.append(PkgTagsInspector(cfg))
    return inspections


def run_rpm_inspections(cfg: Config, rpm_paths: Iterable) -> bool:
    ts = rpm.TransactionSet('', rpm._RPMVSF_NOSIGNATURES)
    inspectors = load_inspections(cfg)
    reporter = ReporterTap()
    reporter.print_header()
    for rpm_path in rpm_paths:
        rpm_basename = os.path.basename(rpm_path)
        with closing(rpm.fd(rpm_path, 'r')) as fd:
            hdr = ts.hdrFromFdno(fd)
            pkg = RPMPackage(fd, hdr, rpm_path)
            pkg_reporter = reporter.init_subtest(rpm_basename)
            for inspector in inspectors:
                inspector.inspect(pkg, pkg_reporter)
            pkg_reporter.print_plan()
            reporter.end_subtest(pkg_reporter)
    reporter.print_plan()
    reporter.print_summary()
    return reporter.failed_count == 0


def run_repo_inspections(cfg: Config, repo_path: str):
    repomd_xml_path = os.path.join(repo_path, 'repodata/repomd.xml')
    repomd = createrepo_c.Repomd()
    createrepo_c.xml_parse_repomd(repomd_xml_path, repomd)
    primary_path = None
    for rec in repomd.records:
        if rec.type == 'primary':
            primary_path = os.path.join(repo_path, rec.location_href)
            break
    packages = []
    def pkg_callback(pkg):
        packages.append(pkg.location_href)
    createrepo_c.xml_parse_primary(primary_path, pkgcb=pkg_callback,
                                   do_files=False)
    return run_rpm_inspections(cfg, (os.path.join(repo_path, p)
                                     for p in packages))
