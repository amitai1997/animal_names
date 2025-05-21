# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fixed parsing of collateral adjectives separated by `<br>` tags in the Wikipedia table. Now properly handles cases like "caudatan<br>salamandrine" for Salamander animals by treating `<br>` tags as separators similar to commas and semicolons.
