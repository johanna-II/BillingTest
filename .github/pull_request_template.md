# PR Checklist

## Changes

- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring
- [ ] Documentation update
- [ ] Test addition/modification

### Testing

- [ ] Ran tests locally (`python run_tests.py --mode fast`)
- [ ] Added new tests (if applicable)
- [ ] All existing tests pass

### Impact Scope

- [ ] `libs/` - Core logic
- [ ] `tests/` - Test code
- [ ] `mock_server/` - Mock server
- [ ] Configuration files (`.yml`, `.toml`)

### CI Optimization Hints

```yaml
# Use these keywords in PR description to change CI behavior
[skip ci] - Skip CI completely
[fast test] - Run fast tests only
[full test] - Run full test suite
```

### Description
<!-- Brief description of changes -->

### Related Issues
<!-- fixes #123 -->
