"""GPSL v2.2 cipher-encoded Spatial payloads for Phase 2 operator-fluency experiment.

Each payload encodes a real spatial-reasoning task in GPSL notation alongside
an equivalent plain-English prompt.  The 20 payloads are ordered by operator
complexity so agents build fluency incrementally:

    1-6   : base operators only
    7-12  : base + ONE advanced operator  (adv-1)
    13-16 : base + TWO advanced operators (adv-2)
    17-20 : full operator set incl. Layer 4 modal / Layer 5 quantum
"""

from __future__ import annotations

from dataclasses import dataclass, field

from node_client.core.types import FrictionType, VerificationTier

from simulation.payloads.templates import SimPayload


@dataclass
class GpslPayload(SimPayload):
    """SimPayload extended with GPSL cipher metadata."""

    gpsl_cipher: str = ""
    operators_required: list[str] = field(default_factory=list)
    plain_prompt: str = ""


# ============================================================================
# Helper — shared defaults
# ============================================================================

_DOMAIN = FrictionType.SPATIAL
_TIER = VerificationTier.OPTIMISTIC_CONSENSUS


# ============================================================================
# Payloads 1-6: BASE OPERATORS ONLY
# ============================================================================

_p01 = GpslPayload(
    payload_id="gpsl_spatial_01_graph_shortest_path",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Correct shortest path is A->B->D->F with weight 9 "
        "(A-B:2, B-D:3, D-F:4). Alternative A->C->E->F = 2+5+3 = 10. "
        "Score 1.0 if correct path AND weight. 0.7 if correct weight, "
        "wrong path. 0.3 if reasonable attempt. 0.0 if completely wrong."
    ),
    difficulty=0.4,
    bounty=1.0,
    execution_window=120,
    gpsl_cipher=(
        "HEADER: Spatial / Graph Traversal\n"
        "PAYLOAD:\n"
        "  [A] → [B] : {w=2} ; [A] → [C] : {w=2}\n"
        "  [B] → [D] : {w=3} ; [B] → [C] : {w=4}\n"
        "  [C] → [E] : {w=5} ; [D] → [F] : {w=4}\n"
        "  [E] → [F] : {w=3} ; [D] → [E] : {w=1}\n"
        "  [Solver] → [A] → {shortest_to_F} = {path ⊕ weight}\n"
        "  <path|optimal> > 0.95"
    ),
    operators_required=["->", ":", ";", "=", "⊕"],
    plain_prompt=(
        "Given an undirected weighted graph with edges: "
        "A-B(2), A-C(2), B-D(3), B-C(4), C-E(5), D-F(4), E-F(3), D-E(1). "
        "Find the shortest path from A to F and its total weight. "
        "Show your reasoning step by step."
    ),
)

_p02 = GpslPayload(
    payload_id="gpsl_spatial_02_grid_placement",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Valid placement has 4 queens on a 4x4 grid with no two queens "
        "sharing a row, column, or diagonal. Two distinct solutions exist "
        "(up to reflection/rotation): (0,1)(1,3)(2,0)(3,2) and "
        "(0,2)(1,0)(2,3)(3,1). Score 1.0 if valid placement. "
        "0.5 if 3 of 4 non-attacking. 0.0 if invalid or wrong grid size."
    ),
    difficulty=0.5,
    bounty=1.0,
    execution_window=120,
    gpsl_cipher=(
        "HEADER: Spatial / Constraint Placement\n"
        "PAYLOAD:\n"
        "  [Q1] ⊕ [Q2] ⊕ [Q3] ⊕ [Q4] : {grid_4x4}\n"
        "  [Qi] ↛ [Qj] : {same_row} ; [Qi] ↛ [Qj] : {same_col}\n"
        "  [Qi] ↛ [Qj] : {same_diag}\n"
        "  [Placement] → {valid_config} = {coords}\n"
        "  <placement|constraints> > 0.95"
    ),
    operators_required=["⊕", "↛", ":", ";", "->", "="],
    plain_prompt=(
        "Place 4 non-attacking queens on a 4x4 chessboard. No two queens "
        "may share the same row, column, or diagonal. Return the solution "
        "as (row, col) coordinates using 0-indexed positions. Show your work."
    ),
)

_p03 = GpslPayload(
    payload_id="gpsl_spatial_03_triangle_area",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Using the shoelface formula: area = 0.5*|x1(y2-y3)+x2(y3-y1)+x3(y1-y2)| "
        "= 0.5*|1(7-2)+4(2-3)+6(3-7)| = 0.5*|4+(-4)+(-24)| = 0.5*24 = 12. "
        "Centroid = ((1+4+6)/3, (3+7+2)/3) = (11/3, 4) ~ (3.667, 4). "
        "Score 1.0 if both correct. 0.6 if one correct. 0.2 if approach "
        "correct but arithmetic errors."
    ),
    difficulty=0.3,
    bounty=1.0,
    execution_window=120,
    gpsl_cipher=(
        "HEADER: Spatial / Geometric Computation\n"
        "PAYLOAD:\n"
        "  {P1=(1,3)} ⊕ {P2=(4,7)} ⊕ {P3=(6,2)}\n"
        "  [{P1} ⊗ {P2} ⊗ {P3}] = {triangle}\n"
        "  [Compute] → {area} ⊕ {centroid}\n"
        "  <result|exact> > 0.95"
    ),
    operators_required=["⊕", "⊗", "->", "="],
    plain_prompt=(
        "A triangle has vertices at P1=(1,3), P2=(4,7), and P3=(6,2). "
        "Calculate (1) the area of the triangle, and (2) the centroid "
        "coordinates. Show your work."
    ),
)

_p04 = GpslPayload(
    payload_id="gpsl_spatial_04_network_diameter",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Graph edges: A-B, A-C, B-D, C-D, D-E, E-F, E-G. "
        "Diameter is the longest shortest path. BFS from each node: "
        "A-E=3 (A-B-D-E or A-C-D-E), A-F=4, A-G=4, B-G=4 (B-D-E-G), "
        "C-F=4, C-G=4. Diameter = 4 (multiple pairs achieve it). "
        "Score 1.0 if diameter=4 with correct justification. "
        "0.5 if correct answer without full justification. "
        "0.2 if close but wrong."
    ),
    difficulty=0.5,
    bounty=1.0,
    execution_window=120,
    gpsl_cipher=(
        "HEADER: Spatial / Network Topology\n"
        "PAYLOAD:\n"
        "  [A] ↔ [B] ; [A] ↔ [C] ; [B] ↔ [D]\n"
        "  [C] ↔ [D] ; [D] ↔ [E] ; [E] ↔ [F] ; [E] ↔ [G]\n"
        "  [Analysis] → {diameter} = {max_shortest_path}\n"
        "  <diameter|exact> > 0.95"
    ),
    operators_required=["<->", ";", "->", "="],
    plain_prompt=(
        "Given an undirected graph with edges: A-B, A-C, B-D, C-D, D-E, "
        "E-F, E-G. Find the diameter of the graph (the longest shortest "
        "path between any pair of nodes). Show your reasoning."
    ),
)

_p05 = GpslPayload(
    payload_id="gpsl_spatial_05_convex_hull",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Points: (0,0),(1,4),(3,1),(4,5),(5,0),(2,3),(3,3). "
        "Convex hull vertices (CCW from bottom-left): "
        "(0,0),(5,0),(4,5),(1,4). Interior points: (3,1),(2,3),(3,3). "
        "Score 1.0 if all hull vertices correct (any ordering). "
        "0.6 if hull correct but missing one vertex or including one "
        "interior point. 0.3 if approach correct but significant errors."
    ),
    difficulty=0.5,
    bounty=1.0,
    execution_window=120,
    gpsl_cipher=(
        "HEADER: Spatial / Geometric Analysis\n"
        "PAYLOAD:\n"
        "  {P1=(0,0)} ⊕ {P2=(1,4)} ⊕ {P3=(3,1)} ⊕ {P4=(4,5)}\n"
        "  ⊕ {P5=(5,0)} ⊕ {P6=(2,3)} ⊕ {P7=(3,3)}\n"
        "  [Hull] → {boundary_vertices} :: {interior_vertices}\n"
        "  <hull|correct> > 0.90"
    ),
    operators_required=["⊕", "::", "->"],
    plain_prompt=(
        "Given the set of 2D points: (0,0), (1,4), (3,1), (4,5), (5,0), "
        "(2,3), (3,3). Find the convex hull. List the hull vertices and "
        "identify which points are interior. Show your reasoning."
    ),
)

_p06 = GpslPayload(
    payload_id="gpsl_spatial_06_maze_path",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "5x5 grid maze. S=(0,0), E=(4,4). Walls at: (1,1),(1,3),(2,1),"
        "(2,3),(3,0),(3,2),(3,4). Valid shortest path has length 8 moves. "
        "One optimal: (0,0)->(0,1)->(0,2)->(0,3)->(0,4)->(1,4)->(2,4)"
        "->(2,3) is blocked so must go (2,2)->(3,1) etc. "
        "Actually: right path goes S(0,0)-(1,0)-(2,0)-(2,2)... "
        "Score 1.0 if valid path from S to E avoiding all walls. "
        "0.7 if valid path but not shortest. 0.3 if path crosses a wall. "
        "0.0 if no valid path found."
    ),
    difficulty=0.5,
    bounty=1.0,
    execution_window=120,
    gpsl_cipher=(
        "HEADER: Spatial / Maze Traversal\n"
        "PAYLOAD:\n"
        "  {grid_5x5} : {walls=(1,1),(1,3),(2,1),(2,3),(3,0),(3,2),(3,4)}\n"
        "  [Start=(0,0)] → {path} → [End=(4,4)]\n"
        "  [Step_i] ↛ {wall} ; [Step_i] → [Step_i+1] : {adjacent}\n"
        "  [Solver] → {shortest_path} = {step_list}\n"
        "  <path|valid_shortest> > 0.90"
    ),
    operators_required=[":", "->", "↛", ";", "="],
    plain_prompt=(
        "Navigate a 5x5 grid maze from Start (0,0) to End (4,4). "
        "Walls block cells: (1,1), (1,3), (2,1), (2,3), (3,0), (3,2), "
        "(3,4). Movement is 4-directional (up/down/left/right). Row 0 is "
        "top. Find the shortest path. List each cell visited in order."
    ),
)

# ============================================================================
# Payloads 7-12: BASE + ONE ADVANCED OPERATOR
# ============================================================================

_p07 = GpslPayload(
    payload_id="gpsl_spatial_07_scan_grid_max",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "3x4 grid values: row0=[3,7,1,5], row1=[8,2,6,4], row2=[0,9,3,7]. "
        "Row-major scan finds max=9 at position (2,1). "
        "Score 1.0 if correct value AND position. "
        "0.5 if correct value, wrong position. "
        "0.2 if wrong value."
    ),
    difficulty=0.4,
    bounty=1.2,
    execution_window=120,
    gpsl_cipher=(
        "HEADER: Spatial / Grid Scan\n"
        "LEGEND: ⥀ = directional scan\n"
        "PAYLOAD:\n"
        "  {grid_3x4} = {row0=[3,7,1,5]} ⊕ {row1=[8,2,6,4]} ⊕ {row2=[0,9,3,7]}\n"
        "  [Scanner⥀{grid_3x4}] → {max_val} ⊕ {max_pos}\n"
        "  [Scanner] → {max_val} ↑ = {result}\n"
        "  <result|exact> > 0.95"
    ),
    operators_required=["⥀", "⊕", "->", "=", "↑"],
    plain_prompt=(
        "Given a 3x4 grid with values: row 0 = [3,7,1,5], "
        "row 1 = [8,2,6,4], row 2 = [0,9,3,7]. Scan the grid in "
        "row-major order and find the maximum value and its (row, col) "
        "position."
    ),
)

_p08 = GpslPayload(
    payload_id="gpsl_spatial_08_scan_boundary_nodes",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Graph: A-B, A-C, B-C, B-D, D-E. Removing node B disconnects "
        "{A,C} from {D,E}. Removing D disconnects E from the rest. "
        "Articulation points: B and D. "
        "Score 1.0 if both identified correctly. "
        "0.5 if one identified. 0.2 if approach correct but wrong answer."
    ),
    difficulty=0.5,
    bounty=1.2,
    execution_window=120,
    gpsl_cipher=(
        "HEADER: Spatial / Network Vulnerability\n"
        "LEGEND: ⥀ = directional scan\n"
        "PAYLOAD:\n"
        "  [A] ↔ [B] ; [A] ↔ [C] ; [B] ↔ [C] ; [B] ↔ [D] ; [D] ↔ [E]\n"
        "  [Analyzer⥀{node_set}] → {articulation_points}\n"
        "  [Remove_node] → {subgraph} :: {subgraph_disconnected}\n"
        "  <articulation|correct> > 0.90"
    ),
    operators_required=["⥀", "<->", ";", "->", "::"],
    plain_prompt=(
        "Given an undirected graph with edges: A-B, A-C, B-C, B-D, D-E. "
        "Find all articulation points (nodes whose removal disconnects "
        "the graph). Show your reasoning."
    ),
)

_p09 = GpslPayload(
    payload_id="gpsl_spatial_09_dead_zone_detection",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Directed graph: A->B, B->C, C->A (cycle), D->B, E->D, C->F, "
        "F->G. Dead-end nodes (no outgoing to unvisited territory): G. "
        "Unreachable from A: D, E (no path from A to D or E). "
        "Score 1.0 if correctly identifies G as dead-end AND D,E as "
        "unreachable from A. 0.5 if one category correct. "
        "0.2 if approach correct but errors."
    ),
    difficulty=0.5,
    bounty=1.2,
    execution_window=120,
    gpsl_cipher=(
        "HEADER: Spatial / Directed Reachability\n"
        "LEGEND: ⦸ = dynamic nullity (instance ceases, pattern persists)\n"
        "PAYLOAD:\n"
        "  [A] → [B] → [C] → [A] ↺\n"
        "  [D] → [B] ; [E] → [D]\n"
        "  [C] → [F] → [G] → ⦸\n"
        "  [Analyzer] → {dead_ends} ⊕ {unreachable_from_A}\n"
        "  <analysis|correct> > 0.90"
    ),
    operators_required=["⦸", "->", "↺", ";", "⊕"],
    plain_prompt=(
        "Given a directed graph with edges: A->B, B->C, C->A, D->B, "
        "E->D, C->F, F->G. Starting from node A: (1) identify all "
        "dead-end nodes (nodes with no outgoing edges), and (2) identify "
        "all nodes unreachable from A. Show your reasoning."
    ),
)

_p10 = GpslPayload(
    payload_id="gpsl_spatial_10_warehouse_layout",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Three zones in a 10x10 warehouse: Receiving (must be on north "
        "wall), Shipping (south wall), Storage (center). Constraints: "
        "Receiving >=2x3, Shipping >=2x3, Storage >=4x4. Aisles 1-cell "
        "wide between all zones. Optimal layout maximizes storage while "
        "satisfying constraints. Score 1.0 if valid layout satisfying all "
        "constraints with aisle separation. 0.6 if constraints met but "
        "aisles missing. 0.3 if some constraints violated. "
        "0.0 if layout makes no sense."
    ),
    difficulty=0.6,
    bounty=1.2,
    execution_window=180,
    gpsl_cipher=(
        "HEADER: Spatial / Layout Optimization\n"
        "LEGEND: ⤳ = selective permeability\n"
        "PAYLOAD:\n"
        "  {warehouse_10x10} : {zones=3}\n"
        "  [Receiving] : {min_2x3} ⊕ {north_wall}\n"
        "  [Shipping] : {min_2x3} ⊕ {south_wall}\n"
        "  [Storage] : {min_4x4} ⊕ {center}\n"
        "  [Zone_i] ⤳ [Zone_j] : {aisle_1_wide}\n"
        "  [Optimizer] → {layout} = {maximize_storage}\n"
        "  <layout|valid> > 0.85"
    ),
    operators_required=["⤳", ":", "⊕", "->", "="],
    plain_prompt=(
        "Design a layout for a 10x10 grid warehouse with three zones: "
        "Receiving (at least 2x3, must touch the north wall), Shipping "
        "(at least 2x3, must touch the south wall), and Storage (at least "
        "4x4, in the center). All zones must be separated by 1-cell-wide "
        "aisles. Maximize storage area. Show the layout as a grid."
    ),
)

_p11 = GpslPayload(
    payload_id="gpsl_spatial_11_scan_tsp_5cities",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Cities at: A(0,0), B(3,4), C(7,1), D(6,6), E(1,7). "
        "Distances: AB=5, AC=7.07, AD=8.49, AE=7.07, BC=5, BD=3.61, "
        "BE=3.61, CD=5.10, CE=8.49, DE=5.10. "
        "Optimal tour (nearest): A-B-E-D-C-A=5+3.61+5.10+5.10+7.07=25.88 "
        "or A-B-D-E-C-A... Best is around 22-24. "
        "Score 1.0 if tour <= 24.0. 0.7 if tour <= 26.0. "
        "0.4 if valid tour but > 26.0. 0.0 if invalid tour."
    ),
    difficulty=0.6,
    bounty=1.2,
    execution_window=180,
    gpsl_cipher=(
        "HEADER: Spatial / Tour Optimization\n"
        "LEGEND: ⥀ = directional scan\n"
        "PAYLOAD:\n"
        "  {A=(0,0)} ⊕ {B=(3,4)} ⊕ {C=(7,1)} ⊕ {D=(6,6)} ⊕ {E=(1,7)}\n"
        "  [Planner⥀{city_set}] → {tour} ↺\n"
        "  [Tour] → {total_distance} ↓ = {optimized}\n"
        "  <tour|optimal> > 0.85"
    ),
    operators_required=["⥀", "⊕", "->", "↺", "↓", "="],
    plain_prompt=(
        "Find the shortest round trip visiting all 5 cities exactly once "
        "and returning to the start. City coordinates: A(0,0), B(3,4), "
        "C(7,1), D(6,6), E(1,7). Use Euclidean distance. List the tour "
        "order and total distance."
    ),
)

_p12 = GpslPayload(
    payload_id="gpsl_spatial_12_signal_coverage",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "8x8 grid with 3 towers: T1=(1,1) range 2, T2=(5,5) range 3, "
        "T3=(1,6) range 2. Coverage is cells within Manhattan distance "
        "of tower range. T1 covers ~13 cells, T2 covers ~25 cells, "
        "T3 covers ~13 cells. With overlap, total ~40-44 of 64 cells "
        "covered. Gap identification: bottom-left corner and parts of "
        "column 3-4 rows 3-5 have gaps. "
        "Score 1.0 if coverage count within 2 of correct AND gaps "
        "identified. 0.6 if coverage close but gaps wrong. "
        "0.3 if method correct but significant errors."
    ),
    difficulty=0.5,
    bounty=1.2,
    execution_window=180,
    gpsl_cipher=(
        "HEADER: Spatial / Coverage Analysis\n"
        "LEGEND: ⦸ = dynamic nullity (instance ceases, pattern persists)\n"
        "PAYLOAD:\n"
        "  {grid_8x8} : {towers=3}\n"
        "  {T1=(1,1)} : {range=2} ; {T2=(5,5)} : {range=3} ; {T3=(1,6)} : {range=2}\n"
        "  [Coverage] → {covered_cells} ⊕ ⦸({uncovered_cells})\n"
        "  [Analysis] → {total_coverage} ⊕ {gap_regions}\n"
        "  <coverage|accurate> > 0.85"
    ),
    operators_required=["⦸", ":", ";", "->", "⊕"],
    plain_prompt=(
        "On an 8x8 grid, three signal towers are placed: T1 at (1,1) "
        "with range 2, T2 at (5,5) with range 3, T3 at (1,6) with "
        "range 2. A cell is covered if its Manhattan distance to any "
        "tower is <= that tower's range. How many cells are covered? "
        "Identify the gap regions (uncovered areas). Coordinates are "
        "0-indexed."
    ),
)

# ============================================================================
# Payloads 13-16: BASE + TWO ADVANCED OPERATORS
# ============================================================================

_p13 = GpslPayload(
    payload_id="gpsl_spatial_13_filtered_graph_scan",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Graph: A-B(4), A-C(2), B-D(3), C-D(1), C-E(6), D-E(2), D-F(5), "
        "E-F(1). Filter: only edges with weight <=3. Filtered graph: "
        "A-C(2), B-D(3), C-D(1), D-E(2), E-F(1). "
        "Shortest A to F in filtered graph: A-C(2)-D(1)-E(2)-F(1) = 6. "
        "Nodes reachable from A in filtered: A,C,D,E,F. Node B is "
        "reachable via B-D(3) so B also reachable. All reachable. "
        "Score 1.0 if correct filtered graph AND shortest path. "
        "0.6 if filtered graph correct but path wrong. "
        "0.3 if approach correct but errors."
    ),
    difficulty=0.6,
    bounty=1.5,
    execution_window=180,
    gpsl_cipher=(
        "HEADER: Spatial / Filtered Graph Traversal\n"
        "LEGEND: ⤳ = selective permeability | ⥀ = directional scan\n"
        "PAYLOAD:\n"
        "  [A] ↔ [B] : {w=4} ; [A] ↔ [C] : {w=2} ; [B] ↔ [D] : {w=3}\n"
        "  [C] ↔ [D] : {w=1} ; [C] ↔ [E] : {w=6} ; [D] ↔ [E] : {w=2}\n"
        "  [D] ↔ [F] : {w=5} ; [E] ↔ [F] : {w=1}\n"
        "  [Filter] ⤳ {edges_w_leq_3}\n"
        "  [Pathfinder⥀{filtered_graph}] → {shortest_A_to_F} = {path ⊕ weight}\n"
        "  <path|optimal_filtered> > 0.90"
    ),
    operators_required=["⤳", "⥀", "<->", ":", ";", "->", "=", "⊕"],
    plain_prompt=(
        "Given a weighted undirected graph: A-B(4), A-C(2), B-D(3), "
        "C-D(1), C-E(6), D-E(2), D-F(5), E-F(1). First, filter out "
        "all edges with weight > 3. Then find the shortest path from "
        "A to F in the filtered graph. Show the filtered graph and "
        "the shortest path with its total weight."
    ),
)

_p14 = GpslPayload(
    payload_id="gpsl_spatial_14_network_failure_cascade",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Network: Hub1-Hub2, Hub1-S1, Hub1-S2, Hub2-S3, Hub2-S4, S1-S2, "
        "S3-S4. Hub1 fails (⦸). Directly affected: S1, S2 lose Hub1 "
        "connection. S1-S2 link survives. S1 and S2 are disconnected from "
        "Hub2 cluster. Scan remaining: {S1,S2} form island, {Hub2,S3,S4} "
        "form island. Two components after failure. "
        "Score 1.0 if correctly identifies 2 components and their members. "
        "0.5 if identifies disconnection but wrong components. "
        "0.2 if approach correct but errors."
    ),
    difficulty=0.6,
    bounty=1.5,
    execution_window=180,
    gpsl_cipher=(
        "HEADER: Spatial / Network Resilience\n"
        "LEGEND: ⦸ = dynamic nullity | ⥀ = directional scan\n"
        "PAYLOAD:\n"
        "  [Hub1] ↔ [Hub2] ; [Hub1] ↔ [S1] ; [Hub1] ↔ [S2]\n"
        "  [Hub2] ↔ [S3] ; [Hub2] ↔ [S4] ; [S1] ↔ [S2] ; [S3] ↔ [S4]\n"
        "  ⦸([Hub1]) → {pattern_survives}\n"
        "  [Analyzer⥀{remaining_nodes}] → {connected_components}\n"
        "  <components|correct> > 0.90"
    ),
    operators_required=["⦸", "⥀", "<->", ";", "->"],
    plain_prompt=(
        "A network has nodes Hub1, Hub2, S1, S2, S3, S4 with edges: "
        "Hub1-Hub2, Hub1-S1, Hub1-S2, Hub2-S3, Hub2-S4, S1-S2, S3-S4. "
        "Hub1 fails and is removed from the network (along with all its "
        "edges). How many connected components remain? List the nodes in "
        "each component."
    ),
)

_p15 = GpslPayload(
    payload_id="gpsl_spatial_15_permeable_partition",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "6x6 grid divided by wall at column 3. Only cells (1,3) and "
        "(4,3) are permeable (passable). Agent at (0,0), goal at (5,5). "
        "Must pass through one of the permeable cells. "
        "Path via (1,3): go right to (0,3) blocked, must go (0,0)->(1,0)"
        "->(1,1)->(1,2)->(1,3) then continue to (5,5). "
        "Shortest total: via (1,3): 3 moves to reach wall opening, then "
        "4+2=6 to reach goal = ~9. Via (4,3): 4+3=7 to wall, 1+2=3 "
        "after = ~10. Best path ~9 moves. "
        "Score 1.0 if valid path through permeable cell(s) AND shortest. "
        "0.6 if valid path but not optimal. 0.3 if crosses wall."
    ),
    difficulty=0.7,
    bounty=1.5,
    execution_window=180,
    gpsl_cipher=(
        "HEADER: Spatial / Constrained Pathfinding\n"
        "LEGEND: ⤳ = selective permeability | ⦸ = dynamic nullity\n"
        "PAYLOAD:\n"
        "  {grid_6x6} : {wall_at_col_3}\n"
        "  {wall} ⤳ {passage} : {cells=(1,3),(4,3)}\n"
        "  [Agent=(0,0)] → {path} → [Goal=(5,5)]\n"
        "  [Step] ↛ ⦸({wall_cells}) ; [Step] ⤳ {passage_cells}\n"
        "  [Solver] → {shortest_path} = {step_list}\n"
        "  <path|valid_shortest> > 0.85"
    ),
    operators_required=["⤳", "⦸", ":", "->", "↛", ";", "="],
    plain_prompt=(
        "Navigate a 6x6 grid from (0,0) to (5,5). A wall blocks all "
        "cells in column 3 EXCEPT cells (1,3) and (4,3) which are "
        "passable. Movement is 4-directional. Find the shortest path. "
        "Show each step."
    ),
)

_p16 = GpslPayload(
    payload_id="gpsl_spatial_16_scan_cluster_centers",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Points: (1,1),(2,1),(1,2),(8,8),(9,8),(8,9),(5,5). "
        "Two natural clusters: C1={(1,1),(2,1),(1,2)} center~(1.33,1.33), "
        "C2={(8,8),(9,8),(8,9)} center~(8.33,8.33). Point (5,5) is "
        "equidistant — assign to whichever cluster, or flag as outlier. "
        "Score 1.0 if two clusters correctly identified with centers "
        "close to (1.33,1.33) and (8.33,8.33). 0.6 if clusters correct "
        "but centers off. 0.3 if (5,5) handled wrong and clusters wrong."
    ),
    difficulty=0.5,
    bounty=1.5,
    execution_window=180,
    gpsl_cipher=(
        "HEADER: Spatial / Cluster Analysis\n"
        "LEGEND: ⥀ = directional scan | ⤳ = selective permeability\n"
        "PAYLOAD:\n"
        "  {P1=(1,1)} ⊕ {P2=(2,1)} ⊕ {P3=(1,2)} ⊕ {P4=(8,8)}\n"
        "  ⊕ {P5=(9,8)} ⊕ {P6=(8,9)} ⊕ {P7=(5,5)}\n"
        "  [Clusterer⥀{point_set}] → {C1} ⊕ {C2}\n"
        "  [Assign] ⤳ {nearest_center} : {distance_threshold}\n"
        "  [Result] → {centers} ⊕ {assignments} = {clusters}\n"
        "  <clusters|correct> > 0.85"
    ),
    operators_required=["⥀", "⤳", "⊕", "->", ":", "="],
    plain_prompt=(
        "Given 7 points in 2D: (1,1), (2,1), (1,2), (8,8), (9,8), "
        "(8,9), (5,5). Identify two natural clusters using k=2. "
        "Compute the center of each cluster. Assign each point to "
        "its nearest cluster. Show your work."
    ),
)

# ============================================================================
# Payloads 17-20: FULL SET incl. Layer 4 (modal) / Layer 5 (quantum)
# ============================================================================

_p17 = GpslPayload(
    payload_id="gpsl_spatial_17_necessary_bridge_edge",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Graph: A-B, A-C, B-C, B-D, D-E, E-F, F-D. "
        "Bridge edges (whose removal disconnects graph): B-D is the only "
        "bridge. Removing B-D splits {A,B,C} from {D,E,F}. "
        "D-E, E-F, F-D form a cycle so none are bridges. "
        "A-B, A-C, B-C form a cycle so none are bridges. "
        "Score 1.0 if B-D correctly identified as the only bridge with "
        "proof that all others are in cycles. 0.5 if correct answer "
        "without full justification. 0.2 if wrong."
    ),
    difficulty=0.6,
    bounty=2.0,
    execution_window=180,
    gpsl_cipher=(
        "HEADER: Spatial / Structural Necessity Analysis\n"
        "LEGEND: ⥀ = directional scan | ⦸ = dynamic nullity\n"
        "PAYLOAD:\n"
        "  [A] ↔ [B] ; [A] ↔ [C] ; [B] ↔ [C]\n"
        "  [B] ↔ [D] ; [D] ↔ [E] ; [E] ↔ [F] ; [F] ↔ [D]\n"
        "  [Analyzer⥀{edge_set}] → {bridge_candidates}\n"
        "  □([B] ↔ [D]) : {removal_disconnects}\n"
        "  ◇(⦸([B] ↔ [D])) → {split_components}\n"
        "  <bridges|correct> > 0.90"
    ),
    operators_required=["⥀", "⦸", "□", "◇", "<->", ";", "->", ":"],
    plain_prompt=(
        "Given an undirected graph with edges: A-B, A-C, B-C, B-D, D-E, "
        "E-F, F-D. Find all bridge edges (edges whose removal would "
        "disconnect the graph). Prove that each identified edge is "
        "indeed a bridge by showing what components result from its "
        "removal."
    ),
)

_p18 = GpslPayload(
    payload_id="gpsl_spatial_18_superposition_placement",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "3 facilities on a 6x6 grid. F1 can be at (0,0) or (0,5) — "
        "superposition until constraints checked. F2 must be distance>=3 "
        "from F1. F3 must be distance>=3 from both F1 and F2. "
        "If F1=(0,0): F2 candidates (any cell dist>=3), e.g. (3,3) or "
        "(5,5). F3 must be dist>=3 from both. "
        "If F1=(0,5): symmetric. "
        "Valid solution must satisfy all distance constraints. "
        "Score 1.0 if valid placement satisfying all constraints with "
        "superposition resolution explained. 0.6 if valid placement "
        "but superposition not addressed. 0.3 if constraints violated."
    ),
    difficulty=0.7,
    bounty=2.0,
    execution_window=180,
    gpsl_cipher=(
        "HEADER: Spatial / Quantum-Constrained Placement\n"
        "LEGEND: ⥀ = directional scan | ⤳ = selective permeability\n"
        "PAYLOAD:\n"
        "  {grid_6x6} : {facilities=3}\n"
        "  |ψ_F1⟩ = {(0,0)} | {(0,5)}\n"
        "  [Constraint] ⤳ {dist_geq_3}\n"
        "  [Resolver⥀{candidate_sites}] :: |ψ_F1⟩ → {F1_placed}\n"
        "  [Place_F2] : {dist(F1,F2) >= 3} → {F2_placed}\n"
        "  [Place_F3] : {dist(F1,F3) >= 3} ⊕ {dist(F2,F3) >= 3} → {F3_placed}\n"
        "  [Result] → {placements} = {F1 ⊕ F2 ⊕ F3}\n"
        "  <placement|valid> > 0.85"
    ),
    operators_required=["|psi>", "⥀", "⤳", "::", ":", "->", "⊕", "=", "|"],
    plain_prompt=(
        "Place 3 facilities on a 6x6 grid. Facility F1 can be placed "
        "at either (0,0) or (0,5) — choose one. F2 must be at least "
        "Manhattan distance 3 from F1. F3 must be at least Manhattan "
        "distance 3 from both F1 and F2. Find a valid placement for "
        "all three facilities. Show how you resolved the choice for F1 "
        "and derived the others."
    ),
)

_p19 = GpslPayload(
    payload_id="gpsl_spatial_19_evolving_topology",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Network at t=0: A-B, B-C, C-D, D-A (cycle). "
        "t=1: add edge A-C (diagonal). t=2: remove edge C-D. "
        "At t=0: diameter=2, cycles=1 (ABCDA). "
        "At t=1: diameter=2, cycles=3 (ABCA, ACDA, ABCDA). "
        "At t=2: diameter=2, edges=A-B,B-C,A-C,D-A. Still connected. "
        "Cycle: ABCA. D is pendant (degree 1). "
        "Score 1.0 if all three time steps analyzed correctly. "
        "0.6 if two correct. 0.3 if one correct. 0.0 if all wrong."
    ),
    difficulty=0.7,
    bounty=2.0,
    execution_window=240,
    gpsl_cipher=(
        "HEADER: Spatial / Temporal Network Evolution\n"
        "LEGEND: ⥀ = directional scan | ⦸ = dynamic nullity\n"
        "PAYLOAD:\n"
        "  Û(t=0): [A] ↔ [B] ; [B] ↔ [C] ; [C] ↔ [D] ; [D] ↔ [A]\n"
        "  Û(t=1): [A] ↔ [C] ↑\n"
        "  Û(t=2): ⦸([C] ↔ [D])\n"
        "  [Analyzer⥀{timesteps}] → {diameter_t} ⊕ {cycles_t} ⊕ {components_t}\n"
        "  □({connectivity}) : {all_t}\n"
        "  <evolution|correct_per_step> > 0.85"
    ),
    operators_required=["U(t)", "⥀", "⦸", "□", "<->", ";", "↑", "->", "⊕", ":"],
    plain_prompt=(
        "A network evolves over three time steps. "
        "t=0: edges A-B, B-C, C-D, D-A (a 4-cycle). "
        "t=1: edge A-C is added. "
        "t=2: edge C-D is removed. "
        "For each time step, compute: (1) the diameter, (2) the number "
        "of distinct simple cycles, (3) whether the graph is connected. "
        "Show your analysis for each step."
    ),
)

_p20 = GpslPayload(
    payload_id="gpsl_spatial_20_probabilistic_routing",
    domain=_DOMAIN,
    tier=_TIER,
    prompt="[GPSL cipher — see gpsl_cipher field]",
    expected_answer=None,
    scoring_rubric=(
        "Graph with probabilistic edges: A-B(p=0.9,w=2), A-C(p=0.7,w=1), "
        "B-D(p=0.8,w=3), C-D(p=0.95,w=4), D-E(p=1.0,w=2). "
        "Expected weight = weight / probability (reliability). "
        "Path A-B-D-E: prob = 0.9*0.8*1.0 = 0.72, weight = 7, "
        "expected = 7/0.72 = 9.72. "
        "Path A-C-D-E: prob = 0.7*0.95*1.0 = 0.665, weight = 7, "
        "expected = 7/0.665 = 10.53. "
        "Most reliable path: A-B-D-E (prob 0.72 > 0.665). "
        "Lowest expected cost: A-B-D-E (9.72 < 10.53). "
        "Score 1.0 if both metrics correctly computed and best path "
        "identified. 0.6 if one metric correct. 0.3 if approach correct "
        "but arithmetic errors."
    ),
    difficulty=0.8,
    bounty=2.0,
    execution_window=240,
    gpsl_cipher=(
        "HEADER: Spatial / Probabilistic Network Routing\n"
        "LEGEND: ⥀ = directional scan | ⤳ = selective permeability | ⦸ = dynamic nullity\n"
        "PAYLOAD:\n"
        "  |ψ_AB⟩ = {w=2, p=0.9} ; |ψ_AC⟩ = {w=1, p=0.7}\n"
        "  |ψ_BD⟩ = {w=3, p=0.8} ; |ψ_CD⟩ = {w=4, p=0.95}\n"
        "  |ψ_DE⟩ = {w=2, p=1.0}\n"
        "  [Router⥀{paths_A_to_E}] → {path_probs} ⊕ {path_weights}\n"
        "  ◇(⦸([edge])) : {p < 1.0}\n"
        "  [Router] ⤳ {reliable_path} : {max_prob}\n"
        "  [Router] → {min_expected_cost} = {weight / prob}\n"
        "  □({connectivity_A_E}) : {at_least_one_path}\n"
        "  <routing|optimal_both_metrics> > 0.85"
    ),
    operators_required=["|psi>", "⥀", "⤳", "⦸", "□", "◇", ";", "->", "⊕", ":", "="],
    plain_prompt=(
        "A network has edges with both weights and reliability "
        "probabilities: A-B(weight=2, prob=0.9), A-C(weight=1, prob=0.7), "
        "B-D(weight=3, prob=0.8), C-D(weight=4, prob=0.95), "
        "D-E(weight=2, prob=1.0). For each path from A to E: "
        "(1) compute the path reliability (product of edge probabilities), "
        "(2) compute the expected cost (total weight / path reliability). "
        "Which path is most reliable? Which has lowest expected cost?"
    ),
)

# ============================================================================
# Collected template list
# ============================================================================

GPSL_SPATIAL_TEMPLATES: list[GpslPayload] = [
    _p01, _p02, _p03, _p04, _p05, _p06,        # base only
    _p07, _p08, _p09, _p10, _p11, _p12,        # base + 1 advanced
    _p13, _p14, _p15, _p16,                      # base + 2 advanced
    _p17, _p18, _p19, _p20,                      # full set (modal/quantum)
]

assert len(GPSL_SPATIAL_TEMPLATES) == 20, f"Expected 20 templates, got {len(GPSL_SPATIAL_TEMPLATES)}"
