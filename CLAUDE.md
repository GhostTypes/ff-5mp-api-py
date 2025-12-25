# Claude Development Notes

## PyPI Publishing

### Configuration Files
- `.pypirc` - Contains PyPI authentication token for publishing packages
  - Location: Project root directory
  - Status: Git-ignored (not tracked in version control)
  - Contains username and API token for automated PyPI uploads
  - Note: This file exists locally but won't be visible in git status

### Publishing to PyPI
To publish a new version:

1. Update version in `pyproject.toml`
2. Clean previous builds: `rm -rf dist/ build/ *.egg-info`
3. Build: `python -m build`
4. Upload: `python -m twine upload dist/*`
   - Credentials will be read automatically from `.pypirc`

### Package Info
- Package name: `flashforge-python-api`
- PyPI URL: https://pypi.org/project/flashforge-python-api/
- Build system: Hatchling
- Current version: 1.0.0
