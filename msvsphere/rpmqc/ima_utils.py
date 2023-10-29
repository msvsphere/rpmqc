import logging
import struct
from typing import Optional, Tuple

import cryptography.hazmat.primitives.asymmetric.ec as crypto_ec
import cryptography.hazmat.primitives.hashes as crypto_hashes
import cryptography.hazmat.primitives.serialization as crypto_serialization
import cryptography.x509

__all__ = ['get_ima_pub_key_id', 'load_ima_pub_key', 'parse_ima_signature',
           'IMAError']


class IMAError(Exception):

    pass


def get_ima_pub_key_id(pub_key: crypto_ec.EllipticCurvePublicKey) -> str:
    """
    Extracts an IMA signature public key ID.

    Args:
        pub_key: IMA signature public key.

    Returns:
        Public key ID.
    """
    key_id = cryptography.x509.SubjectKeyIdentifier.from_public_key(pub_key)
    return key_id.digest[-4:].hex()


def load_ima_pub_key(
        cert_path: str, log: Optional[logging.Logger] = None
) -> Tuple[crypto_ec.EllipticCurvePublicKey,
           crypto_ec.EllipticCurveSignatureAlgorithm]:
    """
    Loads an IMA signature public key from a certificate file.

    This function supports public/private der/pem certificates.

    Args:
        cert_path: Certificate file path.
        log: Logger to use for debug messages.

    Returns:
        IMA signature public key and signature algorithm.

    Raises:
        IMAError: If public key load failed.
    """
    if not log:
        log = logging.getLogger(__name__)
    loaders = (
        (cryptography.x509.load_der_x509_certificate, {}),
        (crypto_serialization.load_pem_private_key, {'password': None}),
        (crypto_serialization.load_der_private_key, {'password': None})
    )
    with open(cert_path, 'rb') as fd:
        content = fd.read()
    # try different loaders because we don't know what type of certificate
    # we got (public or private, der or pem)
    for loader, kwargs in loaders:
        try:
            log.debug(f'loading IMA certificate using loader {loader}')
            cert = loader(content, **kwargs)
            # NOTE: RPM uses only SHA256 for IMA signatures
            hash_algo = crypto_hashes.SHA256()
            pub_key = cert.public_key()
            # NOTE: starting from cryptography 41.0.0 version there is the
            #       "signature_algorithm_parameters" property that returns
            #       a signature algorithm, but EL8/9 and Fedora<39 have an
            #       older version, so we have to guess here
            if isinstance(pub_key, crypto_ec.EllipticCurvePublicKey):
                sign_algo = crypto_ec.ECDSA(hash_algo)
            else:
                # TODO: add RSA keys support
                raise IMAError(f'unsupported IMA public key type '
                               f'{type(pub_key)}')
            return pub_key, sign_algo
        except Exception as e:
            log.debug(f'failed to load IMA certificate using loader '
                      f'{loader}: {e}')
    raise IMAError(f'failed to load IMA public key from {cert_path}')


def parse_ima_signature(sig_hdr: bytes) -> Tuple[str, bytes]:
    """
    Extracts an IMA public key and signature from a file signature header.

    Args:
        sig_hdr: File IMA signature.

    Notes:
         The constant values are taken from the imaevm.h file.

         See the signature_v2_hdr structure definition in the imaevm.h file
         for a signature header format description.

    Returns:
        Public key ID and a file signature.
    """
    EVM_IMA_XATTR_DIGSIG = 3
    DIGSIG_VERSION_2 = 2
    PKEY_HASH_SHA256 = 4
    byte_sign = bytearray(sig_hdr)
    if byte_sign[0] != EVM_IMA_XATTR_DIGSIG:
        raise IMAError(f'invalid signature type {byte_sign[0]}')
    elif byte_sign[1] != DIGSIG_VERSION_2:
        raise IMAError(f'only V2 format signatures are supported')
    elif byte_sign[2] != PKEY_HASH_SHA256:
        raise IMAError(f'only SHA256 digest algorithm is supported')
    pub_key_id = bytes(byte_sign[3:7]).hex()
    sig_size = struct.unpack('>H', byte_sign[7:9])[0]
    signature = bytes(byte_sign[9:sig_size+9])
    return pub_key_id, signature
