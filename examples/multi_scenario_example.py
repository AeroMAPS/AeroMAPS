"""
Example script demonstrating multi-scenario comparison.

This script shows how to use the MultiProcess class to compare
multiple AeroMAPS scenarios with built-in comparison plots.
"""

from aeromaps import create_process, create_multi_process


def main():
    """Run example multi-scenario comparison."""
    
    print("=" * 60)
    print("AeroMAPS Multi-Scenario Comparison Example")
    print("=" * 60)
    
    # Create and compute multiple scenarios
    print("\n1. Creating and computing scenarios...")
    
    # For demonstration, we'll use the same config but could be different
    scenarios = {}
    
    print("   - Creating scenario 1...")
    proc1 = create_process()
    proc1.compute()
    scenarios["Baseline"] = proc1
    
    print("   - Creating scenario 2...")
    proc2 = create_process()
    proc2.compute()
    scenarios["Alternative"] = proc2
    
    print(f"   ✓ Created {len(scenarios)} scenarios")
    
    # Create multi-process manager
    print("\n2. Creating multi-process manager...")
    multi = create_multi_process(scenarios)
    print(f"   ✓ Managing {len(multi)} scenarios: {multi.get_scenario_names()}")
    
    # List available plots
    print("\n3. Available comparison plots:")
    plots = multi.list_available_plots()
    for plot_name in plots:
        print(f"   - {plot_name}")
    
    # Create comparison plots
    print("\n4. Creating comparison plots...")
    
    # CO2 emissions comparison
    print("   - Creating CO2 emissions comparison...")
    try:
        fig1 = multi.plot("co2_emissions_comparison", save=False)
        print("     ✓ CO2 emissions comparison created")
    except Exception as e:
        print(f"     ✗ Could not create plot: {e}")
    
    # Energy consumption comparison
    print("   - Creating energy consumption comparison...")
    try:
        fig2 = multi.plot("energy_consumption_comparison", save=False)
        print("     ✓ Energy consumption comparison created")
    except Exception as e:
        print(f"     ✗ Could not create plot: {e}")
    
    # Energy mix comparison
    print("   - Creating energy mix comparison...")
    try:
        fig3 = multi.plot("energy_mix_comparison", save=False)
        print("     ✓ Energy mix comparison created")
    except Exception as e:
        print(f"     ✗ Could not create plot: {e}")
    
    print("\n" + "=" * 60)
    print("Multi-scenario comparison complete!")
    print("=" * 60)
    
    # Example of handling scenarios with missing outputs
    print("\nNote: If scenarios have different models/outputs, the")
    print("MultiProcess will automatically:")
    print("  1. Check which scenarios have required outputs")
    print("  2. Show warnings for scenarios with missing data")
    print("  3. Create plots with only valid scenarios")


if __name__ == "__main__":
    main()
