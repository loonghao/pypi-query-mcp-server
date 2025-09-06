# Transitive Dependency Enhancement

## Overview

This enhancement adds comprehensive transitive dependency analysis to the PyPI Query MCP Server. The `get_package_dependencies` tool now supports analyzing the complete dependency tree of a package with advanced features for handling complex dependency scenarios.

## New Features

### 1. Transitive Dependency Resolution
- **Parameter**: `include_transitive: bool = False`
- **Description**: When set to `True`, recursively resolves all dependencies of dependencies
- **Default**: `False` (maintains backward compatibility)

### 2. Depth Control
- **Parameter**: `max_depth: int = 5`
- **Description**: Limits the maximum recursion depth to prevent excessive analysis
- **Default**: 5 levels deep

### 3. Python Version Filtering
- **Parameter**: `python_version: str | None = None`
- **Description**: Filters dependencies based on target Python version compatibility
- **Example**: `"3.10"`, `"3.11"`

## Enhanced Response Format

When `include_transitive=True`, the response includes:

### Basic Information (Same as before)
```json
{
  "package_name": "requests",
  "version": "2.31.0",
  "requires_python": ">=3.7",
  "include_transitive": true,
  "max_depth": 5,
  "python_version": "3.10",
  "runtime_dependencies": ["urllib3>=1.21.1", "certifi>=2017.4.17"],
  "development_dependencies": [],
  "optional_dependencies": {}
}
```

### Transitive Dependencies Analysis
```json
{
  "transitive_dependencies": {
    "dependency_tree": {
      "package_name": "requests",
      "version": "2.31.0",
      "depth": 0,
      "children": {
        "urllib3": {
          "package_name": "urllib3",
          "version": "2.0.4",
          "depth": 1,
          "children": {}
        }
      }
    },
    "all_packages": {
      "requests": {
        "name": "requests",
        "version": "2.31.0",
        "depth": 0,
        "dependency_count": {
          "runtime": 3,
          "development": 0,
          "total_extras": 0
        }
      }
    },
    "circular_dependencies": [],
    "depth_analysis": {
      "max_depth": 2,
      "depth_distribution": {"0": 1, "1": 3, "2": 1},
      "average_depth": 1.2,
      "shallow_deps": 3,
      "deep_deps": 1,
      "leaf_packages": ["certifi", "charset-normalizer"]
    }
  }
}
```

### Enhanced Summary Statistics
```json
{
  "dependency_summary": {
    "direct_runtime_count": 3,
    "direct_dev_count": 0,
    "direct_optional_groups": 0,
    "total_transitive_packages": 8,
    "total_runtime_dependencies": 15,
    "max_dependency_depth": 3,
    "complexity_score": {
      "score": 25.4,
      "level": "moderate",
      "recommendation": "Moderate complexity, manageable with proper tooling",
      "factors": {
        "total_packages": 9,
        "max_depth": 3,
        "total_dependencies": 15
      }
    }
  }
}
```

### Analysis and Health Metrics
```json
{
  "analysis": {
    "resolution_stats": {
      "total_packages": 9,
      "total_runtime_dependencies": 15,
      "max_depth": 3
    },
    "potential_conflicts": [
      {
        "package": "urllib3",
        "conflicting_constraints": [
          {"constraint": "urllib3>=1.21.1", "required_by": "requests"},
          {"constraint": "urllib3>=2.0.0", "required_by": "another-package"}
        ],
        "severity": "potential"
      }
    ],
    "maintenance_concerns": {
      "total_packages": 9,
      "packages_without_version_info": 0,
      "high_dependency_packages": [
        {"name": "requests", "dependency_count": 8}
      ],
      "maintenance_risk_score": {
        "score": 12.5,
        "level": "low"
      }
    },
    "performance_impact": {
      "estimated_install_time_seconds": 33,
      "estimated_memory_footprint_mb": 105,
      "performance_level": "good",
      "recommendations": [],
      "metrics": {
        "package_count_impact": "low",
        "depth_impact": "low",
        "resolution_complexity": "simple"
      }
    }
  }
}
```

## Advanced Features

### 1. Circular Dependency Detection
- Automatically detects and reports circular dependencies
- Prevents infinite loops during resolution
- Provides detailed cycle information including:
  - Cycle path
  - Cycle length
  - Packages involved

### 2. Performance Safeguards
- **Maximum depth limits**: Prevents excessive recursion
- **Visited package tracking**: Avoids re-processing packages
- **Memory-efficient caching**: Reduces redundant API calls
- **Timeout handling**: Graceful degradation for large trees

### 3. Complexity Analysis
- **Complexity scoring**: Numerical assessment of dependency complexity
- **Performance impact estimation**: Rough estimates for installation time and memory usage
- **Maintenance risk assessment**: Identifies potential maintenance concerns
- **Recommendations**: Actionable advice based on analysis

## Usage Examples

### Basic Direct Dependencies (Existing Functionality)
```python
# MCP tool call
result = await get_package_dependencies("requests")
# Returns only direct dependencies
```

### Transitive Dependencies with Default Settings
```python
# MCP tool call
result = await get_package_dependencies(
    package_name="requests",
    include_transitive=True
)
# Returns complete dependency tree with default depth=5
```

### Advanced Transitive Analysis
```python
# MCP tool call
result = await get_package_dependencies(
    package_name="django",
    include_transitive=True,
    max_depth=3,
    python_version="3.11"
)
# Returns filtered dependency tree for Python 3.11 with max depth 3
```

### Testing with Complex Packages
```python
# Test with packages known for complex dependencies
packages_to_test = [
    "tensorflow",  # Machine learning - many dependencies
    "django",      # Web framework - moderate complexity
    "requests",    # HTTP library - simple but popular
    "fastapi",     # Modern web framework
    "pandas",      # Data analysis - scientific dependencies
]

for package in packages_to_test:
    result = await get_package_dependencies(
        package_name=package,
        include_transitive=True,
        max_depth=4,
        python_version="3.10"
    )
    print(f"{package}: {result['dependency_summary']['total_transitive_packages']} packages")
```

## Error Handling

The implementation includes comprehensive error handling for:

### 1. Circular Dependencies
- **Detection**: Automatically detected during tree traversal
- **Prevention**: Visited package tracking prevents infinite loops
- **Reporting**: Detailed cycle information in response

### 2. Missing Packages
- **Graceful degradation**: Continues analysis even if some packages aren't found
- **Logging**: Warnings for missing packages
- **Partial results**: Returns analysis for available packages

### 3. Network Errors
- **Retry logic**: Built into the underlying PyPI client
- **Timeout handling**: Prevents hanging on slow responses
- **Error propagation**: Clear error messages for debugging

### 4. Depth Limits
- **Automatic limiting**: Respects max_depth parameter
- **Performance protection**: Prevents excessive API calls
- **Progress tracking**: Depth information in results

## Performance Considerations

### 1. API Usage
- **Caching**: Reduces redundant PyPI API calls
- **Batch processing**: Efficient handling of multiple dependencies
- **Rate limiting**: Respects PyPI rate limits

### 2. Memory Usage
- **Streaming processing**: Processes dependencies as they're resolved
- **Memory-efficient data structures**: Optimized for large dependency trees
- **Garbage collection**: Proper cleanup of intermediate data

### 3. Time Complexity
- **Exponential growth**: Dependency trees can grow exponentially
- **Depth limits**: max_depth prevents runaway analysis
- **Early termination**: Stops on circular dependencies

## Testing Recommendations

### 1. Test with Various Package Types
```python
test_cases = [
    {"package": "six", "expected_complexity": "low"},       # Simple, no deps
    {"package": "requests", "expected_complexity": "low"},  # Few deps
    {"package": "django", "expected_complexity": "moderate"}, # Moderate deps
    {"package": "tensorflow", "expected_complexity": "high"}, # Many deps
]
```

### 2. Test Edge Cases
- Packages with circular dependencies
- Packages with very deep dependency trees
- Packages with conflicting version constraints
- Packages with optional dependencies

### 3. Performance Testing
- Measure response times for different max_depth values
- Test memory usage with large dependency trees
- Validate timeout handling

## Integration Notes

### 1. Backward Compatibility
- Default `include_transitive=False` maintains existing behavior
- All existing response fields preserved
- No breaking changes to existing functionality

### 2. MCP Tool Interface
The enhanced tool maintains the same interface pattern:
```json
{
  "name": "get_package_dependencies",
  "parameters": {
    "package_name": "string (required)",
    "version": "string (optional)",
    "include_transitive": "boolean (optional, default: false)",
    "max_depth": "integer (optional, default: 5)",
    "python_version": "string (optional)"
  }
}
```

### 3. Logging
Enhanced logging provides insights into:
- Dependency resolution progress
- Performance metrics
- Error conditions
- Cache hit/miss ratios

## Future Enhancements

### Potential improvements for future versions:
1. **Dependency conflict resolution**: Automatic suggestion of compatible versions
2. **Security vulnerability scanning**: Integration with security databases
3. **License compatibility checking**: Analysis of license conflicts
4. **Performance benchmarking**: Real-world performance data
5. **Visual dependency graphs**: Export to graph formats
6. **Dependency update planning**: Automated update recommendations

## Conclusion

The transitive dependency enhancement provides comprehensive dependency analysis while maintaining backward compatibility and performance. It enables users to understand the full impact of package dependencies, identify potential issues, and make informed decisions about package usage.