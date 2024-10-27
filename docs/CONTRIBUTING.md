# Contributing

### **Table of Contents**

- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Standards and Guidelines](#standards-and-guidelines)

## Getting Started

Before contributing, it's wise to consult someone on the Kusogaki team (either through the discord server or as an issue on the PR).

## How to Contribute

Thanks in advance for helping out on the project!

Please refer to [CONTRIBUTING_DEV.md](./CONTRIBUTING_DEV.md) for making code changes that affect functionality.

## Standards and Guidelines

### Pull Request Naming Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for our pull request titles (and commit messages on the master branch). Please follow the guidelines below when naming pull requests.

For types, we use the following:

- `build`: Changes that affect the build system or external dependencies
- `chore`: Other changes that don't apply to any of the above
- `ci`: Changes to our CI configuration files
- `docs`: Documentation only changes
- `feat`: A new feature
- `fix`: A bug fix
- `perf`: A code change that improves performance
- `refactor`: A code change that neither fixes a bug nor adds a feature, but makes the code easier to read, understand, or improve
- `revert`: Reverts a previous commit
- `style`: Changes that do not affect the meaning of the code (white space, formatting, etc.)
- `test`: Adding missing tests or correcting existing tests

### Pull Request General Guidelines

- **Smaller is better**. Submit **one** pull request per bug fix or feature. A pull request should contain isolated changes pertaining to a single bug fix or feature implementation. **Do not** refactor or reformat code that is unrelated to your change. Very large pull requests will take enormous amounts of time to review, or may be rejected altogether.

- **Prioritize understanding over cleverness**. Please write code that is easily readible and understandable. Remember that source code usually gets written once and read often.

- **Follow existing coding style and conventions**. In order to prevent confusion, keep your code consistent with the style, formatting, and conventions in the rest of the code base. Consistency makes it easier to review and modify in the future.

- **Include test coverage**. Add unit tests or update existing unit tests when possible. Follow existing patterns for implementing tests.

- **Add documentation**. Document your changes with code when applicable.

- **Resolve any merge conflicts** that may occur.

- **Promptly address any CI failures**. If your pull request fails to build or pass tests, please push another commit to fix it.

- **When writing comments**, use properly constructred sentences, including punctuation.

### Writing Commit Messages

Writing good commit messages is very important in order to keep track of what each commit is contributing to the project. As we use these commits to make releases, it's vital we keep track of what changes contributed to the new release.

- Each commit needs to include a commit type provided above.
- The subject should be separate from the body with a blank line.
- Limit the subject line to 50 characters.
- Don't end the subject line with a period.
- Use the body to explain why, not what and how (when applicable).

**Example commit message**: `docs: fix typo in README introduction section`