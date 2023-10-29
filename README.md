# rpmqc

The RPM packages quality control tool.

Ideologically, rpmqc is similar to [rpmlint](https://github.com/rpm-software-management/rpmlint),
but they solve slightly different tasks: rpmlint is an awesome tool for checking
an RPM package for common errors (a packager's tool), while rpmqc is designed
to quickly check an entire repository/compose for typical release manager's
errors like missing signatures or wrong branding.


## Install

All requirements are available from Fedora or EL 8/9 + EPEL repositories:

```
# EL 9 derivatives
$ sudo dnf install -y --enablerepo=epel python3-createrepo_c \
      python3-cryptography python3-rpm python3-schema python3-pyyaml \
      python3-virtualenv
```

Currently, there is no RPM package available, so the recommended way is to
install rpmqc from PyPI using a virtual environment:

```shell
$ mkdir rpmqc
$ cd rpmqc
$ virtualenv --system-site-packages .venv
$ . .venv/bin/activate
$ pip install rpmqc

$ rpmqc --version
rpmqc 0.0.4
```

optionally, you can create an `rpmqc` alias in your `~/.bashrc`:

```shell
# don't forget to adjust the path accordingly to your configuration
alias rpmqc="rpmqc/.venv/bin/rpmqc"
```


## Configuration

The program expects a configuration file in YAML format:

```yaml
---
package:
  signatures:
    # expected RPM package signature PGP key id
    pgp_key_id: 8BDA73A4
    # IMA signature public certificate path
    ima_cert_path: ~/.vault/ima-sign.x509
  tags:
    # expected RPM tag values, regular expressions are also supported
    buildhost: !regex ^builder-(x86|arm64)-\d+\.msvsphere-os\.ru$
    packager: MSVSphere
    vendor: MSVSphere
...
```

all inspections are optional and will be performed if a corresponding
configuration file option is set.


## Usage

Currently, rpmqc supports only two modes: single (or multiple) RPM packages
checking (`inspect-rpm`) and an entire repository checking (`inspect-repo`).
For usage instructions see `rpmqc inspect-rpm --help` and
`rpmqc inspect-repo --help`, respectively.


## License

rpmqc is available under the terms of the
[GNU General Public License v2.0](LICENSE), or (at your option) any later
version of the license.


## References

* [The Test Anything Protocol v14 specification](https://testanything.org/tap-version-14-specification.html)
* [The RPM Package Manager](https://github.com/rpm-software-management/rpm)
* [IMA Wiki](https://sourceforge.net/p/linux-ima/wiki/Home/)
* [rpmlint](https://github.com/rpm-software-management/rpmlint) - 
  a tool for checking common errors in RPM packages.
* [rpminspect](https://github.com/rpminspect/rpminspect) - 
  an RPM build deviation analysis tool.