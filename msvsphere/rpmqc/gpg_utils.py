# functions to use /usr/bin/gpg utility

import os
import subprocess
from typing import Tuple, Optional


def get_key(gpg_out_str: str) -> Optional[str]:
    """
    Get key from gpg utility output.
    :param gpg_out_str: gpg utility output string
    :return: key from gpg utility output, None if not found
    """
    lines = gpg_out_str.split('\n')
    # out_str example:
    # gpg: Signature made Wed Feb 28 11:45:22 2024 MSK
    # gpg:                using RSA key 65A8574FF9AB78C0A22DF67B5270D8D992A37F50
    # gpg: Good signature from "xxx <xxx@yyy.com>" [ultimate]
    for line in lines:
        if 'key' in line:
            line = line.strip()
            try:
                key = line.split(' ')[-1:][0]
                return key
            except IndexError:
                pass
    return None


def verify_asc_signature(file_to_check: str, asc_file: str, need_key_length: int) -> Tuple[int, str, Optional[str]]:
    """
    Verify file GPG signature using gpg utility and ASC signature
    :param file_to_check: File name to check
    :param asc_file: .asc file with signature
    :param need_key_length: Need key length to return
    :return: tuple: (gpg utility retcode, gpg utility output, key)
    """
    # /usr/bin/gpg --verify repomd.xml.asc repomd.xml
    gpg_cmd_list = ["/usr/bin/gpg", "--verify", asc_file, file_to_check]
    environment = {
        'LANGUAGE': os.environ.get('LANGUAGE') or 'en',
        'GPG_TTY': os.environ.get('GPG_TTY') or '',
        'DISPLAY': os.environ.get('DISPLAY') or '',
        'GPG_AGENT_INFO': os.environ.get('GPG_AGENT_INFO') or '',
        'GPG_PINENTRY_PATH': os.environ.get('GPG_PINENTRY_PATH') or '',
    }
    process = subprocess.Popen(gpg_cmd_list,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env=environment, shell=False, text=True)
    _stdout, _ = process.communicate()
    stdout_string = _stdout.strip()
    key = get_key(stdout_string)
    if len(key) >= need_key_length:
        key_id = key[len(key) - need_key_length:].lower()
    else:
        key_id = key
    return process.returncode, stdout_string, key_id
