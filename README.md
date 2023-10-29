# rpmqc

The RPM packages quality control tool.

Ideologically, rpmqc is similar to [rpmlint](https://github.com/rpm-software-management/rpmlint),
but they solve slightly different tasks: rpmlint is an awesome tool for checking
an RPM package for common errors (a packager's tool), while rpmqc is designed
to quickly check an entire repository/compose for typical release manager's
errors like missing signatures or wrong branding.


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