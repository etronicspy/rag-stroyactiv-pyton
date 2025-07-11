# Project Architecture

## Overview
This document describes the high-level architecture of the RAG Construction Materials API project.

## Core Components
- **API Routes**: Defined in `api/routes/`.
- **Services**: Business logic in `services/`.
- **Core**: Configurations, databases, logging in `core/`.

## Parser Integration
The parser module will be integrated into `core/parsers/` to handle AI-powered material parsing. This includes dependency injection with main config, logging, and validation. See PARSER_MODULE_INTEGRATION_PLAN_V2.md for details. 