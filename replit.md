# Overview

Sigma2XSIAM is a custom pySigma backend designed to convert Sigma rules into accurate Cortex XSIAM XQL queries. The project addresses limitations in the standard `pysigma-backend-cortexxdr` by providing proper handling of XSIAM-specific syntax, Cortex Extended Data Model (XDM) field mappings, and complex Sigma modifiers. The system focuses on generating clean, readable XQL queries that are ready for use in the XSIAM console.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
The project implements a custom pySigma backend through the `CortexXSIAMBackend` class, which handles the core conversion logic from Sigma rules to XQL queries. The backend is structured as a Python package under the `cortex.backends` module, allowing for modular organization and easy integration with the pySigma framework.

## Processing Pipeline
The system uses a YAML-based processing pipeline (`cortex_xdm.yml`) that defines field mappings between generic Sigma fields and the official Cortex Extended Data Model schema. This pipeline-driven approach allows for flexible configuration and easy maintenance of field translations without modifying core backend code.

## Rule Processing Workflow
The conversion process follows a structured workflow:
1. Load Sigma rules from YAML files
2. Apply the custom processing pipeline for field mapping
3. Process rules through the custom backend for XQL conversion
4. Output formatted, console-ready queries

## Modular Design
The codebase follows a modular structure with separate concerns:
- Backend implementation in dedicated module (`cortex/backends/`)
- Processing pipeline configuration in external YAML files
- Conversion scripts as standalone utilities
- Package structure supporting editable installation for development

## Error Handling and Validation
The system includes robust error handling with file existence checks, import validation, and graceful fallback mechanisms for different pySigma API versions.

# External Dependencies

## Core Framework
- **pySigma**: Primary framework for Sigma rule processing and backend development (>=0.1.20)
- **PyYAML**: YAML parsing and processing for configuration files and rule definitions (>=6.0)

## Target Platform Integration
- **Cortex XSIAM**: Target platform for generated XQL queries
- **Cortex Extended Data Model (XDM)**: Schema standard for field mappings and data structure alignment

## Development Dependencies
The project supports plugin-based installation through the SigmaPluginDirectory system, allowing integration with the broader pySigma ecosystem while maintaining independence as a custom backend solution.