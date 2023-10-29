from contextlib import closing
import stat

from .pkg_base_inspector import *
from ..ima_utils import *

import cryptography.exceptions
import rpm

__all__ = ['PkgIMASignatureInspector']


class PkgIMASignatureInspector(PkgBaseInspector):

    """
    Verifies an RPM package IMA signatures.
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        sign_cfg = cfg.data.get('package', {}).get('signatures', {})
        ima_cert_path = sign_cfg.get('ima_cert_path')
        if ima_cert_path:
            self.ima_pub_key, self.ima_sign_algo = (
                load_ima_pub_key(ima_cert_path)
            )
        else:
            self.ima_pub_key = self.ima_sign_algo = None

    def inspect(self, pkg: RPMPackage, reporter: ReporterTap):
        if not self.ima_pub_key:
            reporter.skipped('IMA signature',
                             reason='no IMA certificate configured')
            return
        expected_key_id = get_ima_pub_key_id(self.ima_pub_key)
        test_case = f'IMA signature is {expected_key_id}'
        files = rpm.files(pkg.hdr)
        with closing(rpm.fd(pkg.fd, 'r',
                            pkg.hdr['payloadcompressor'])) as payload, \
                closing(files.archive(payload)) as archive:
            for f in archive:
                if stat.S_ISDIR(f.mode) or stat.S_ISLNK(f.mode) or \
                        not archive.hascontent():
                    # skip directories and symlinks because IMA operates only
                    # on files, also skip hardlink records
                    continue
                elif f.imasig is None:
                    reporter.failed(test_case, {
                        'message': 'IMA signature is not found',
                        'path': f.name
                    })
                    return
                key_id, sig = parse_ima_signature(f.imasig)
                try:
                    self.ima_pub_key.verify(sig, archive.read(),
                                            self.ima_sign_algo)
                except cryptography.exceptions.InvalidSignature:
                    reporter.failed(test_case, {
                        'message': 'unexpected IMA signature',
                        'got': key_id,
                        'expected': expected_key_id,
                        'path': f.name
                    })
                    return
            reporter.passed(test_case)
