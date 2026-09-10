# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-10

### Added

- **Dark Mode / Light Mode**: Toggle between dark and light themes in Global Settings
- **Certificate Export Formats**: Support for PEM and DER formats (.pem, .cer, .crt)
- **Enhanced Batch CSV Format**: Full certificate parameters per row with validation
  - Format: `cert_name;Country;State/Province;Locality;Organization;CN;SAN;Validity days;key size`
  - Validation before processing with detailed error messages
  - Invalid rows are skipped with warnings
- **Output Path Management**: Display and change certificate output paths
  - Path shown in Label with Browse button
  - Path persisted in project configuration
- **Internationalization (i18n)**: Multi-language support
  - English and Spanish translations
  - Easy to add more languages
  - Translation files in `locales/` folder
- **Global Settings Dialog**: Centralized configuration
  - Theme selection (Light/Dark)
  - Language selection
  - Default export format


### Changed

- **batch_generator.py**: Complete rewrite for v0.2.0 CSV format
  - New validation system with detailed error reporting
  - Support for per-certificate parameters
  - Better error handling
- **config.py**: Extended with global settings
  - Added `theme`, `language`, `default_export_format` keys
  - Helper functions for accessing settings
- **menu_bar.py**: Enabled Global Settings menu item
- **Code organization**: Better separation of concerns
  - `utils/i18n.py` - Translation system
  - `utils/cert_export.py` - Export format utilities
  - `ui/settings_dialog.py` - Settings UI

### Fixed

- Version number corrected from v1.0.0 to v0.1.1 (typo fix)
- Improved error messages in batch generation
- Better validation feedback for users

### Deprecated

- None

### Removed

- None

### Security

- Private keys always exported as PEM (never DER) for security
- Validation prevents creation of certificates with invalid parameters

## [0.1.1] - 2026-09-09

### Fixed

- Documentation updates
- Minor bug fixes

## [0.1.0] - 2026-09-02

### Added

- Initial release with project-based workflow
- CA, server, and client certificate generation
- Batch certificate generation from CSV
- Real-time activity log
- Recent projects management
- Professional menu bar (Files, Options, Help)
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

### Security

- Private keys (`*_key.pem`) properly ignored in `.gitignore`
- CA validation before allowing certificate generation
