"""
Plots for life cycle assessments interpretation
"""

from pyvis.network import Network
import os
from IPython.display import display, IFrame
from lca_algebraic.activity import Activity

# from aeromaps.models.impacts.life_cycle_assessment.helpers import list_processes
from lca_modeller.helpers import list_processes
import matplotlib
import matplotlib.pyplot as plt

USER_DB = "Foreground DB"
default_process_tree_filename = "process_tree.html"


def process_tree(
    model: Activity,
    foreground_only: bool = True,
    outfile: str = default_process_tree_filename,
    colormap: str = "Pastel2",
):
    """
    Plots an interactive tree to visualize the activities and exchanges declared in the LCA module.
    :param model: The model containing activities and exchanges.
    :param foreground_only: Boolean flag to include only foreground activities.
    :param outfile: Output filename for the generated tree.
    :param colormap: Colormap to use for node coloring.
    """
    # Init network
    net = Network(
        notebook=True, directed=True, layout=True, cdn_resources="remote", filter_menu=False
    )

    # Get processes hierarchy
    df = list_processes(model, foreground_only)
    df["description"] = df["activity"] + "\n" + df["unit"].fillna("")

    # Colors
    unique_values = df["database"].unique()
    value_indices = {value: i for i, value in enumerate(unique_values)}
    norm = matplotlib.colors.Normalize(vmin=0, vmax=len(unique_values), clip=True)
    mapper = plt.cm.ScalarMappable(norm=norm, cmap=plt.get_cmap(colormap))
    colors = df["database"].apply(
        lambda x: matplotlib.colors.to_hex(mapper.to_rgba(value_indices[x]))
    )

    # Populate network
    edge_data = zip(
        df["activity"],
        df["description"],
        df["parents"],
        df["amounts"],
        df["level"],
        df["database"],
        colors,
    )

    edges = {}
    for activity, description, parents, amounts, level, database, color in edge_data:
        src = activity if database == USER_DB else f"{activity}\n[{database}]"
        # desc_array = description.split(',')
        # desc_db = description.split('(')
        # desc = ',\n'.join(desc_array[:2]) if len(desc_array) > 1 else desc_array[0]
        # desc += f"\n({desc_db[-1]}" if len(desc_db) > 1 else ''
        desc = description

        net.add_node(src, desc, title=src, level=level + 1, shape="box", color=color)

        for parent, amount in zip(parents, amounts):
            if parent:
                edge_key = (src, parent)
                if edge_key in edges:  # Multiple edges between the same nodes
                    edges[edge_key].append(str(amount))
                else:  # first time edge links act and its parent: create new node for parent
                    edges[edge_key] = [str(amount)]

    # Add edges to the network with unique labels
    for (src, dst), labels in edges.items():
        if len(labels) == 1:
            net.add_edge(src, dst, label=labels[0], title=f"Exch. 1: {labels[0]}")
        else:
            num_edges = len(labels)
            roundness_step = 0.1 / num_edges  # Adjust the denominator to control spacing
            for i, label in enumerate(labels):
                curve_type = "curvedCW" if i % 2 == 0 else "curvedCCW"
                roundness = roundness_step * (
                    i + 1
                )  # Adjust roundness to avoid excessive curvature
                net.add_edge(
                    src,
                    dst,
                    label=label,
                    title=f"Exch. {i + 1}: {label}",
                    smooth={"enabled": True, "type": curve_type, "roundness": roundness},
                )

    # Set options
    net.set_edge_smooth("vertical")
    net.toggle_physics(False)
    net.show_buttons(filter_=True)
    net.options.layout.hierarchical.nodeSpacing = 200

    # Save
    net.save_graph(outfile)

    # Display in Jupyter Notebook
    display(IFrame(src=os.path.relpath(outfile), width="100%", height=700))
