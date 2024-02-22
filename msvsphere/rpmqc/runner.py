from contextlib import closing
import os.path
from typing import Iterable, List

import createrepo_c
import rpm

from .config import Config
from .inspectors.pkg_base_inspector import PkgBaseInspector
from .reporter import ReporterTap
from .rpm_package import RPMPackage
from .repo_inspectors import repo_files_inspector, repo_modules_inspector, repo_groups_inspector, \
    repomd_pgp_key_inspector

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


def run_repo_inspections(cfg: Config, repo_path: str) -> bool:
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


def run_repo_metadata_inspections(cfg: Config, repo_path: str) -> bool:
    """
    Run the repositories metadata tests
    :param cfg: Config dict
    :param repo_path: Full path to the repositories
    """
    repo_reporter = ReporterTap()
    repo_reporter.print_header()
    # 1. File tests
    try:
        repo_names_list = cfg.data['repos']['repo_names_list']
        files_result = repo_files_inspector(repo_path, repo_names_list, repo_reporter)
    except KeyError:
        repo_test_reporter = repo_reporter.init_subtest('Repository files integrity test')
        repo_test_reporter.skipped('Test skipped',
                                   reason='repos.repo_names_list key is missing in provided config')
        repo_reporter.end_subtest(repo_test_reporter)
        files_result = True
    # 2. Module tests
    try:
        modules_repo_names_list = cfg.data['repos']['modules_repo_names_list']
        repo_result = repo_modules_inspector(repo_path, modules_repo_names_list, repo_reporter)
    except KeyError:
        repo_test_reporter = repo_reporter.init_subtest('Repository module test')
        repo_test_reporter.skipped('Test skipped',
                                   reason='repos.modules_repo_names_list key is missing in provided config')
        repo_reporter.end_subtest(repo_test_reporter)
        repo_result = True
    # 3. Group tests
    try:
        groups_repo_names_list = cfg.data['repos']['groups_repo_names_list']
        group_result = repo_groups_inspector(repo_path, groups_repo_names_list, repo_reporter)
    except KeyError:
        repo_test_reporter = repo_reporter.init_subtest('Repository group test')
        repo_test_reporter.skipped('Test skipped',
                                   reason='repos.groups_repo_names_list key is missing in provided config')
        repo_reporter.end_subtest(repo_test_reporter)
        group_result = True
    # 4. repomd.xml PGP key test
    try:
        repomd_xml_pgp_repos_list = cfg.data['repos']['repomd_xml_pgp_repos_list']
        repomd_xml_pgp_key_id = cfg.data['repos']['repomd_xml_pgp_key_id']
        repo_gpg_result = repomd_pgp_key_inspector(repo_path, repomd_xml_pgp_repos_list, repomd_xml_pgp_key_id,
                                                   repo_reporter)
    except KeyError:
        repo_test_reporter = repo_reporter.init_subtest('repomd.xml PGP key test')
        repo_test_reporter.skipped('Test skipped',
                                   reason='repos.repomd_xml_pgp_key_id key is missing in provided config')
        repo_reporter.end_subtest(repo_test_reporter)
        repo_gpg_result = True
    repo_reporter.print_plan()
    repo_reporter.print_summary()
    return files_result and repo_result and group_result and repo_gpg_result
