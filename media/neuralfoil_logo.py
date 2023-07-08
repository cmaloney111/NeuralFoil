import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import aerosandbox.tools.pretty_plots as p
from matplotlib.colors import LinearSegmentedColormap

fig = plt.figure(figsize=(6, 3))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis('off')

##### Draw the NN
n_nodes_per_side = 20
n_nodes = 2 * n_nodes_per_side
n_layers = 10
n_neighbors_to_connect = 2

cmap = LinearSegmentedColormap.from_list("custom_cmap", ["crimson", "dodgerblue"])

af = asb.Airfoil("dae11").repanel(n_nodes_per_side)

### Compute where the Neural Network nodes should be drawn, and the directions to propagate them in
nodes_start = np.concatenate([
    af.upper_coordinates()[::-1],
    af.lower_coordinates()[::-1]
], axis=0)
nodes_start_tangent_direction = np.roll(nodes_start, -1, axis=0) - np.roll(nodes_start, 1, axis=0)
nodes_start_normal = (np.rotation_matrix_2D(np.pi / 2) @ (nodes_start_tangent_direction.T)).T
nodes_start_direction = nodes_start_normal / np.linalg.norm(nodes_start_normal, axis=1).reshape(-1, 1)
nodes_start_direction[0] = np.array([-1, 0])
nodes_start_direction[-1] = np.array([-1, 0])

theta_deg = np.linspace(30, -30, n_nodes)

nodes_end = np.stack([
    1 + 1 * np.cosd(theta_deg),
    0 + 1 * np.sind(theta_deg)
], axis=1)
nodes_end_direction = np.stack([
    np.ones(n_nodes),
    np.zeros(n_nodes)
], axis=1)

from scipy import interpolate

xs = nodes_start[:, 0].reshape(-1, 1)
nodes_start_direction = 1. * nodes_start_direction * (1 - xs ** 8)# + (1 - xs) ** 2)

nodes_interpolator = interpolate.CubicSpline(
    x=[0, 1],
    y=np.stack([nodes_start, nodes_end], axis=0),
    axis=0,
    bc_type=(
        (1, nodes_start_direction),
        (2, np.zeros_like(nodes_end))
        # (1, nodes_end_direction * 2)
    )
)

all_nodes = nodes_interpolator(np.arange(n_layers + 1) / n_layers)

layer_colors = cmap(np.linspace(0, 1, n_layers + 1))

for i, (layer_nodes, layer_color) in enumerate(zip(all_nodes, layer_colors)):

    # Plot this layer's nodes
    x = layer_nodes[:, 0]  # The x-coordinates of the nodes in this layer
    y = layer_nodes[:, 1]  # The y-coordinates of the nodes in this layer
    ax.plot(
        x,
        y,
        ".",
        alpha=0.6,
        color=layer_color,
        markeredgecolor="white",
        markeredgewidth=0.5
    )

    # Connect this layer's nodes
    layer_nodes_for_ring = interpolate.CubicSpline(
        x=np.linspace(0, 1, len(layer_nodes)),
        y=layer_nodes,
        axis=0,
    )(np.linspace(0, 1, 500))

    ax.plot(
        layer_nodes_for_ring[:, 0],
        layer_nodes_for_ring[:, 1],
        color=layer_color,
        linewidth=1,
        alpha=0.4 if i != 0 else 1
    )
    # if i == 0:
    #     plt.fill(x, y, color="white", zorder=2.5)

    # Plot connections to the next layer, if applicable
    if i != len(all_nodes) - 1:
        xn = all_nodes[i + 1][:, 0]  # The x-coordinates of the nodes in the (n)ext layer
        yn = all_nodes[i + 1][:, 1]  # The y-coordinates of the nodes in the (n)ext layer

        for neighbor_offset in range(-n_neighbors_to_connect, n_neighbors_to_connect + 1):

            def roll_truncate(x, n):
                if n == 0:
                    return x
                elif n > 0:
                    return x[n:]
                else:
                    return x[:n]


            ax.plot(
                np.stack([roll_truncate(x, -neighbor_offset), roll_truncate(xn, neighbor_offset)]),
                np.stack([roll_truncate(y, -neighbor_offset), roll_truncate(yn, neighbor_offset)]),
                color=layer_color,
                linewidth=0.5,
                alpha=0.5
            )

text_kwargs = dict(
    fontsize=48,
    fontname="Raleway",
)

x_offset = -0.15
y_offset = -0.04

plt.text(
    x_offset, y_offset, "Neural", ha="right", va="bottom",
    color=p.adjust_lightness(colors[0], 0.75), **text_kwargs
)
plt.text(
    x_offset, y_offset, "Foil", ha="right", va="top",
    color=p.adjust_lightness(colors[1], 0.75), **text_kwargs
)

plt.gca().set_aspect("equal", adjustable='box')
plt.xlim(-1.35, 2.1)

plt.show()
