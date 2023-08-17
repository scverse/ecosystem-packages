# Scverse Ecosystem Packages

This repository contains the list of scverse ecosystem packages that are displayed on scverse.org.
The goal is to increase visibility of ecosystem packages and make it easier for users to find appropriate software.
Registered ecosystem packages can also get their own tag to use on the [scverse forum](https://discourse.scverse.org) for user discussion.
Authors of these packages can be added the [scverse github organization](https://github.com/scverse).
In the future, we may also test releases of core packages against the test suites of ecosystem packages.

If a package is part of this list, it means it fulfills certain minimum requirements as outlined below.
It **does not** imply endorsement or that an in-depth review has been performed.

**Hint:** If you want to receive notifications about new ecosystem packages, simply use GitHub's "watch" functionality for this repository.

## How can my package become part of the list?

Submit a pull-request adding a `meta.yaml` file for your package to the `packages` directory.

-   Please refer to other entries for examples
-   The full definition of available fields is available in [`schema.json`](schema.json)
-   Please copy the checklist from below into the pull request description and answer all questions.

## What are the requirements for an ecosystem package?

For a package to become an approved ecosystem package, it must fulfill all mandatory requirements from the checklist below.

Ecosystem packages can be written in non-Python languages as long as they fulfill the above requirements.

If you cannot or do not want to comply with these requirements, you are still free to make your package interoperable with scverse by using our datastructures, but we will not list your package on our ecosystem page.

## Checklist for adding packages

### Mandatory

Name of the tool: XXX

Short description: XXX

How does the package use scverse data structures (please describe in a few sentences): XXX

-   [ ] The code is publicly available under an [OSI-approved](https://opensource.org/licenses/alphabetical) license
-   [ ] The package provides versioned releases
-   [ ] The package can be installed from a standard registry (e.g. PyPI, conda-forge, bioconda)
-   [ ] The package uses automated software tests and runs them via continuous integration (CI)
-   [ ] The package provides API documentation via a website or README
-   [ ] The package uses scverse datastructures where appropriate (i.e. AnnData, MuData or SpatialData and their modality-specific extensions)
-   [ ] I am an author or maintainer of the tool and agree on listing the package on the scverse website

### Recommended

-   [ ] Please announce this package on scverse communication channels (zulip, discourse, twitter)
-   [ ] Please tag the author(s) these announcements. Handles (e.g. `@scverse_team`) to include are:
    -   Twitter:
    -   Zulip:
    -   Discourse:
    -   Mastodon:
-   [ ] The package provides tutorials (or "vignettes") that help getting users started quickly
-   [ ] The package uses the [scverse cookiecutter template](https://github.com/scverse/cookiecutter-scverse).
