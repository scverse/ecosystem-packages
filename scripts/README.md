# Scripts

To hack on the scripts:

- Use `prek/pre-commit run -a jsonschema-gentypes` to generate types from schema initially
- Use `prek/pre-commit install` so checks are automatically run on commit

To e.g. run registry validation locally, call `validate-registry`, e.g. like this:

```shell
env "GITHUB_TOKEN=$(gh auth token)" hatch run validate-registry
```
