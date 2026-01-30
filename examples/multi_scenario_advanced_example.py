"""
Advanced example demonstrating multi-scenario comparison with grouping.

This example shows how to:
1. Create and compute multiple scenarios
2. Use scenario grouping for visual organization
3. Override required_outputs at instance level
4. Programmatically create groups
"""

from aeromaps import create_process, create_multi_process


def example_1_basic_grouping():
    """Example 1: Basic scenario grouping."""
    print("=" * 60)
    print("Example 1: Basic Scenario Grouping")
    print("=" * 60)
    
    # Create scenarios with temporal variations
    print("\nCreating 6 scenarios (2 pathways x 3 time periods)...")
    
    multi = create_multi_process({
        "Baseline_2030": create_process(),
        "Baseline_2040": create_process(),
        "Baseline_2050": create_process(),
        "Optimistic_2030": create_process(),
        "Optimistic_2040": create_process(),
        "Optimistic_2050": create_process(),
    })
    
    # Compute all at once
    print("Computing all scenarios...")
    multi.compute_all()
    
    # Define groups - scenarios in same group share color
    scenario_groups = {
        "Baseline Pathway": [
            "Baseline_2030",
            "Baseline_2040",
            "Baseline_2050"
        ],
        "Optimistic Pathway": [
            "Optimistic_2030",
            "Optimistic_2040",
            "Optimistic_2050"
        ]
    }
    
    print("\nScenario grouping:")
    print("  Group 'Baseline Pathway' - same color, 3 line styles")
    print("  Group 'Optimistic Pathway' - same color, 3 line styles")
    
    # Create plots with grouping
    print("\nCreating grouped comparison plots...")
    multi.plot("co2_emissions_comparison", scenario_groups=scenario_groups)
    multi.plot("energy_mix_comparison", scenario_groups=scenario_groups)
    
    print("✓ Plots created with scenario grouping")


def example_2_technology_comparison():
    """Example 2: Technology pathways with sensitivity."""
    print("\n" + "=" * 60)
    print("Example 2: Technology Comparison with Cost Sensitivity")
    print("=" * 60)
    
    # Create scenarios for different technologies and cost assumptions
    print("\nCreating 9 scenarios (3 technologies x 3 cost levels)...")
    
    multi = create_multi_process({
        "Biofuel_Low": create_process(),
        "Biofuel_Mid": create_process(),
        "Biofuel_High": create_process(),
        "Hydrogen_Low": create_process(),
        "Hydrogen_Mid": create_process(),
        "Hydrogen_High": create_process(),
        "Electric_Low": create_process(),
        "Electric_Mid": create_process(),
        "Electric_High": create_process(),
    })
    
    print("Computing all scenarios...")
    multi.compute_all()
    
    # Group by technology
    tech_groups = {
        "Biofuel": ["Biofuel_Low", "Biofuel_Mid", "Biofuel_High"],
        "Hydrogen": ["Hydrogen_Low", "Hydrogen_Mid", "Hydrogen_High"],
        "Electric": ["Electric_Low", "Electric_Mid", "Electric_High"]
    }
    
    print("\nTechnology grouping:")
    print("  Each technology = 1 color")
    print("  Cost levels (Low/Mid/High) = different line styles")
    
    # Create comparison plots
    print("\nCreating technology comparison plots...")
    multi.plot("energy_consumption_comparison", scenario_groups=tech_groups)
    multi.plot("biofuel_production_comparison", scenario_groups=tech_groups)
    
    print("✓ Technology comparison plots created")


def example_3_required_outputs_override():
    """Example 3: Override required_outputs."""
    print("\n" + "=" * 60)
    print("Example 3: Override required_outputs at Instance Level")
    print("=" * 60)
    
    from aeromaps.plots.multi_scenario.emissions import CO2EmissionsComparisonPlot
    
    # Create simple scenarios
    multi = create_multi_process({
        "Scenario_A": create_process(),
        "Scenario_B": create_process()
    })
    multi.compute_all()
    
    # Check class default
    print(f"\nClass default: {CO2EmissionsComparisonPlot.get_required_outputs()}")
    
    # Use class default
    print("\n1. Using class default required_outputs:")
    plot1 = CO2EmissionsComparisonPlot(multi.processes)
    print(f"   Instance uses: {plot1.get_instance_required_outputs()}")
    
    # Override at instance level
    print("\n2. Overriding required_outputs at instance level:")
    custom = ["co2_emissions", "contrails_emissions"]
    plot2 = CO2EmissionsComparisonPlot(
        multi.processes,
        required_outputs=custom,
        check_outputs=False  # Skip validation
    )
    print(f"   Instance uses: {plot2.get_instance_required_outputs()}")
    
    print("\n✓ Instance-level override demonstrated")


def example_4_programmatic_groups():
    """Example 4: Automatically create groups from naming."""
    print("\n" + "=" * 60)
    print("Example 4: Programmatic Group Creation")
    print("=" * 60)
    
    # Create scenarios with consistent naming
    scenarios = {
        "Policy_A_2030": create_process(),
        "Policy_A_2040": create_process(),
        "Policy_A_2050": create_process(),
        "Policy_B_2030": create_process(),
        "Policy_B_2040": create_process(),
        "Policy_B_2050": create_process(),
        "Policy_C_2030": create_process(),
        "Policy_C_2040": create_process(),
        "Policy_C_2050": create_process(),
    }
    
    print(f"\nCreated {len(scenarios)} scenarios")
    
    multi = create_multi_process(scenarios)
    multi.compute_all()
    
    # Automatically extract groups from names
    print("\nAutomatically creating groups from naming convention...")
    auto_groups = {}
    
    for scenario_name in multi.get_scenario_names():
        # Extract policy type (first part of name)
        policy = scenario_name.split('_')[0] + "_" + scenario_name.split('_')[1]
        group_name = f"Policy {policy.split('_')[1]}"
        
        if group_name not in auto_groups:
            auto_groups[group_name] = []
        auto_groups[group_name].append(scenario_name)
    
    print("\nGenerated groups:")
    for group_name, members in auto_groups.items():
        print(f"  {group_name}:")
        for member in members:
            print(f"    - {member}")
    
    # Use auto-generated groups
    print("\nCreating plots with auto-generated groups...")
    multi.plot("co2_emissions_comparison", scenario_groups=auto_groups)
    
    print("✓ Programmatic grouping demonstrated")


def example_5_mixed_grouping():
    """Example 5: Mixed grouped and ungrouped scenarios."""
    print("\n" + "=" * 60)
    print("Example 5: Mixed Grouping (Some Grouped, Some Independent)")
    print("=" * 60)
    
    # Create scenarios
    multi = create_multi_process({
        "Reference": create_process(),
        "Policy_Variant_A": create_process(),
        "Policy_Variant_B": create_process(),
        "Policy_Variant_C": create_process(),
        "Extreme_Case": create_process(),
    })
    
    multi.compute_all()
    
    # Group only the policy variants
    mixed_groups = {
        "Policy Variants": [
            "Policy_Variant_A",
            "Policy_Variant_B",
            "Policy_Variant_C"
        ]
        # "Reference" and "Extreme_Case" not in any group
    }
    
    print("\nGrouping structure:")
    print("  Group 'Policy Variants': 3 scenarios (same color)")
    print("  'Reference': independent (own color)")
    print("  'Extreme_Case': independent (own color)")
    
    # Create plot
    print("\nCreating plot with mixed grouping...")
    multi.plot("co2_emissions_comparison", scenario_groups=mixed_groups)
    
    print("✓ Mixed grouping demonstrated")


def example_6_saving_with_groups():
    """Example 6: Save plots with grouping."""
    print("\n" + "=" * 60)
    print("Example 6: Saving Plots with Scenario Grouping")
    print("=" * 60)
    
    # Create scenarios
    multi = create_multi_process({
        "Short_Term": create_process(),
        "Medium_Term": create_process(),
        "Long_Term": create_process(),
    })
    
    multi.compute_all()
    
    # Simple grouping
    groups = {
        "All Terms": ["Short_Term", "Medium_Term", "Long_Term"]
    }
    
    # Save with custom size
    print("\nSaving plot with scenario grouping...")
    multi.plot(
        "co2_emissions_comparison",
        scenario_groups=groups,
        save=True,
        size_inches=(14, 8)
    )
    
    print("✓ Saved as: co2_emissions_comparison.pdf")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" " * 15 + "AeroMAPS Advanced Multi-Scenario Examples")
    print("=" * 70)
    
    try:
        example_1_basic_grouping()
        example_2_technology_comparison()
        example_3_required_outputs_override()
        example_4_programmatic_groups()
        example_5_mixed_grouping()
        example_6_saving_with_groups()
        
        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)
        print("\nKey Features Demonstrated:")
        print("  ✓ Scenario grouping with coordinated colors/line styles")
        print("  ✓ Technology and policy pathway comparisons")
        print("  ✓ Instance-level required_outputs override")
        print("  ✓ Programmatic group creation")
        print("  ✓ Mixed grouped/ungrouped scenarios")
        print("  ✓ Saving plots with grouping")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
