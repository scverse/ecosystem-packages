# Reviewer guide

The purpose of this document is to describe how to review ecosystem packages.

Users add pull requests to request to be added to the scverse ecosystem package listing.
To be added, the the packages must fulfil the criteria listed in the ecosystems-package [README](https://github.com/scverse/ecosystem-packages#checklist-for-adding-packages).
Users are asked as part of their PR to add the checklist to the main PR comment and to fill it faithfully.
Your job as reviewer is to assess if the all checklist criteria are fulfilled.
Additionally, in case you notice anything else that could be improved (technically, or scientifically)
you can point that out during the review, but highlight that this is independnet of the criteria required
for package approval.

Check the [package schema](https://github.com/scverse/ecosystem-packages/blob/main/scripts/src/ecosystem_scripts/schema.json) for additional context.

## 1. Check if the checklist exists and is the same as the original one in the README

Some users modify the checklist or leave out points or do not provide any checklist at all.
All "mandatory" points from the original checklist must be fulfilled.

## 2. Check the license

- license declared in the meta.yaml matches the license in the repo `LICENSE` file and in metadata fields of the package (e.g. pyproject.toml).
- A `LICENSE` file is mandatory
- license is indeed OSI-approved

## 3. Check releases

- releases are available on PyPI or any other approved registry.
- The repo makes use of github releases, or at least uses git tags that are consistent with the releases on the registry.

## 4. Automated tests

- Check the source code of the package if automated tests cover essential functions of the package and a reasonable range of inputs and conditions.
- At least all user-facing (public) functions should be covered by tests, but there can be exceptions, e.g. if a function is trivial or there are good reasons why it can't be tested automatically (e.g. slow and doesn't work with toy data)
- Minimal tests ensure that the function does not fail on an example data set. Ideally, tests also ensure the correctness of the results, e.g. by comparing against a snapshot. Provide feedback on how good the test quality is.

## 5. Continuous integration

- Check the repo that CI scripts exist that execute the automated tests from (4).
- Check that the CI checks are actually executed (on commits to main and PRs)
- Typically, this is done in github actions, but other CI systems are allowed, too.

## 6. API docs

- API documentation must exist. API documentation is an overview of all public functions provided by the package with a documentation of their parameters.
- Typically this is done via sphinx-autodocs, but it is ok to have it in a README or any other documentation system, as long as it's comprehensive.

## 7. data structures

- The package must be interoperable with other scverse packages by using its data structures
- AnnData for unimodal omics data
- MuData for multimodal omics data
- SpatialData for spatially resolved omics data.

## 8. author approval

- The author must have ticked the checkbox "I am an author or maintainer of the tool and agree on listing the package on the scverse website"
