# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-02

### Added
- Initial release with project-based workflow
- CA, server, and client certificate generation
- Batch certificate generation from CSV
- Real-time activity log
- Recent projects management
- Professional menu bar (Archivo, Opciones, Ayuda)
- Immutable CA per project (created at project creation)
- Certificate log viewer with export functionality
- Semantic versioning (SEMVER) implementation

### Changed
- Complete codebase restructure (core/, ui/, utils/)
- Separated business logic from UI layer
- Fixed critical bug: folder paths now persist after Browse selection

### Fixed
- UI bug where StringVar was not updating after folder selection
- CA immutability enforcement at project level

### Deprecated
- None

### Removed
- None

### Security
- Private keys (*_key.pem) properly ignored in .gitignore
- CA validation before allowing certificate generation