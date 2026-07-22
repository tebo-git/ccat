import svgwrite
import os
import json
import random
import math

OUTPUT_DIR = "data/abstract_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Core drawing functions ───────────────────────────────────────────────────

def make_svg(filename, draw_fn, size=100):
    dwg = svgwrite.Drawing(filename, size=(f"{size}px", f"{size}px"))
    dwg.add(dwg.rect(insert=(0,0), size=(size,size), fill="white", stroke="none"))
    draw_fn(dwg, size)
    dwg.save()

def draw_shape_element(dwg, shape, cx, cy, r, fill, stroke="#1e293b", rotation=0, stroke_width=2):
    if shape == "circle":
        dwg.add(dwg.circle(center=(cx,cy), r=r, fill=fill, stroke=stroke, stroke_width=stroke_width))
    elif shape == "square":
        el = dwg.rect(insert=(cx-r, cy-r), size=(r*2, r*2), fill=fill, stroke=stroke, stroke_width=stroke_width)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "triangle":
        pts = [(cx, cy-r), (cx+r, cy+r), (cx-r, cy+r)]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=stroke_width)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "pentagon":
        pts = [(cx + r*math.cos(math.radians(90 + 72*i)),
                cy - r*math.sin(math.radians(90 + 72*i))) for i in range(5)]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=stroke_width)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "hexagon":
        pts = [(cx + r*math.cos(math.radians(60*i)),
                cy + r*math.sin(math.radians(60*i))) for i in range(6)]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=stroke_width)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "cross":
        t = max(r // 3, 4)
        pts = [
            (cx-t, cy-r), (cx+t, cy-r), (cx+t, cy-t),
            (cx+r, cy-t), (cx+r, cy+t), (cx+t, cy+t),
            (cx+t, cy+r), (cx-t, cy+r), (cx-t, cy+t),
            (cx-r, cy+t), (cx-r, cy-t), (cx-t, cy-t)
        ]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=stroke_width)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "diamond":
        pts = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=stroke_width)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "arrow":
        s = r
        t = max(s // 3, 4)
        pts = [
            (cx, cy-s), (cx+s, cy), (cx+t, cy),
            (cx+t, cy+s), (cx-t, cy+s), (cx-t, cy),
            (cx-s, cy)
        ]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=stroke_width)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "star":
        outer, inner = r, r // 2
        pts = []
        for i in range(10):
            angle = math.radians(90 + i * 36)
            rad = outer if i % 2 == 0 else inner
            pts.append((cx + rad * math.cos(angle), cy - rad * math.sin(angle)))
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=stroke_width)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "octagon":
        pts = [(cx + r*math.cos(math.radians(45*i)),
                cy + r*math.sin(math.radians(45*i))) for i in range(8)]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=stroke_width)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)

def add_dot(dwg, position, cx, cy, r, fill="#1e293b", dot_r=4):
    offset = r * 0.55
    positions = {
        "top-left":     (cx - offset, cy - offset),
        "top-right":    (cx + offset, cy - offset),
        "bottom-left":  (cx - offset, cy + offset),
        "bottom-right": (cx + offset, cy + offset),
        "center":       (cx, cy),
        "top":          (cx, cy - offset),
        "bottom":       (cx, cy + offset),
        "left":         (cx - offset, cy),
        "right":        (cx + offset, cy),
    }
    dx, dy = positions.get(position, (cx, cy))
    dwg.add(dwg.circle(center=(dx, dy), r=dot_r, fill=fill))

def draw_question_mark(dwg):
    dwg.add(dwg.text("?", insert=(32, 65), font_size="45px",
            fill="#94a3b8", font_family="Arial", font_weight="bold"))

def draw_shape_with_inner(dwg, outer, inner, cx, cy, outer_r, inner_r,
                           outer_fill, inner_fill, outer_color, inner_color,
                           outer_rot=0, inner_rot=0):
    draw_shape_element(dwg, outer, cx, cy, outer_r, outer_fill,
                       stroke=outer_color, rotation=outer_rot)
    draw_shape_element(dwg, inner, cx, cy, inner_r, inner_fill,
                       stroke=inner_color, rotation=inner_rot)

def draw_grid_pattern(dwg, rows, cols, filled_cells, cell_size=20, color="#2563eb"):
    """Draw a grid of small squares, some filled."""
    start_x = 50 - (cols * cell_size) // 2
    start_y = 50 - (rows * cell_size) // 2
    for r in range(rows):
        for c in range(cols):
            x = start_x + c * cell_size
            y = start_y + r * cell_size
            fill = color if (r, c) in filled_cells else "white"
            dwg.add(dwg.rect(insert=(x+1, y+1), size=(cell_size-2, cell_size-2),
                             fill=fill, stroke="#1e293b", stroke_width=1))

def shuffle_with_correct(correct, wrong_list):
    # Deduplicate wrong list
    seen = set()
    unique_wrong = []
    for w in wrong_list:
        key = str(w)
        if key not in seen and str(w) != str(correct):
            seen.add(key)
            unique_wrong.append(w)
    # Pad if needed
    while len(unique_wrong) < 4:
        unique_wrong.append(wrong_list[0] if wrong_list else correct)
    all_opts = [correct] + unique_wrong[:4]
    random.shuffle(all_opts)
    label = chr(65 + all_opts.index(correct))
    return all_opts, label

COLORS = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
GRAY = "#94a3b8"
ALL_SHAPES = ["circle", "square", "triangle", "diamond", "pentagon",
              "hexagon", "star", "cross", "arrow"]  # No octagon

# Shapes grouped by number of sides (for "sides increases" patterns)
SIDES_ORDER = ["triangle", "square", "pentagon", "hexagon"]  # No octagon -- too similar to circle

# ─── EASY generators (genuine but approachable) ───────────────────────────────

def gen_sides_increase(qid):
    """Easy: number of sides increases -- only use triangle/square/pentagon/hexagon (visually distinct)."""
    color = random.choice(COLORS)
    # Only use shapes that are clearly visually distinct from each other
    # Never use octagon -- looks too similar to hexagon/circle at small size
    DISTINCT_SHAPES = ["triangle", "square", "pentagon", "hexagon"]
    
    # Pick a starting index: either 0 (triangle->square->pentagon->hexagon)
    # or variation sequences
    sequences = [
        (["triangle", "square", "pentagon", "hexagon"], "triangle"),  # wraps to start
        (["square", "pentagon", "hexagon", "triangle"], "square"),    # wrap
        (["triangle", "square", "pentagon", "hexagon"], "hexagon"),   # NOT wrap -- just repeat hexagon as wrong signal
    ]
    seq_shapes, _ = random.choice(sequences[:2])  # always use first two
    correct_shape = "hexagon" if seq_shapes[-1] == "pentagon" else "triangle"
    
    # Simple reliable sequence: triangle -> square -> pentagon -> hexagon
    seq_shapes = ["triangle", "square", "pentagon", "hexagon"]
    correct_shape = "triangle"  # wraps around -- restart the cycle
    r = 30

    seq_files = []
    for i, shape in enumerate(seq_shapes):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, shape=shape):
            draw_shape_element(dwg, shape, 50, 50, r, color)
        make_svg(fname, draw)
        seq_files.append(fname)

    # Wrong options: all visually distinct from correct (triangle)
    wrong_opts = [
        "square",    # 2 back
        "pentagon",  # 1 back
        "hexagon",   # last in sequence -- most tempting wrong answer
        "diamond",   # completely different
    ]
    all_opts, correct_label = shuffle_with_correct(correct_shape, wrong_opts)

    opt_files = []
    for i, shape in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, shape=shape):
            draw_shape_element(dwg, shape, 50, 50, r, color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "The sequence cycles through shapes with increasing sides: triangle (3), square (4), pentagon (5), hexagon (6). After hexagon, it cycles back to triangle."
    }

def gen_rotation_with_fill(qid):
    """Easy: rotation series with fill change. Never use diamond (symmetric when rotated).
    Uses multiple structural variants to avoid repetition."""
    # Never use diamond or circle -- they look the same rotated
    shape = random.choice(["triangle", "arrow", "pentagon"])
    color = random.choice(COLORS)
    r = 28

    variant = random.randint(1, 3)

    if variant == 1:
        # Classic: 90 degree rotation, fill alternates colored/white
        seq = [(0, color), (90, "white"), (180, color), (270, "white")]
        correct = (0, color)   # completes the cycle: back to start AND filled
        wrong_opts = [
            (0, "white"),    # right rotation WRONG fill -- most tempting trap
            (270, color),    # previous step repeated
            (90, color),     # wrong rotation right fill
            (180, "white"),  # two steps back
        ]
        explanation = "Two rules: shape rotates 90° clockwise AND alternates filled/empty each step."

    elif variant == 2:
        # 90 degree rotation, fill stays same throughout
        seq = [(0, color), (90, color), (180, color), (270, color)]
        correct = (0, color)   # completes full rotation back to start
        wrong_opts = [
            (90, color),    # one step -- didn't complete cycle
            (270, color),   # previous step repeated
            (180, color),   # two steps back
            (0, "white"),   # right rotation wrong fill
        ]
        explanation = "Shape rotates 90° clockwise each step. Fill stays constant. After 270°, it returns to 0°."

    else:
        # 180 degree rotation alternating (flip pattern)
        seq = [(0, color), (180, color), (0, "white"), (180, "white")]
        correct = (0, color)   # cycle restarts: 0 degrees filled
        wrong_opts = [
            (180, color),    # wrong rotation right fill
            (0, "white"),    # right rotation wrong fill -- previous step
            (180, "white"),  # both wrong
            (90, color),     # completely wrong rotation
        ]
        explanation = "Two rules: shape flips 180° each step AND fill alternates every two steps."

    seq_files = []
    for i, (rot, fill) in enumerate(seq):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, rot=rot, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color, rotation=rot)
        make_svg(fname, draw)
        seq_files.append(fname)

    all_opts, correct_label = shuffle_with_correct(correct, wrong_opts)

    opt_files = []
    for i, (rot, fill) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, rot=rot, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": explanation
    }

def gen_dot_clockwise_in_shape(qid):
    """Easy: dot moves clockwise inside different shapes each step."""
    shapes = ["square", "pentagon", "hexagon", "diamond"]
    shape = random.choice(shapes)
    positions = ["top-left", "top-right", "bottom-right", "bottom-left"]
    start = random.randint(0, 3)
    color = random.choice(COLORS)
    r = 28

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        pos = positions[(start + i) % 4]
        def draw(dwg, size, pos=pos):
            draw_shape_element(dwg, shape, 50, 50, r, "white", stroke=color)
            add_dot(dwg, pos, 50, 50, r, fill=color)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct_pos = positions[(start + 4) % 4]
    wrong_positions = [
        positions[(start + 3) % 4],
        positions[(start + 1) % 4],
        positions[(start + 2) % 4],
        "center",
    ]
    all_pos, correct_label = shuffle_with_correct(correct_pos, wrong_positions)

    opt_files = []
    for i, pos in enumerate(all_pos):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, pos=pos):
            draw_shape_element(dwg, shape, 50, 50, r, "white", stroke=color)
            add_dot(dwg, pos, 50, 50, r, fill=color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"The dot moves clockwise around the corners of the shape."
    }

def gen_size_increase_series(qid):
    """Easy: shape grows larger -- VERY distinct wrong options to avoid ambiguity."""
    shape = random.choice(["circle", "square", "triangle", "pentagon", "hexagon"])
    color = random.choice(COLORS)

    variant = random.randint(1, 2)

    if variant == 1:
        # Grows: 8, 18, 28, 38 -- next is 48
        sizes = [8, 18, 28, 38]
        correct_size = 48
        # Wrong: tiny, small, medium, slightly off -- all clearly different from 48
        wrong_sizes = [8, 18, 28, 42]
        explanation = "The shape grows larger by 10 units each step. After 38, the next is 48."
    else:
        # Shrinks: 44, 32, 20, 8 -- next wraps or is tiny
        sizes = [44, 32, 20, 8]
        correct_size = 8  # Wait -- next would be negative, so cycle back
        correct_size = 44  # cycle back to large
        wrong_sizes = [8, 20, 32, 38]
        explanation = "The shape shrinks by 12 units each step. After the smallest, it cycles back to the largest."

    seq_files = []
    for i, s in enumerate(sizes):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, s=s):
            draw_shape_element(dwg, shape, 50, 50, max(s, 4), color)
        make_svg(fname, draw)
        seq_files.append(fname)

    # Ensure wrong options are all clearly distinct from correct (min 10 apart)
    unique_wrong = []
    for w in wrong_sizes:
        if abs(w - correct_size) >= 10 and w not in unique_wrong:
            unique_wrong.append(w)
    # Pad with very distinct sizes if needed
    for fallback in [5, 15, 25, 35, 45]:
        if len(unique_wrong) >= 4:
            break
        if abs(fallback - correct_size) >= 10 and fallback not in unique_wrong:
            unique_wrong.append(fallback)

    all_sizes, correct_label = shuffle_with_correct(correct_size, unique_wrong[:4])

    opt_files = []
    for i, s in enumerate(all_sizes):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, s=s):
            draw_shape_element(dwg, shape, 50, 50, max(s, 4), color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "The shape grows larger by the same amount each step."
    }

def gen_shape_mirror(qid):
    """Easy: shape alternates orientations. Never use symmetric shapes."""
    # Only use shapes where rotation is clearly visible
    shape = random.choice(["triangle", "arrow"])
    color = random.choice(COLORS)
    r = 28

    variant = random.randint(1, 2)

    if variant == 1:
        # Alternates 0 and 180 (upright vs flipped)
        rotations = [0, 180, 0, 180]
        correct_rot = 0
        # Wrong: 180 (continuing wrong), 90, 270 (clearly different)
        wrong_rots = [180, 90, 270, 135]
        explanation = "The shape alternates between upright (0°) and flipped (180°). After flipped, the next is upright."
    else:
        # Alternates 90 and 270 (left vs right)
        rotations = [90, 270, 90, 270]
        correct_rot = 90
        wrong_rots = [270, 0, 180, 45]
        explanation = "The shape alternates between pointing left (90°) and pointing right (270°)."

    seq_files = []
    for i, rot in enumerate(rotations):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, r, color, rotation=rot)
        make_svg(fname, draw)
        seq_files.append(fname)

    all_rots, correct_label = shuffle_with_correct(correct_rot, wrong_rots)

    opt_files = []
    for i, rot in enumerate(all_rots):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, r, color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": explanation
    }

def gen_odd_one_out_symmetry(qid):
    """Easy: four shapes same rotation, one clearly different. Use shapes where rotation is obvious."""
    # Only use asymmetric shapes where rotation difference is very clear
    shape = random.choice(["triangle", "arrow", "pentagon"])
    color = random.choice(COLORS)
    majority_rot = 0
    # Use 90 or 180 -- very obvious rotation difference, not subtle 45 degrees
    outlier_rot = random.choice([90, 180, 270])

    rots = [majority_rot] * 4 + [outlier_rot]
    random.shuffle(rots)
    correct_label = chr(65 + rots.index(outlier_rot))

    opt_files = []
    for i, rot in enumerate(rots):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, 30, color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "odd_one_out",
        "question": "Which figure does NOT belong with the others?",
        "sequence_images": [], "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Four figures point in the same direction (0°). One is rotated {outlier_rot}° and clearly does not belong."
    }

def gen_odd_one_out_sides(qid):
    """Easy: four shapes have same number of sides, one has different sides."""
    # Group shapes by sides
    groups = [
        (["triangle", "triangle", "triangle", "triangle"], "diamond"),
        (["square", "square", "square", "square"], "triangle"),
        (["pentagon", "pentagon", "pentagon", "pentagon"], "hexagon"),
        (["hexagon", "hexagon", "hexagon", "hexagon"], "pentagon"),
    ]
    group, outlier = random.choice(groups)
    color = random.choice(COLORS)

    shapes_list = group + [outlier]
    random.shuffle(shapes_list)
    correct_label = chr(65 + shapes_list.index(outlier))

    opt_files = []
    for i, shape in enumerate(shapes_list):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, shape=shape):
            draw_shape_element(dwg, shape, 50, 50, 28, color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "odd_one_out",
        "question": "Which figure does NOT belong with the others?",
        "sequence_images": [], "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "Four shapes have the same number of sides. One shape has a different number of sides."
    }

# ─── MEDIUM generators ────────────────────────────────────────────────────────

def gen_inner_shape_series(qid):
    """Medium: inner shape changes while outer stays fixed."""
    outer = random.choice(["square", "circle", "hexagon"])
    inner_seq = random.sample(["triangle", "diamond", "arrow", "star", "cross"], 4)
    correct_inner = random.choice([s for s in ALL_SHAPES if s not in inner_seq and s != outer])
    color = random.choice(COLORS)
    outer_r, inner_r = 35, 16

    seq_files = []
    for i, inner in enumerate(inner_seq):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, inner=inner):
            draw_shape_element(dwg, outer, 50, 50, outer_r, "white")
            draw_shape_element(dwg, inner, 50, 50, inner_r, color)
        make_svg(fname, draw)
        seq_files.append(fname)

    wrong_opts = [
        inner_seq[-1],   # repeat last
        inner_seq[-2],   # two back
        inner_seq[0],    # first in sequence
        outer,           # outer shape
    ]
    all_opts, correct_label = shuffle_with_correct(correct_inner, wrong_opts)

    opt_files = []
    for i, inner in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, inner=inner):
            draw_shape_element(dwg, outer, 50, 50, outer_r, "white")
            draw_shape_element(dwg, inner, 50, 50, inner_r, color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"The outer shape stays fixed. Each step introduces a new inner shape in sequence."
    }

def gen_grid_pattern_series(qid):
    """Medium: a 3x3 grid fills progressively -- one cell added each step."""
    color = random.choice(COLORS)
    all_cells = [(r, c) for r in range(3) for c in range(3)]
    random.shuffle(all_cells)

    # Sequence: 1, 3, 5, 7 cells filled
    counts = [1, 3, 5, 7]
    correct_count = 9  # all filled

    seq_files = []
    for i, count in enumerate(counts):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        filled = set(all_cells[:count])
        def draw(dwg, size, filled=filled):
            draw_grid_pattern(dwg, 3, 3, filled, cell_size=26, color=color)
        make_svg(fname, draw)
        seq_files.append(fname)

    # Options: 9 filled (correct), 8 filled, 7 filled, 6 filled, 5 filled
    wrong_counts = [8, 7, 6, 5]
    all_counts, correct_label = shuffle_with_correct(correct_count, wrong_counts)

    opt_files = []
    for i, count in enumerate(all_counts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        filled = set(all_cells[:count])
        def draw(dwg, size, filled=filled):
            draw_grid_pattern(dwg, 3, 3, filled, cell_size=26, color=color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "The number of filled cells increases by 2 each step (1, 3, 5, 7...). The next must have all 9 cells filled."
    }

def gen_double_shape_series(qid):
    """Medium: two shapes move independently -- one rotates, one changes size."""
    shape_a = random.choice(["triangle", "arrow", "pentagon"])
    shape_b = random.choice(["circle", "square", "hexagon"])
    color_a = random.choice(COLORS)
    color_b = random.choice([c for c in COLORS if c != color_a])

    rotations = [0, 90, 180, 270]
    sizes_b = [10, 16, 22, 28]
    r_a = 22

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        rot, sz = rotations[i], sizes_b[i]
        def draw(dwg, size, rot=rot, sz=sz):
            # shape_a top-left rotating
            draw_shape_element(dwg, shape_a, 30, 30, r_a, color_a, rotation=rot)
            # shape_b bottom-right growing
            draw_shape_element(dwg, shape_b, 70, 70, sz, color_b)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct = (0, 34)  # shape_a back to 0, shape_b largest
    wrong_opts = [
        (270, 34),  # shape_a wrong, shape_b right
        (0, 28),    # shape_a right, shape_b wrong (prev size)
        (90, 34),   # shape_a wrong, shape_b right
        (0, 22),    # shape_a right, shape_b too small
    ]
    all_opts, correct_label = shuffle_with_correct(correct, wrong_opts)

    opt_files = []
    for i, (rot, sz) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, rot=rot, sz=sz):
            draw_shape_element(dwg, shape_a, 30, 30, r_a, color_a, rotation=rot)
            draw_shape_element(dwg, shape_b, 70, 70, sz, color_b)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Two independent rules: the top-left shape rotates 90 degrees each step, while the bottom-right shape grows larger. Both must be correct."
    }

def gen_odd_one_out_inner_shape(qid):
    """Medium: four figures have same outer+inner combo, one inner differs."""
    outer = random.choice(["square", "circle", "hexagon", "pentagon"])
    inner_group = random.choice(["triangle", "diamond", "star", "cross", "arrow"])
    outlier_inner = random.choice([s for s in ["triangle", "diamond", "star", "cross", "arrow"]
                                   if s != inner_group])
    color = random.choice(COLORS)
    outer_r, inner_r = 34, 15

    inners = [inner_group] * 4 + [outlier_inner]
    random.shuffle(inners)
    correct_label = chr(65 + inners.index(outlier_inner))

    opt_files = []
    for i, inner in enumerate(inners):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, inner=inner):
            draw_shape_element(dwg, outer, 50, 50, outer_r, "white")
            draw_shape_element(dwg, inner, 50, 50, inner_r, color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "odd_one_out",
        "question": "Which figure does NOT belong with the others?",
        "sequence_images": [], "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Four figures share the same outer and inner shape combination. One has a different inner shape."
    }

def gen_odd_one_out_combined(qid):
    """Medium: four share TWO attributes (shape + fill), outlier breaks one."""
    shape = random.choice(["circle", "square", "pentagon", "hexagon"])
    color = random.choice(COLORS)
    majority_rot = 0

    # Four: same shape, same fill, same rotation
    # Outlier: same shape, same fill, DIFFERENT rotation
    outlier_rot = random.choice([45, 90, 135, 180])

    rots = [majority_rot] * 4 + [outlier_rot]
    fills = [color] * 5
    random.shuffle(rots)
    # Find where outlier_rot is after shuffle
    correct_label = chr(65 + rots.index(outlier_rot))

    opt_files = []
    for i, (rot, fill) in enumerate(zip(rots, fills)):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, rot=rot, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, 28, fill, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "odd_one_out",
        "question": "Which figure does NOT belong with the others?",
        "sequence_images": [], "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "All figures share the same shape and color but one is oriented differently."
    }

def gen_position_series(qid):
    """Medium: small shape moves diagonally across a 3x3 grid."""
    shape = random.choice(["circle", "square", "triangle", "diamond"])
    color = random.choice(COLORS)
    # Diagonal positions: top-left -> center -> bottom-right -> top-right -> center -> bottom-left
    positions_x = [20, 35, 50, 65]
    positions_y = [20, 35, 50, 65]
    # Move diagonally
    coords = [(20, 20), (35, 35), (50, 50), (65, 65)]
    correct_coord = (80, 80) if random.random() > 0.5 else (20, 80)
    # Simpler: move right across the top
    coords = [(15, 50), (35, 50), (55, 50), (75, 50)]
    correct_coord = (50, 50)  # back to center

    seq_files = []
    for i, (cx, cy) in enumerate(coords):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, cx=cx, cy=cy):
            # Draw border box
            dwg.add(dwg.rect(insert=(5,5), size=(90,90), fill="none",
                            stroke="#e2e8f0", stroke_width=1))
            draw_shape_element(dwg, shape, cx, cy, 12, color)
        make_svg(fname, draw)
        seq_files.append(fname)

    wrong_coords = [(15, 50), (35, 50), (75, 50), (50, 20)]
    all_coords, correct_label = shuffle_with_correct(correct_coord, wrong_coords)

    opt_files = []
    for i, (cx, cy) in enumerate(all_coords):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, cx=cx, cy=cy):
            dwg.add(dwg.rect(insert=(5,5), size=(90,90), fill="none",
                            stroke="#e2e8f0", stroke_width=1))
            draw_shape_element(dwg, shape, cx, cy, 12, color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "The shape moves across the frame in a consistent direction. Track the position to find where it ends up next."
    }

# ─── HARD generators ─────────────────────────────────────────────────────────

def gen_matrix_shape_rotation(qid):
    """Hard: 3x3 matrix where shape AND rotation follow row/column rules."""
    shapes = random.sample(["triangle", "arrow", "pentagon", "star", "cross"], 3)
    color = random.choice(COLORS)
    row_rots = [0, 90, 180]

    cells = []
    for row in range(3):
        for col in range(3):
            cells.append((shapes[col], row_rots[row]))

    missing_idx = random.randint(0, 8)
    correct_shape, correct_rot = cells[missing_idx]

    matrix_files = []
    for i, (shape, rot) in enumerate(cells):
        if i == missing_idx:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}_missing.svg"
            def draw(dwg, size):
                draw_question_mark(dwg)
        else:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}.svg"
            def draw(dwg, size, shape=shape, rot=rot):
                draw_shape_element(dwg, shape, 50, 50, 28, color, rotation=rot)
        make_svg(fname, draw)
        matrix_files.append(fname)

    other_shapes = [s for s in shapes if s != correct_shape]
    wrong_opts = [
        (correct_shape, (correct_rot + 90) % 360),   # right shape wrong rot
        (other_shapes[0], correct_rot),               # wrong shape right rot
        (other_shapes[1], correct_rot),               # wrong shape right rot
        (correct_shape, (correct_rot + 180) % 360),  # right shape opposite rot
    ]
    all_opts, correct_label = shuffle_with_correct(
        (correct_shape, correct_rot), wrong_opts)

    opt_files = []
    for i, (shape, rot) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, shape=shape, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, 28, color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "matrix_3x3",
        "question": "Which figure completes the 3x3 matrix?",
        "sequence_images": matrix_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Each column uses a different shape. Each row uses a different rotation (0, 90, 180 degrees). The missing piece must match both its row and column rules."
    }

def gen_matrix_size_fill(qid):
    """Hard: 3x3 matrix where size and fill follow independent row/column rules."""
    shape = random.choice(["circle", "square", "pentagon", "hexagon"])
    color = random.choice(COLORS)
    col_sizes = [14, 24, 34]
    row_fills = ["white", GRAY, color]

    cells = []
    for row in range(3):
        for col in range(3):
            cells.append((col_sizes[col], row_fills[row]))

    missing_idx = random.randint(0, 8)
    correct_size, correct_fill = cells[missing_idx]

    matrix_files = []
    for i, (sz, fill) in enumerate(cells):
        if i == missing_idx:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}_missing.svg"
            def draw(dwg, size):
                draw_question_mark(dwg)
        else:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}.svg"
            def draw(dwg, size, sz=sz, fill=fill):
                draw_shape_element(dwg, shape, 50, 50, sz, fill, stroke=color)
        make_svg(fname, draw)
        matrix_files.append(fname)

    other_sizes = [s for s in col_sizes if s != correct_size]
    other_fills = [f for f in row_fills if f != correct_fill]
    wrong_opts = [
        (correct_size, other_fills[0]),   # right size wrong fill
        (other_sizes[0], correct_fill),   # wrong size right fill
        (other_sizes[1], correct_fill),   # wrong size right fill
        (correct_size, other_fills[1]),   # right size different wrong fill
    ]
    all_opts, correct_label = shuffle_with_correct(
        (correct_size, correct_fill), wrong_opts)

    opt_files = []
    for i, (sz, fill) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, sz=sz, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, sz, fill, stroke=color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "matrix_3x3",
        "question": "Which figure completes the 3x3 matrix?",
        "sequence_images": matrix_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Each column determines the size (small, medium, large). Each row determines the fill (empty, grey, colored). Find the intersection."
    }

def gen_three_rule_series(qid):
    """Hard: three simultaneous changing rules."""
    shapes = random.sample(["triangle", "square", "pentagon", "hexagon", "circle"], 3)
    color = random.choice(COLORS)
    shape_seq = [shapes[0], shapes[1], shapes[2], shapes[0]]
    rotations = [0, 90, 180, 270]
    fills = [color, "white", color, "white"]
    r = 26

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        shape, rot, fill = shape_seq[i], rotations[i], fills[i]
        def draw(dwg, size, shape=shape, rot=rot, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color, rotation=rot)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct = (shapes[1], 0, color)
    wrong_opts = [
        (shapes[1], 270, color),     # wrong rotation
        (shapes[0], 0, color),       # wrong shape
        (shapes[1], 0, "white"),     # wrong fill
        (shapes[2], 0, color),       # wrong shape
    ]
    all_opts, correct_label = shuffle_with_correct(correct, wrong_opts)

    opt_files = []
    for i, (shape, rot, fill) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, shape=shape, rot=rot, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Three rules operate simultaneously: shapes cycle in sequence, rotation increases 90 degrees each step, and fill alternates filled/empty. All three must match."
    }

def gen_inner_outer_both_change(qid):
    """Hard: both inner and outer shapes rotate independently."""
    outer = random.choice(["square", "hexagon", "pentagon"])
    inner = random.choice(["triangle", "arrow", "star", "cross"])
    color_outer = random.choice(COLORS)
    color_inner = random.choice([c for c in COLORS if c != color_outer])
    outer_r, inner_r = 35, 16

    outer_rots = [0, 90, 180, 270]
    inner_rots = [0, 180, 0, 180]  # inner oscillates

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        or_, ir = outer_rots[i], inner_rots[i]
        def draw(dwg, size, or_=or_, ir=ir):
            draw_shape_element(dwg, outer, 50, 50, outer_r, "white",
                               stroke=color_outer, rotation=or_)
            draw_shape_element(dwg, inner, 50, 50, inner_r, color_inner,
                               rotation=ir)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct = (0, 0)  # outer back to 0, inner also 0
    wrong_opts = [
        (0, 180),    # outer right inner wrong
        (270, 0),    # outer wrong inner right
        (90, 0),     # outer wrong inner right
        (0, 90),     # outer right inner wrong
    ]
    all_opts, correct_label = shuffle_with_correct(correct, wrong_opts)

    opt_files = []
    for i, (or_, ir) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, or_=or_, ir=ir):
            draw_shape_element(dwg, outer, 50, 50, outer_r, "white",
                               stroke=color_outer, rotation=or_)
            draw_shape_element(dwg, inner, 50, 50, inner_r, color_inner,
                               rotation=ir)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "Two independent rules: the outer shape rotates 90 degrees clockwise each step, while the inner shape alternates between two orientations. Track both independently."
    }

def gen_matrix_inner_outer(qid):
    """Hard: 3x3 matrix with shape-in-shape where both vary."""
    outers = random.sample(["square", "circle", "hexagon"], 3)
    inners = random.sample(["triangle", "diamond", "cross"], 3)
    color = random.choice(COLORS)
    outer_r, inner_r = 32, 14

    cells = []
    for row in range(3):
        for col in range(3):
            cells.append((outers[col], inners[row]))

    missing_idx = random.randint(0, 8)
    correct_outer, correct_inner = cells[missing_idx]

    matrix_files = []
    for i, (out, inn) in enumerate(cells):
        if i == missing_idx:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}_missing.svg"
            def draw(dwg, size):
                draw_question_mark(dwg)
        else:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}.svg"
            def draw(dwg, size, out=out, inn=inn):
                draw_shape_element(dwg, out, 50, 50, outer_r, "white")
                draw_shape_element(dwg, inn, 50, 50, inner_r, color)
        make_svg(fname, draw)
        matrix_files.append(fname)

    other_outers = [o for o in outers if o != correct_outer]
    other_inners = [i for i in inners if i != correct_inner]
    wrong_opts = [
        (other_outers[0], correct_inner),
        (correct_outer, other_inners[0]),
        (other_outers[1], correct_inner),
        (correct_outer, other_inners[1]),
    ]
    all_opts, correct_label = shuffle_with_correct(
        (correct_outer, correct_inner), wrong_opts)

    opt_files = []
    for i, (out, inn) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, out=out, inn=inn):
            draw_shape_element(dwg, out, 50, 50, outer_r, "white")
            draw_shape_element(dwg, inn, 50, 50, inner_r, color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "matrix_3x3",
        "question": "Which figure completes the 3x3 matrix?",
        "sequence_images": matrix_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "Each column determines the outer shape. Each row determines the inner shape. Find the combination that satisfies both the row and column of the missing cell."
    }

def gen_odd_one_out_two_rules(qid):
    """Hard: odd one out where you must spot which of TWO rules is broken."""
    shape = random.choice(["triangle", "arrow", "pentagon", "star"])
    color = random.choice(COLORS)
    majority_rot = 0
    majority_fill = color

    # Four: correct shape, rotation, fill
    # Outlier: breaks BOTH rules -- different rotation AND different fill
    outlier_rot = random.choice([90, 135, 180])
    outlier_fill = "white"

    configs = [(majority_rot, majority_fill)] * 4 + [(outlier_rot, outlier_fill)]
    random.shuffle(configs)
    correct_label = chr(65 + configs.index((outlier_rot, outlier_fill)))

    opt_files = []
    for i, (rot, fill) in enumerate(configs):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, rot=rot, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, 28, fill, stroke=color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "odd_one_out",
        "question": "Which figure does NOT belong with the others?",
        "sequence_images": [], "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "Four figures share the same orientation and fill. One figure differs in both rotation and fill -- it breaks two rules simultaneously."
    }

# ─── Generate 75 questions ────────────────────────────────────────────────────

final_plan = [
    # Easy: 30 questions
    (gen_sides_increase, 5),
    (gen_rotation_with_fill, 5),
    (gen_dot_clockwise_in_shape, 5),
    (gen_size_increase_series, 5),
    (gen_shape_mirror, 5),
    (gen_odd_one_out_symmetry, 3),
    (gen_odd_one_out_sides, 2),
    # Medium: 25 questions
    (gen_inner_shape_series, 5),
    (gen_grid_pattern_series, 4),
    (gen_double_shape_series, 5),
    (gen_odd_one_out_inner_shape, 5),
    (gen_odd_one_out_combined, 3),
    (gen_position_series, 3),
    # Hard: 20 questions
    (gen_matrix_shape_rotation, 5),
    (gen_matrix_size_fill, 5),
    (gen_three_rule_series, 3),
    (gen_inner_outer_both_change, 4),
    (gen_matrix_inner_outer, 2),
    (gen_odd_one_out_two_rules, 1),
]

questions = []
qid = 1
for gen_fn, count in final_plan:
    for _ in range(count):
        try:
            q = gen_fn(qid)
            questions.append(q)
            qid += 1
        except Exception as e:
            print(f"Error in {gen_fn.__name__} qid {qid}: {e}")
            qid += 1

with open("data/abstract_bank.json", "w") as f:
    json.dump(questions, f, indent=2)

easy = sum(1 for q in questions if q["difficulty"] == "easy")
medium = sum(1 for q in questions if q["difficulty"] == "medium")
hard = sum(1 for q in questions if q["difficulty"] == "hard")
print(f"Generated {len(questions)} abstract questions")
print(f"Easy: {easy}, Medium: {medium}, Hard: {hard}")
print(f"Images saved to {OUTPUT_DIR}")
