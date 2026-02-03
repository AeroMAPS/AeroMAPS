# Process and Pathways Manager Fixes

## Overview

This document describes the critical fixes made to resolve fundamental issues in the plot inheritance structure, specifically around `self.process` access and `pathways_manager` availability.

## Issues Identified

### Issue 1: self.process Not Stored

**Problem:**
The parent class `SingleScenarioPlot` was not storing a reference to the process object. However, many plot subclasses were trying to access `self.process.pathways_manager`, which caused AttributeError.

**Root Cause:**
In `SingleScenarioPlot.__init__()`, the process was used to extract data but never stored:

```python
# OLD CODE (BROKEN)
def __init__(self, process, figsize=None, ...):
    # Extract data from process
    self._extract_data(process.data)  # Uses process but doesn't store it
    
    # ... rest of initialization
    self.create_plot()  # Subclass may try to access self.process
```

When subclasses tried to use `self.process.pathways_manager` in their `create_plot()` or other methods, it failed because `self.process` was never set.

### Issue 2: pathways_manager Not Always Present

**Problem:**
The `pathways_manager` attribute was only created when energy models were configured. If a process didn't have energy models, accessing `process.pathways_manager` would raise AttributeError.

**Root Cause:**
In `AeroMAPSProcess`, the `pathways_manager` was only created in `_initialize_generic_energy()` (line 1042):

```python
def _initialize_generic_energy(self):
    # Only called if energy models are configured
    self.pathways_manager = EnergyCarrierManager()
    # ...
```

This method is only called in `setup_mda()` and only if energy configuration exists. For processes without energy models, `pathways_manager` would not exist at all.

## Solutions Implemented

### Solution 1: Store Process Reference in SingleScenarioPlot

**File:** `aeromaps/plots/single_scenario_plot.py`

Added `self.process = process` at the start of `__init__()`:

```python
# NEW CODE (FIXED)
def __init__(self, process, figsize=None, check_outputs=True, required_outputs=None, **kwargs):
    """Initialize the plot with data from a process."""
    
    # Store the process object for access by subclasses
    self.process = process
    
    # Set instance-level required_outputs
    if required_outputs is not None:
        self.required_outputs = required_outputs
    else:
        self.required_outputs = self.__class__.required_outputs.copy() if self.__class__.required_outputs else []
    
    # Validate required outputs if requested
    if check_outputs and self.required_outputs:
        self._validate_required_outputs(process.data)
    
    # Extract data from process
    self._extract_data(process.data)
    
    # ... rest of initialization
```

**Key Points:**
- `self.process = process` is set FIRST, before any other operations
- This makes the process available to all methods in subclasses
- Subclasses can access `self.process.pathways_manager`, `self.process.data`, etc.

### Solution 2: Initialize pathways_manager in Process

**File:** `aeromaps/core/process.py`

Added `self.pathways_manager = None` at the start of `__init__()`:

```python
# NEW CODE (FIXED)
def __init__(self, configuration_file=None, custom_models=None, optimisation=False):
    """Initialize an AeroMAPSProcess instance."""
    
    # Initialize pathways_manager to None - will be populated if energy models are used
    self.pathways_manager = None
    
    self.configuration_file = (
        os.path.abspath(os.fspath(configuration_file))
        if configuration_file is not None
        else None
    )
    self._initialize_configuration()
    
    # ... rest of initialization
```

**Key Points:**
- `pathways_manager` is initialized to `None` at the start
- The attribute always exists, preventing AttributeError
- If energy models are configured, it will be replaced with an `EnergyCarrierManager` instance
- If not configured, it remains `None`

## Impact and Benefits

### For Plot Classes

**Before:**
```python
class MyPlot(SingleScenarioPlot):
    def create_plot(self):
        # This would fail with AttributeError: 'MyPlot' object has no attribute 'process'
        manager = self.process.pathways_manager
```

**After:**
```python
class MyPlot(SingleScenarioPlot):
    def create_plot(self):
        # This works! self.process is stored by parent class
        if self.process.pathways_manager is not None:
            manager = self.process.pathways_manager
            # Use manager safely
        else:
            # Handle case where energy models not configured
            pass
```

### Benefits

1. **No More AttributeError:**
   - `self.process` always exists in plot classes
   - `process.pathways_manager` always exists (may be None)

2. **Consistent Access Pattern:**
   - All plots can access process attributes via `self.process`
   - Standard defensive pattern: check if not None before use

3. **Better Encapsulation:**
   - Process object fully accessible to plots
   - Can access any process attribute or method

4. **Backward Compatible:**
   - Existing plots that don't use these features continue to work
   - No breaking changes to the API

## Usage Patterns

### Safe Access to pathways_manager

```python
class MyEnergyPlot(SingleScenarioPlot):
    def create_plot(self):
        # Defensive check
        if self.process.pathways_manager is not None:
            # Energy models are configured
            pathways = self.process.pathways_manager.get_all()
            for pathway in pathways:
                # Plot pathway data
                pass
        else:
            # Energy models not configured
            # Fall back to alternative or skip
            pass
```

### Access Other Process Attributes

```python
class MyPlot(SingleScenarioPlot):
    def create_plot(self):
        # Access any process attribute
        models = self.process.models
        config = self.process.configuration_file
        parameters = self.process.parameters
        
        # Use in plotting logic
```

### No Need to Store Separately

```python
# BEFORE (Old pattern - DON'T USE)
class OldPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        super().__init__(process, figsize)
        self.pathways_manager = self.process.pathways_manager  # Redundant!

# AFTER (New pattern - CORRECT)
class NewPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        super().__init__(process, figsize)
        # No need to store separately, just use self.process.pathways_manager
    
    def create_plot(self):
        if self.process.pathways_manager is not None:
            # Access directly
            manager = self.process.pathways_manager
```

## Migration Guide

For existing plot classes that were trying to use `self.process` or `self.pathways_manager`:

1. **Remove any manual storage of pathways_manager:**
   ```python
   # Remove this line from __init__:
   self.pathways_manager = self.process.pathways_manager
   ```

2. **Access via self.process instead:**
   ```python
   # Change from:
   manager = self.pathways_manager
   
   # To:
   if self.process.pathways_manager is not None:
       manager = self.process.pathways_manager
   ```

3. **Add defensive checks where appropriate:**
   ```python
   # Before using pathways_manager
   if self.process.pathways_manager is not None:
       # Safe to use
   ```

## Testing

The fixes ensure that:
- ✅ All plot classes can instantiate without AttributeError
- ✅ Plots work whether or not energy models are configured
- ✅ Existing plots remain functional
- ✅ New plots can safely access process attributes

## Summary

These two simple changes fix fundamental issues in the plot inheritance structure:

1. **SingleScenarioPlot stores `self.process`** - Enables all plots to access process
2. **Process initializes `pathways_manager` to None** - Prevents AttributeError

The result is a robust, consistent system where plots can safely access process attributes and handle cases where optional features (like energy models) may not be configured.
