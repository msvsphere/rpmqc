import re
from typing import Tuple, Union

import rpm

__all__ = ['RPMPackage']


class RPMPackage:

    def __init__(self, fd: rpm.fd, hdr: rpm.hdr, path: str):
        self.fd = fd
        self.hdr = hdr
        self.path = path

    @property
    def signature(self) -> Union[Tuple[str, str], Tuple[None, None]]:
        """
        PGP signature information from an RPM package header.

        Returns:
            A signature digest algorithm (e.g. "RSA/SHA256") and a PGP key ID.
        """
        empty = '(none)'
        for tag in ('RSAHEADER', 'DSAHEADER', 'SIGGPG', 'SIGPGP'):
            signature = self.hdr.sprintf(f'%{{{tag}:pgpsig}}')
            if signature != empty:
                break
        if signature == empty:
            return None, None
        re_rslt = re.search(r'^([\w/]+),.*?Key\s+ID\s+([a-zA-Z\d]+)$',
                            signature)
        if not re_rslt:
            raise Exception(f'unsupported signature format "{signature}"')
        digest_algo, sig_key_id = re_rslt.groups()
        return digest_algo, sig_key_id

    def __str__(self):
        return self.path
