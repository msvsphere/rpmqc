import os.path
import re

from schema import Schema, And, Or, Optional, Use

from .file_utils import normalize_path

__all__ = ['ConfigSchema']


StrOrRegex = Or(
    And(str, len), re.Pattern,
    error='either a non-empty string or regular expression is required'
)


def comma_str_to_list(comma_str: str) -> list:
    """
    Converts a comma separated string to a list of string.
    Examples:
     - 'AppStream,BaseOS,CRB' --> ['AppStream', 'BaseOS', 'CRB']
     - 'AppStream, BaseOS, CRB' --> ['AppStream', 'BaseOS', 'CRB']
    :param comma_str: Input string
    :return: list of string
    """
    return [s.strip() for s in comma_str.split(',')]


def string_or_number_to_lower_string(input_sn: str) -> str:
    """
    Converts a string or number to string in lower case
    :param input_sn: String or number to convert
    :return:
    """
    return str(input_sn).lower()


ConfigSchema = Schema({
    'package': {
        Optional('signatures', default={}): {
            Optional('pgp_key_id'): And(
                Or(str, int), Use(string_or_number_to_lower_string), lambda s: len(s) in (8, 16),
                error='RPM packages PGP key ID length should be either 8 or 16 characters'
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
    },
    'repos': {
        Optional('repo_names_list'): And(
            str, Use(comma_str_to_list)
        ),
        Optional('modules_repo_names_list'): And(
            str, Use(comma_str_to_list)
        ),
        Optional('groups_repo_names_list'): And(
            str, Use(comma_str_to_list)
        ),
        Optional('repomd_xml_pgp_repos_list'): And(
            str, Use(comma_str_to_list)
        ),
        Optional('repomd_xml_pgp_key_id'): And(
            Or(str, int), Use(string_or_number_to_lower_string), lambda s: len(str(s)) in (8, 16),
            error='repomd.xml PGP key ID length should be either 8 or 16 characters'
        )
    }
})
