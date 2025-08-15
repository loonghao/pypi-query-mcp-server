# Fix for include_extras Parameter Validation Issue

## Summary

Fixed a critical issue where the `include_extras` parameter in the `resolve_dependencies` tool was not working correctly due to incorrect Python version filtering that was removing extra dependencies from consideration.

## Root Cause Analysis

The issue was in the `_is_requirement_applicable` method in `pypi_query_mcp/core/dependency_parser.py`. When filtering requirements by Python version, the method was evaluating markers like `extra == "socks"` in an environment that didn't include the `extra` variable, causing these requirements to be filtered out incorrectly.

### The Problem

1. **Python version filtering was too aggressive**: The `filter_requirements_by_python_version` method was filtering out ALL requirements with markers that couldn't be evaluated, including extra requirements.

2. **Marker evaluation environment was incomplete**: When evaluating markers like `extra == "socks"`, the environment didn't include the `extra` variable, so the evaluation always returned `False`.

3. **Incorrect filtering logic**: Extra dependencies should not be filtered by Python version at all - they should be handled separately based on user selection.

### Before the Fix

```python
# In _is_requirement_applicable method
def _is_requirement_applicable(self, req: Requirement, python_version: Version) -> bool:
    if not req.marker:
        return True

    env = {
        "python_version": str(python_version),
        # ... other environment variables
    }
    
    try:
        return req.marker.evaluate(env)  # This returns False for extra == "socks"
    except Exception as e:
        logger.warning(f"Failed to evaluate marker for {req}: {e}")
        return True
```

**Result**: Requirements like `PySocks!=1.5.7,>=1.5.6; extra == "socks"` were filtered out because `extra == "socks"` evaluated to `False` in an environment without the `extra` variable.

## The Fix

Added a check to exclude extra requirements from Python version filtering:

```python
def _is_requirement_applicable(self, req: Requirement, python_version: Version) -> bool:
    if not req.marker:
        return True

    # If the marker contains 'extra ==', this is an extra dependency
    # and should not be filtered by Python version. Extra dependencies
    # are handled separately based on user selection.
    marker_str = str(req.marker)
    if "extra ==" in marker_str:
        return True

    # Rest of the method unchanged...
```

### Why This Fix Works

1. **Preserves extra requirements**: Extra dependencies are no longer filtered out by Python version filtering
2. **Maintains correct Python version filtering**: Non-extra requirements are still properly filtered by Python version
3. **Separates concerns**: Extra handling is kept separate from Python version filtering, as it should be
4. **Backwards compatible**: Doesn't break existing functionality

## Testing Results

### Before the Fix
```python
# Example: requests[socks] with Python 3.10
result = await resolve_package_dependencies("requests", include_extras=["socks"], python_version="3.10")
print(result["summary"]["total_extra_dependencies"])  # Output: 0 ❌
```

### After the Fix
```python
# Example: requests[socks] with Python 3.10  
result = await resolve_package_dependencies("requests", include_extras=["socks"], python_version="3.10")
print(result["summary"]["total_extra_dependencies"])  # Output: 1 ✅
print(result["dependency_tree"]["requests"]["dependencies"]["extras"])
# Output: {'socks': ['PySocks!=1.5.7,>=1.5.6; extra == "socks"']} ✅
```

## Examples of Correct Usage

### Basic Examples

```python
# Requests with SOCKS proxy support
await resolve_package_dependencies("requests", include_extras=["socks"])

# Django with password hashing extras
await resolve_package_dependencies("django", include_extras=["argon2", "bcrypt"])

# Setuptools with testing tools
await resolve_package_dependencies("setuptools", include_extras=["test"])

# Flask with async and dotenv support
await resolve_package_dependencies("flask", include_extras=["async", "dotenv"])
```

### How to Find Available Extras

1. **Check the package's PyPI page** - Look for available extras in the description
2. **Use the `provides_extra` field** - Available in package metadata
3. **Check package documentation** - Often lists available extras
4. **Look for requirements with `extra ==`** - In the `requires_dist` field

### Common Mistakes to Avoid

❌ **Wrong**: Using generic extra names
```python
# These don't exist for requests
await resolve_package_dependencies("requests", include_extras=["dev", "test"])
```

✅ **Right**: Using package-specific extra names
```python
# These are actual extras for requests
await resolve_package_dependencies("requests", include_extras=["socks", "use-chardet-on-py3"])
```

## Files Modified

1. **`pypi_query_mcp/core/dependency_parser.py`**: Fixed `_is_requirement_applicable` method
2. **`pypi_query_mcp/server.py`**: Updated documentation for `include_extras` parameter
3. **`pypi_query_mcp/tools/dependency_resolver.py`**: Updated docstring for `include_extras` parameter
4. **`tests/test_dependency_resolver.py`**: Added comprehensive test cases
5. **`examples/extras_usage_demo.py`**: Added demonstration of correct usage

## Validation

The fix has been validated with:

- ✅ Real PyPI packages (requests, django, setuptools, flask)
- ✅ Various extra combinations
- ✅ Python version filtering still works for non-extra requirements  
- ✅ Transitive dependency resolution with extras
- ✅ Edge cases (non-existent extras, extras with no dependencies)
- ✅ Backwards compatibility with existing code

## Performance Impact

- **Minimal**: Only adds a simple string check for `"extra =="` in markers
- **Positive**: Reduces unnecessary marker evaluations for extra requirements
- **No regression**: All existing functionality continues to work as before

## Conclusion

This fix resolves the core issue with `include_extras` parameter validation while maintaining all existing functionality. Users can now successfully resolve optional dependencies using the correct extra names as defined by each package.