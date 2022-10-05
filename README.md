# Scverse Ecosystem Packages

This repository contains a list of approved software that works together with
scverse core packages and are listed on our website. The goal is to increase
visibility of ecosystem packages and make it easier for users to find
appropriate software.

**Hint:** If you want to receive notifications about new ecosystem packages, simply
use GitHub's "watch" functionality for this repository.

## What are the requirements for an ecosystem package?

For a package to be approved as ecosystem package we expect certain minimum
requirements, in particular:

-   The package can be installed from a standard registry (e.g. PyPI or
    conda-forge)
-   The package uses automated software tests and continuous integration
-   The package provides API documentation
-   The package uses scverse datastructures where appropriate (i.e.
    anndata/mudata and their modality-specific extensions)

There are additional requirements which we strongly recommend, but do not
enforce:

-   The package should provide tutorials (or "vignettes") as part of the
    documentation.
-   The package uses our [cookiecutter
    template](https://github.com/scverse/cookiecutter-scverse).

Note that the ecosystem packages are not necessarily constrained to Python
software, as long as they fulfil the above requirements.

If you cannot or do not want to comply with these requirements, you are still
free to use be interoperable with scverse packages by using our datastructures,
but we will not list your package on our ecosystem page.

## How can my package become part of the list?

Submit a pull-request adding your package to the `packages.yml` file. The
pull-request template will guide you. You will be asked to answer a short
questionnaire which our core team will usually review within a week.
