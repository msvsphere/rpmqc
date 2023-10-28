from .pkg_base_inspector import *

__all__ = ['PkgSignatureInspectorInspector']


class PkgSignatureInspectorInspector(PkgBaseInspector):

    """
    Verifyies an RPM package PGP signature and a digest algorithm.
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        sign_cfg = cfg.data.get('package', {}).get('signatures', {})
        self.pgp_key_id = sign_cfg.get('pgp_key_id')
        self.pgp_digest_algo = sign_cfg.get('pgp_digest_algo')

    def inspect(self, pkg: RPMPackage, reporter: ReporterTap):
        digest_algo, key_id = pkg.signature
        test_case = (f'PGP signature is {self.pgp_key_id} '
                     f'({self.pgp_digest_algo})')
        if not key_id:
            reporter.failed(test_case, {'message': 'package is not signed'})
        elif key_id[-len(self.pgp_key_id):] != self.pgp_key_id:
            reporter.failed(test_case, {
                'message': 'unexpected package signature',
                'got': key_id,
                'expected': self.pgp_key_id
            })
        elif digest_algo != self.pgp_digest_algo:
            reporter.failed(test_case, {
                'message': 'unexpected package signature digest algorithm',
                'got': digest_algo,
                'expected': self.pgp_digest_algo
            })
        else:
            reporter.passed(test_case)
