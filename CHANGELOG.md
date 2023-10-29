# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Add a configuration file example to the README.

### Fixed

- Make the "package.tags" section optional in a configuration file.


## [0.0.3] - 2023-10-29

### Added

- Implement IMA signatures inspector.
- Implement tests skipping in the TAP reporter.
- Exit with a non-zero exit code if some tests failed.
- Use pytest-compatible exit codes.

### Fixed

- Skip PGP signature tests instead of failing if PGP key id is not specified in
  a configuration file.
- Remove second "Inspector" word from the inspector class names.


## [0.0.2] - 2023-10-28

### Added

- Add subtests support to the TAP reporter.
- Use a tested RPM file base name as a main test description and use subtests
  for individual inspections.
- Add license information and TAP/RPM references to the README file.


## [0.0.1] - 2023-10-28

### Added

- Implement the initial project architecture. 
- Add [TAP](https://testanything.org/) format output support.
- Add an RPM package signature inspection.
- Add a very basic PRM package tags inspection.
