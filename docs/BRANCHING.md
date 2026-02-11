# Branching Strategy

To maintain a stable production environment and facilitate collaborative development, we use the following branching strategy:

## Core Branches

### `main`
- **Purpose**: Production-ready code only.
- **Rules**: 
  - No direct commits. 
  - All changes must come via a Pull Request from `develop`.
  - Must always be in a deployable state.

### `develop`
- **Purpose**: Integration branch for features.
- **Rules**:
  - The main branch for development.
  - Features are merged here after review and testing.

## Supporting Branches

### `feature/*`
- **Purpose**: Development of new features (e.g., `feature/ml-optimization`).
- **Base Branch**: `develop`
- **Merge Back To**: `develop` via Pull Request.

### `bugfix/*`
- **Purpose**: Fixing bugs found in `develop`.
- **Base Branch**: `develop`
- **Merge Back To**: `develop`.

### `hotfix/*`
- **Purpose**: Critical fixes for the `main` branch.
- **Base Branch**: `main`
- **Merge Back To**: `main` and `develop`.

## Workflow
1. Create a branch from `develop`.
2. Commit changes.
3. Push branch to GitHub.
4. Open a Pull Request to `develop`.
5. Once approved and tested, merge into `develop`.
6. Periodically merge `develop` into `main` for release.
