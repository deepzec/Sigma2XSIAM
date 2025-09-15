# Sigma2XSIAM

## Overview

Sigma2XSIAM is a custom pySigma backend designed to convert Sigma security rules into Cortex XSIAM XQL (Extended Query Language) queries. The project addresses limitations of the standard `pysigma-backend-cortexxdr` by providing accurate syntax handling, proper field mapping to Cortex Extended Data Model (XDM), and advanced modifier support for XSIAM's specific requirements.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Custom Backend Implementation**: Built as a standalone Python backend extending `TextQueryBackend` from pySigma
- **Modular Design**: Organized in `cortex/backends/` directory structure following Python package conventions
- **Processing Pipeline**: Uses YAML-based configuration (`pipelines/cortex_xdm.yml`) for field mapping and rule transformation

### Core Components
- **CortexXSIAMBackend Class**: Main conversion engine handling Sigma rule parsing and XQL query generation
- **Field Mapping System**: Transforms generic Sigma fields to Cortex XDM schema fields
- **Operator Translation**: Converts Sigma operators (`contains`, `startswith`, `endswith`) to XSIAM-specific XQL syntax
- **Modifier Processing**: Handles complex Sigma modifiers like `contains|all` with proper AND-based logic

### Query Generation
- **Precedence Handling**: Implements proper operator precedence for NOT, AND, OR conditions
- **String Handling**: Custom quoting and escaping mechanisms for XQL compatibility
- **Wildcard Support**: Translates Sigma wildcards to XQL pattern matching
- **Regular Expression**: Converts regex patterns using XQL's `~=` operator

### Processing Pipeline
- **YAML Configuration**: Externalized field mapping rules for maintainability
- **Rule Validation**: Checks for required files and proper rule structure
- **Error Handling**: Comprehensive error reporting for missing dependencies and malformed rules

## External Dependencies

### Core Dependencies
- **pySigma (>=0.1.20)**: Primary Sigma rule processing framework
- **PyYAML (>=6.0)**: YAML configuration file parsing
- **requests**: HTTP client library for external integrations

### Development Tools
- **defusedxml**: Secure XML parsing for coverage reporting
- **Virtual Environment**: Recommended Python environment isolation

### Target Platform
- **Cortex XSIAM**: Primary target platform for generated XQL queries
- **Cortex Extended Data Model (XDM)**: Field schema standard for mapping