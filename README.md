# Scverse Ecosystem Packages

This repository contains a list of approved software that works together with
scverse core packages and are listed on our website. The goal is to increase
visibility of ecosystem packages and make it easier for users to find
appropriate software. In the future, we may also test releases of core packages against
the test suites of ecosystem packages.

If a package is part of this list, it means it fulfils certain minimum requirements
as outlined below. It **does not** mean we endorse the package or performed an in-depth
review.

**Hint:** If you want to receive notifications about new ecosystem packages, simply
use GitHub's "watch" functionality for this repository.

## How can my package become part of the list?

Submit a pull-request adding a `meta.yaml` file for your package to the `packages` directory.

-   Please refer to other entries for examples
-   The full definition of available fields is available in [`schema.json`](schema.json)
-   Please copy the checklist from below into the pull request description and answer all questions.

## What are the requirements for an ecosystem package?

For a package to become an approved ecosystem package, it must fulfill all mandatory requirements from the checklist
below.

Ecosystem packages can be written in non-Python languages as long as they fulfill the above requirements.

If you cannot or do not want to comply with these requirements, you are still
free to make your package interoperable with scverse by using our datastructures,
but we will not list your package on our ecosystem page.

## Checklist for adding packages

### Mandatory

Name of the tool: XXX

Short description: XXX

How does the package use scverse data structures (please describe in a few sentences): XXX

-   [ ] The code is publicly available under an OSI-approved license
-   [ ] The package provides versioned releases
-   [ ] The package can be installed from a standard registry (e.g. PyPI or conda-forge)
-   [ ] The package uses automated software tests and continuous integration
-   [ ] The package provides API documentation
-   [ ] The README/documentation provides a statement what level of support users can expect
-   [ ] The package uses scverse datastructures where appropriate (i.e.anndata/mudata and their modality-specific extensions)
-   [ ] I am the author or maintainer of the tool and agree on listing the package on the scverse website

### Recommended

-   [ ] The package provides tutorials (or "vignettes") that help getting users started quickly
-   [ ] The package uses the [scverse cookiecutter template](https://github.com/scverse/cookiecutter-scverse).
