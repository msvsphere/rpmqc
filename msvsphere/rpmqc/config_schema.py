import os.path
import re

from schema import Schema, And, Or, Optional, Use

from .file_utils import normalize_path

__all__ = ['ConfigSchema']


StrOrRegex = Or(
    And(str, len), re.Pattern,
    error='either a non-empty string or regular expression is required'
)


ConfigSchema = Schema({
    'package': {
        Optional('signatures', default={}): {
            Optional('pgp_key_id'): And(
                str, Use(str.lower), lambda s: len(s) in (8, 16),
                error='PGP key ID length should be either 8 or 16 characters'
            ),
            Optional('pgp_digest_algo', default='RSA/SHA256'): And(
                str, Use(str.upper)
            ),
            Optional('ima_cert_path'): And(
                str, Use(normalize_path), lambda p: os.path.exists(p),
                error='IMA certificate file does not exist'
            )
        },
        Optional('tags', default={}): {
            Optional('buildhost'): StrOrRegex,
            Optional('packager'): StrOrRegex,
            Optional('vendor'): StrOrRegex
        }
    }
})
