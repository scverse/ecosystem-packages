# Scverse Ecosystem Packages

This repository contains the list of scverse ecosystem packages that are displayed on scverse.org and are part of
the scverse® project.
The goal is to increase visibility of ecosystem packages and make it easier for users to find appropriate software.
Registered ecosystem packages can also get their own tag to use on the [scverse forum](https://discourse.scverse.org) for user discussion.
Authors of these packages can be added to the [scverse github organization](https://github.com/scverse).
In the future, we may also test releases of core packages against the test suites of ecosystem packages.

If a package is part of this list, it means it fulfills certain minimum requirements as outlined below.
It **does not** imply endorsement or that an in-depth review has been performed.

**Hint:** If you want to receive notifications about new ecosystem packages, simply use GitHub's "watch" functionality for this repository.

## How can my package become part of the list?

Submit a pull-request adding a `meta.yaml` file for your package to the `packages` directory.

- Please copy the checklist from below into the pull request description and answer all questions.
- Please refer to other entries for examples
- The full definition of available fields is available in [`schema.json`](scripts/src/ecosystem_scripts/schema.json)
- You can add a logo in svg/png/webp format if you like. Currently it is not used on our website, though.
- Please set `topics` from the controlled vocabulary below, in addition to free-form `tags`

## Topics and tags

Packages carry two kinds of keywords, and they do different jobs.

`topics` say what a package is **for**. They come from a controlled vocabulary, are validated
against [`schema.json`](scripts/src/ecosystem_scripts/schema.json), and drive the filters on
[scverse.org/packages](https://scverse.org/packages/#ecosystem). Pick every topic that genuinely
applies, usually one to three. If none of them fit your package, propose a new one in your pull
request rather than forcing a bad match.

| Topic                   | For packages that …                                                        |
| ----------------------- | -------------------------------------------------------------------------- |
| `annotation`            | assign cell type or state labels, or transfer them from a reference        |
| `cell-communication`    | infer ligand–receptor interactions and cell–cell signalling                |
| `clustering`            | group cells, spots or genes into populations or domains                    |
| `deconvolution`         | estimate cell type composition of mixed or bulk measurements               |
| `differential-analysis` | test for differential expression or abundance, or score gene sets          |
| `epigenomics`           | work with chromatin accessibility, methylation or related modalities       |
| `gene-networks`         | infer regulatory networks, co-expression or gene programs                  |
| `imaging`               | work with histology, microscopy or whole-slide images                      |
| `immune`                | analyse immune receptor repertoires or are otherwise immunology-specific   |
| `infrastructure`        | provide data structures, file formats, I/O or tooling rather than analysis |
| `integration`           | correct batch effects, map to references, or join datasets and modalities  |
| `multi-omics`           | jointly analyse two or more molecular modalities                           |
| `perturbation`          | analyse CRISPR screens, drug response or other perturbation experiments    |
| `preprocessing`         | do quality control, filtering, normalisation or denoising                  |
| `proteomics`            | work with mass spectrometry, cytometry or other protein measurements       |
| `spatial`               | work with spatially resolved measurements                                  |
| `trajectory`            | infer pseudotime, RNA velocity, lineage or cell fate                       |
| `visualization`         | provide plotting, interactive exploration or data browsers                 |

`tags` stay free-form and are only used for search, so they do not need to match anyone else's
spelling. Use them for anything the topics are too coarse to express — an assay, a method, a
platform, a dependency.

## What are the requirements for an ecosystem package?

For a package to become an approved ecosystem package, it must fulfill all mandatory requirements from the checklist below.

Ecosystem packages can be written in non-Python languages as long as they fulfill the above requirements.

If you cannot or do not want to comply with these requirements, you are still free to make your package interoperable with scverse by using our datastructures, but we will not list your package on our ecosystem page.

## Checklist for adding packages

### Mandatory

Name of the tool: XXX

Short description: XXX

How does the package use scverse data structures (please describe in a few sentences): XXX

- [ ] The code is publicly available under an [OSI-approved](https://opensource.org/licenses/alphabetical) license
- [ ] The package provides versioned releases
- [ ] The package can be installed from a standard registry (e.g. PyPI, conda-forge, bioconda)
- [ ] Automated tests cover essential functions of the package and a reasonable range of inputs and conditions [^1]
- [ ] Continuous integration (CI) automatically executes these tests on each push or pull request [^2]
- [ ] The package provides API documentation via a website or README[^3]
- [ ] The package uses scverse datastructures where appropriate (i.e. AnnData, MuData or SpatialData and their modality-specific extensions)
- [ ] The `topics` field is set from the controlled vocabulary documented above
- [ ] I am an author or maintainer of the tool and agree on listing the package on the scverse website

### Recommended

- [ ] Please announce this package on scverse communication channels (zulip, discourse, twitter)
- [ ] Please tag the author(s) these announcements. Handles (e.g. `@scverse_team`) to include are:
    - Zulip:
    - Discourse:
    - Mastodon:
    - Bluesky:
    - Twitter:

- [ ] The package provides tutorials (or "vignettes") that help getting users started quickly
- [ ] The package uses the [scverse cookiecutter template](https://github.com/scverse/cookiecutter-scverse).

[^1]: We recommend thtat tests cover at least all user facing (public) functions. Minimal tests ensure that the function does not fail on an example data set. Ideally, tests also ensure the correctness of the results, e.g. by comparing against a snapshot.

[^2]: Continuous integration means that software tests are automatically executed on every push to the git repository. This guarantees they are always run and that they are run in a clean environment. Scverse ecosystem packages most commonly use [GitHub Actions](https://github.com/features/actions) for CI. For an example, check out our [cookiecutter template](https://github.com/scverse/cookiecutter-scverse).

[^3]: By API documentation, we mean an overview of _all_ public functions provided a package, with documentation of their parameters. For an example, see the [Scanpy documentation](https://scanpy.readthedocs.io/page/api/preprocessing.html). In simple cases, this can be done manually in a README file. For anything more complex, we recommend the [Sphinx Autodoc plugin](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)
