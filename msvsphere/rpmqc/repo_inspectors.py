# repo_inspectors

import os
import hashlib
import tempfile
import subprocess
from typing import Optional, List

from .reporter import ReporterTap
import createrepo_c
from .gpg_utils import verify_asc_signature


def _repomd_test(repomd_xml_path: str, repo_reporter: ReporterTap) -> bool:
    """
    repomd.xml file test
    :param repomd_xml_path: Full path repomd.xml
    :param repo_reporter: TAP reporter object
    :return: True - test failed, all follow tests are not available. False - test passed, follow tests are allowed
    """
    test_case_name = f'{os.path.basename(repomd_xml_path)} should present'
    if os.path.isfile(repomd_xml_path):
        repo_reporter.passed(test_case_name)
        return False
    repo_reporter.failed(test_case_name, {
        'message': 'File not found',
        'path': repomd_xml_path
    })
    return True


def _get_unpack_file_hash(repo_os_path: str, archive_path: str, hash_name: str) -> Optional[str]:
    """
    Unpack file from archive and get it's hash
    :param repo_os_path: Path to repository, for example /rsync/rsync/msvsphere/9.3/AppStream/x86_64/os
    :param archive_path: Archive path relative to repo_os_path
    :param hash_name: Hash name to use
    :return: File hash or none if error
    """
    archive_full_path = os.path.join(repo_os_path, archive_path)
    if archive_path.endswith('.xz'):
        # /bin/xz --decompress --stdout arc.xz
        unpack_cmd = ['/bin/xz', '--decompress', '--stdout', archive_full_path]
        proc = subprocess.Popen(unpack_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                shell=False, text=False)
        stdout, _ = proc.communicate()
        with tempfile.TemporaryFile() as fp:
            fp.write(stdout)
            fp.seek(0)
            hash_string = hashlib.file_digest(fp, hash_name)
        return hash_string.hexdigest()
    if archive_path.endswith('.gz'):
        # gzip -d -c file.gz
        unpack_cmd = ['/bin/gzip', '-d', '-c', archive_full_path]
        proc = subprocess.Popen(unpack_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                shell=False, text=False)
        stdout, _ = proc.communicate()
        with tempfile.TemporaryFile() as fp:
            fp.write(stdout)
            fp.seek(0)
            hash_string = hashlib.file_digest(fp, hash_name)
        return hash_string.hexdigest()
    return None


def repo_files_inspector(repo_base_path: str, repo_names_list: List[str], repo_reporter: ReporterTap) -> bool:
    """
    Repository files inspector test
    :param repo_base_path: Base path to repositories. For example: /rsync/msvsphere/9.3
    :param repo_names_list: List of repositories to inspect
    :param repo_reporter: Reporter instance
    :return: True - all tests passed successfully, False - failed tests are present
    """
    for repo_name in repo_names_list:
        repo_test_reporter = repo_reporter.init_subtest(f'Repository \'{repo_name}\' files integrity test')
        repo_os_path = os.path.join(repo_base_path, repo_name, 'x86_64/os')
        repomd_xml_path = os.path.join(repo_base_path, repo_name, 'x86_64/os', 'repodata/repomd.xml')
        # Test case 1
        is_continue = _repomd_test(repomd_xml_path, repo_test_reporter)
        if is_continue:
            repo_reporter.end_subtest(repo_test_reporter)
            continue
        # Test case 2
        repomd = createrepo_c.Repomd()
        createrepo_c.xml_parse_repomd(repomd_xml_path, repomd)
        # Test all records in repo
        for rec in repomd.records:
            primary_path = os.path.join(repo_os_path, rec.location_href)
            # Test case 2.1
            test_case_name = f'Check is file {rec.location_href} present'
            if os.path.isfile(primary_path):
                repo_test_reporter.passed(test_case_name)
            else:
                repo_test_reporter.failed(test_case_name, {
                    'message': f'File {rec.location_href} is absent',
                    'path': primary_path
                })
                continue
            # Test case 2.2. Source file size check
            test_case_name = f'Check file {rec.location_href} size'
            file_size = os.path.getsize(primary_path)
            # Check packed file size
            if file_size == rec.size:
                repo_test_reporter.passed(test_case_name)
            else:
                repo_test_reporter.failed(test_case_name, {
                    'message': f'File size is not equal: repomd.xml contains {rec.size}; but actual size is {file_size}',
                    'path': primary_path
                })
            # Test case 2.3. Source file hash check
            test_case_name = f'Check file {rec.location_href} hash {rec.checksum_type}'
            with open(primary_path, "rb") as f:
                calculated_digest = hashlib.file_digest(f, rec.checksum_type)
            s_calculated_digest = calculated_digest.hexdigest()
            if s_calculated_digest == rec.checksum:
                repo_test_reporter.passed(test_case_name)
            else:
                repo_test_reporter.failed(test_case_name, {
                    'message': f'Hash is differ. repomd.xml data: type: {rec.type}; '
                               f'hash: {rec.checksum}; calculated hash is {s_calculated_digest}',
                    'path': rec.location_href
                })
            # Test case 2.4. Unpacked files hash check
            # Unpacked files test
            if rec.size_open != -1:
                # Record contains archive
                test_case_name = f'Check {rec.location_href} unpacked hash {rec.checksum_type}'
                unpack_file_hash = _get_unpack_file_hash(repo_os_path, rec.location_href, rec.checksum_type)
                if unpack_file_hash:
                    if unpack_file_hash == rec.checksum_open:
                        repo_test_reporter.passed(test_case_name)
                    else:
                        repo_test_reporter.failed(test_case_name, {
                            'message': f'Hash is differ. repomd.xml data: type: {rec.type}; '
                                       f'hash: {rec.rec.checksum_open}; calculated hash is {unpack_file_hash}',
                            'path': rec.location_href
                        })
                else:
                    repo_test_reporter.skipped(test_case_name,
                                               reason=f"Checker cannot unpack file {rec.location_href}")
        repo_reporter.end_subtest(repo_test_reporter)
    return repo_reporter.failed_count == 0


def repo_modules_inspector(repo_base_path: str, repo_names_list: List[str], repo_reporter: ReporterTap) -> bool:
    """
    Repository modules inspector test
    :param repo_base_path: Base path to repositories. For example: /rsync/msvsphere/9.3
    :param repo_names_list: List of repositories to inspect
    :param repo_reporter: Reporter instance
    :return: True - all tests passed successfully, False - failed tests are present
    """
    for repo_name in repo_names_list:
        repo_test_reporter = repo_reporter.init_subtest(f'Repository \'{repo_name}\' module test')
        repo_os_path = os.path.join(repo_base_path, repo_name, 'x86_64/os')
        repomd_xml_path = os.path.join(repo_base_path, repo_name, 'x86_64/os', 'repodata/repomd.xml')
        # Test case 1
        is_continue = _repomd_test(repomd_xml_path, repo_test_reporter)
        if is_continue:
            repo_reporter.end_subtest(repo_test_reporter)
            continue
        repomd = createrepo_c.Repomd()
        createrepo_c.xml_parse_repomd(repomd_xml_path, repomd)
        is_modules_record_found = False
        module_file_path = None
        for rec in repomd.records:
            if rec.type != 'modules':
                continue
            is_modules_record_found = True
            module_file_path = os.path.join(repo_os_path, rec.location_href)
        # Test case 2. 'module' record presence in repomd.xml
        test_case_name = f'Check repo {repo_name} have \'module\' record in repomd.xml file'
        if is_modules_record_found:
            repo_test_reporter.passed(test_case_name)
        else:
            repo_test_reporter.failed(test_case_name, {
                'message': f'Repo {repo_name} is not module. \'modules\' record is absent in repomd.xml'
            })
        # Test case 3. modules.yaml file should exist
        test_case_name = f'Check is file aka modules.yaml exist in repo'
        if module_file_path and os.path.exists(module_file_path):
            repo_test_reporter.passed(test_case_name)
        else:
            repo_test_reporter.failed(test_case_name, {
                'message': f'File is absent in repo'
            })
        repo_reporter.end_subtest(repo_test_reporter)
    return repo_reporter.failed_count == 0


def repo_groups_inspector(repo_base_path: str, repo_names_list: List[str], repo_reporter: ReporterTap) -> bool:
    """
    Repository groups inspector test
    :param repo_base_path: Base path to repositories. For example: /rsync/msvsphere/9.3
    :param repo_names_list: List of repositories to inspect
    :param repo_reporter: Reporter instance
    :return: True - all tests passed successfully, False - failed tests are present
    """
    for repo_name in repo_names_list:
        repo_test_reporter = repo_reporter.init_subtest(f'Repository \'{repo_name}\' group test')
        repo_os_path = os.path.join(repo_base_path, repo_name, 'x86_64/os')
        repomd_xml_path = os.path.join(repo_base_path, repo_name, 'x86_64/os', 'repodata/repomd.xml')
        # Test case 1. Is repomd.xml file present in repo
        is_continue = _repomd_test(repomd_xml_path, repo_test_reporter)
        if is_continue:
            repo_reporter.end_subtest(repo_test_reporter)
            continue
        repomd = createrepo_c.Repomd()
        createrepo_c.xml_parse_repomd(repomd_xml_path, repomd)
        is_group_record_found = False
        # Test case 2. comps.xml/comps.xml.xz file should present
        for rec in repomd.records:
            if rec.type in ['group', 'group_xz']:
                is_group_record_found = True
                group_file_path = os.path.join(repo_os_path, rec.location_href)
                if rec.type == 'group':
                    filename_to_search = f'comps-{repo_name}.x86_64.xml'
                else:
                    filename_to_search = f'comps-{repo_name}.x86_64.xml.xz'
                test_case_name = 'comps.xml file should present'
                if not group_file_path.endswith(filename_to_search):
                    repo_test_reporter.failed(test_case_name, {
                        'message': 'comps.xml file is absent in repomd.xml'
                    })
        # Test case 2. 'group' record presence in repomd.xml
        test_case_name = f'Check repo {repo_name} have \'group\' record in repomd.xml file'
        if is_group_record_found:
            repo_test_reporter.passed(test_case_name)
        else:
            repo_test_reporter.failed(test_case_name, {
                'message': f'Repo {repo_name} is not module. \'modules\' record is absent in repomd.xml'
            })
        repo_reporter.end_subtest(repo_test_reporter)
    return repo_reporter.failed_count == 0


def repomd_pgp_key_inspector(repo_base_path: str, repo_names_list: List[str], pgp_key_id: str,
                             repo_reporter: ReporterTap) -> bool:
    """
    repomd.xml PGP key test
    :param repo_base_path: Base path to repositories. For example: /rsync/msvsphere/9.3
    :param repo_names_list: List of repositories to inspect
    :param pgp_key_id: PGP key ID to use in test
    :param repo_reporter: Reporter instance
    :return: True - all tests passed successfully, False - failed tests are present
    """
    for repo_name in repo_names_list:
        repo_test_reporter = repo_reporter.init_subtest(f'Repository \'{repo_name}\' group test')
        repo_os_path = os.path.join(repo_base_path, repo_name, 'x86_64/os')
        repomd_xml_path = os.path.join(repo_os_path, 'repodata/repomd.xml')
        # Test case 1. Is repomd.xml file present in repo
        is_continue = _repomd_test(repomd_xml_path, repo_test_reporter)
        if is_continue:
            repo_test_reporter.end_subtest(repo_test_reporter)
            continue
        # Test case 2. Is repomd.xml.asc file present in repo
        repomd_xml_asc_path = os.path.join(repo_os_path, 'repodata/repomd.xml.asc')
        test_case_name = f'Check file {repomd_xml_asc_path} is present in repo {repo_name}'
        if os.path.isfile(repomd_xml_asc_path):
            repo_reporter.passed(test_case_name)
        else:
            repo_test_reporter.failed(test_case_name, {
                'message': 'File not found',
                'path': repomd_xml_asc_path
            })
            return False
        # Test case 3. PGP key ID check
        repodir = '/home/pavel/almalinux'
        repomd_xml_path = os.path.join(repodir, 'repomd.xml')
        repomd_xml_asc_path = os.path.join(repodir, 'repomd.xml.asc')
        test_case_name = f'PGP signature check'
        returncode, out_string, found_key_id = verify_asc_signature(repomd_xml_path, repomd_xml_asc_path, len(pgp_key_id))
        if returncode == 0:
            repo_test_reporter.passed(test_case_name)
        else:
            repo_test_reporter.failed(test_case_name, {
                'message': f'repomd.xml GPG signature check failed: return code is {returncode}. '
                           f'gpg utility output: {out_string}'
            })
        test_case_name = f'PGP key id check'
        if found_key_id == pgp_key_id:
            repo_test_reporter.passed(test_case_name)
        else:
            repo_test_reporter.failed(test_case_name, {
                'message': f'repomd.xml GPG key id check failed: found key {found_key_id}, expected {pgp_key_id}. '
                           f'gpg utility output: {out_string}'
            })
        repo_reporter.end_subtest(repo_test_reporter)
    return repo_reporter.failed_count == 0
