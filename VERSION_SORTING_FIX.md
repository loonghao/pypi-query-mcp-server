# Semantic Version Sorting Fix

## Problem Description

The `get_package_versions` tool was using basic string sorting for package versions instead of semantic version sorting. This caused incorrect ordering where pre-release versions (like `5.2rc1`) appeared before stable versions (like `5.2.5`) when they should come after.

### Specific Issue
- **Problem**: `"5.2rc1"` was appearing before `"5.2.5"` in version lists
- **Root Cause**: Using `sorted(releases.keys(), reverse=True)` performs lexicographic string sorting
- **Impact**: Misleading version order in package version queries

## Solution Implemented

### 1. Added Semantic Version Sorting Function

**File**: `/pypi_query_mcp/core/version_utils.py`

```python
def sort_versions_semantically(versions: list[str], reverse: bool = True) -> list[str]:
    """Sort package versions using semantic version ordering.
    
    This function properly sorts versions by parsing them as semantic versions,
    ensuring that pre-release versions (alpha, beta, rc) are ordered correctly
    relative to stable releases.
    """
```

**Key Features**:
- Uses the `packaging.version.Version` class for proper semantic parsing
- Handles pre-release versions correctly (alpha < beta < rc < stable)
- Gracefully handles invalid versions by falling back to string sorting
- Maintains original version strings in output
- Comprehensive logging for debugging

### 2. Updated Package Query Functions

**File**: `/pypi_query_mcp/tools/package_query.py`

**Changes Made**:
1. **Import**: Added `from ..core.version_utils import sort_versions_semantically`
2. **format_version_info()**: Replaced basic sorting with semantic sorting
3. **format_package_info()**: Updated available_versions to use semantic sorting

**Before**:
```python
# Sort versions (basic sorting, could be improved with proper version parsing)
sorted_versions = sorted(releases.keys(), reverse=True)
```

**After**:
```python
# Sort versions using semantic version ordering
sorted_versions = sort_versions_semantically(list(releases.keys()), reverse=True)
```

## Test Results

### 1. Unit Tests - Semantic Version Sorting

```
Test 1 - Pre-release ordering:
  Input:  ['5.2rc1', '5.2.5', '5.2.0', '5.2a1', '5.2b1']
  Output: ['5.2.5', '5.2.0', '5.2rc1', '5.2b1', '5.2a1']
  ✅ PASS: Correct pre-release ordering
```

### 2. Task Requirement Validation

```
Task requirement validation:
  Input: ['5.2rc1', '5.2.5']
  Output: ['5.2.5', '5.2rc1']
  Requirement: '5.2rc1' should come after '5.2.5'
  ✅ PASS: Requirement met!
```

### 3. Pre-release Ordering Validation

```
Pre-release ordering validation:
  Input: ['1.0.0', '1.0.0rc1', '1.0.0b1', '1.0.0a1']
  Output: ['1.0.0', '1.0.0rc1', '1.0.0b1', '1.0.0a1']
  Expected order: stable > rc > beta > alpha
  ✅ PASS: Pre-release ordering correct!
```

### 4. Real Package Testing

**Django** (complex versioning with pre-releases):
```
Recent versions: ['5.2.5', '5.2.4', '5.2.3', '5.2.2', '5.2.1', '5.2', '5.2rc1', '5.2b1', '5.2a1', '5.1.11']
String-sorted:   ['5.2rc1', '5.2b1', '5.2a1', '5.2.5', '5.2.4', '5.2.3', '5.2.2', '5.2.1', '5.2', '5.1.9']
✅ Semantic sorting correctly places stable versions before pre-releases
```

**NumPy** (simple versioning):
```
Recent versions: ['2.3.2', '2.3.1', '2.3.0', '2.2.6', '2.2.5', '2.2.4', '2.2.3', '2.2.2', '2.2.1', '2.2.0']
✅ Both sorting methods produce identical results (as expected for simple versions)
```

### 5. Edge Cases Testing

**Complex versions with dev, post, and invalid versions**:
```
Input:  ['1.0.0', '1.0.0.post1', '1.0.0.dev0', '1.0.0a1', '1.0.0b1', '1.0.0rc1', '1.0.1', 'invalid-version', '1.0']
Output: ['1.0.1', '1.0.0.post1', '1.0.0', '1.0', '1.0.0rc1', '1.0.0b1', '1.0.0a1', '1.0.0.dev0', 'invalid-version']
✅ Handles all edge cases correctly
```

### 6. Regression Testing

```bash
poetry run python -m pytest tests/ -v
============================= test session starts ==============================
64 passed in 9.25s
✅ All existing tests continue to pass
```

## Implementation Details

### Semantic Version Ordering Rules

1. **Stable versions** come before **pre-release versions** of the same base version
2. **Pre-release ordering**: `alpha < beta < rc < stable`
3. **Development versions** (`dev`) come before **alpha versions**
4. **Post-release versions** (`post`) come after **stable versions**
5. **Invalid versions** are sorted lexicographically and placed after valid versions

### Error Handling

- Invalid version strings are gracefully handled
- Falls back to string sorting for unparseable versions
- Logs warnings for invalid versions (debug level)
- Maintains all original version strings in output

### Performance Considerations

- Minimal performance impact (parsing is fast)
- Uses efficient sorting algorithms
- Caches parsed versions during single sort operation
- No breaking changes to existing API

## Verification Commands

```bash
# Run standalone semantic version tests
python test_version_sorting_standalone.py

# Test with real PyPI packages
poetry run python test_real_packages.py

# Test specific task requirement
poetry run python test_specific_case.py

# Run full test suite
poetry run python -m pytest tests/ -v
```

## Files Modified

1. **`/pypi_query_mcp/core/version_utils.py`**: Added `sort_versions_semantically()` function
2. **`/pypi_query_mcp/tools/package_query.py`**: Updated to use semantic version sorting

## Dependencies

- Uses existing `packaging` library (already a dependency in `pyproject.toml`)
- No new dependencies added
- Compatible with Python 3.10+

## Conclusion

The semantic version sorting fix successfully resolves the issue where pre-release versions were incorrectly appearing before stable versions. The implementation:

- ✅ Fixes the specific problem mentioned (`5.2rc1` vs `5.2.5`)
- ✅ Handles all pre-release types correctly (alpha, beta, rc)
- ✅ Manages edge cases (dev, post, invalid versions)
- ✅ Maintains backward compatibility
- ✅ Passes all existing tests
- ✅ Uses robust, industry-standard version parsing

The fix provides accurate, intuitive version ordering that matches user expectations and semantic versioning standards.