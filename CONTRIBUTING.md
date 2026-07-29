# Contributing to EDSPiKE AI Model

## Branch Strategy

```
Prod (production) ← Staging ← your fork/branch
```

- **`Prod`** — production-ready code. Protected. Only accepts PRs from `Staging` after review and approval by `@hayfordafriyie`.
- **`Staging`** — integration branch. Anyone can open a PR here. Changes are tested and reviewed before merging.

## How to Contribute

1. **Fork** the repo on GitHub.
2. **Clone** your fork and create a feature branch from `Staging`:
   ```bash
   git clone https://github.com/YOUR_USERNAME/EDSPiKE-AI-Model.git
   git checkout -b feature/your-feature origin/Staging
   ```
3. **Make your changes** and commit:
   ```bash
   git add .
   git commit -m "Description of your change"
   ```
4. **Push** to your fork:
   ```bash
   git push origin feature/your-feature
   ```
5. **Open a Pull Request** targeting `Staging` on GitHub.
   - Write a clear title and description.
   - Reference any related issues.

## Review Process

1. Your PR will be reviewed by maintainers.
2. Once approved, it merges into `Staging`.
3. After sufficient testing, `Staging` is merged into `Prod` via a separate PR that requires `@hayfordafriyie` approval.

## Guidelines

- Keep PRs focused — one feature/fix per PR.
- Add tests for new functionality.
- Follow existing code style (no extra comments, concise code).
- Do not include `.env` files, secrets, or large binary files.
- Large model files (>100MB) must use Git LFS.

## Need Help?

Open an issue or start a discussion on GitHub.
