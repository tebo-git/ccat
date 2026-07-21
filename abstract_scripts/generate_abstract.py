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

def add_dots_count(dwg, count, cx, cy, r):
    all_positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
    for i in range(min(count, 5)):
        add_dot(dwg, all_positions[i], cx, cy, r)

def shuffle_with_correct(correct, wrong_list):
    all_opts = [correct] + wrong_list
    random.shuffle(all_opts)
    label = chr(65 + all_opts.index(correct))
    return all_opts, label

def draw_question_mark(dwg):
    dwg.add(dwg.text("?", insert=(32, 65), font_size="45px",
            fill="#94a3b8", font_family="Arial", font_weight="bold"))

COLORS = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
ALL_SHAPES = ["circle", "square", "triangle", "diamond", "pentagon", "hexagon", "star", "cross", "arrow"]

# ─── EASY generators ──────────────────────────────────────────────────────────

def gen_dot_moves_clockwise(qid):
    """Easy: dot moves clockwise. Distractors use adjacent wrong positions."""
    shapes = ["square", "pentagon", "hexagon", "circle"]
    shape = random.choice(shapes)
    positions = ["top-left", "top-right", "bottom-right", "bottom-left"]
    start = random.randint(0, 3)
    r = 28

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        pos = positions[(start + i) % 4]
        def draw(dwg, size, pos=pos):
            draw_shape_element(dwg, shape, 50, 50, r, "white")
            add_dot(dwg, pos, 50, 50, r)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct_pos = positions[(start + 4) % 4]
    # Distractors: adjacent positions and center -- plausible but wrong
    wrong_positions = [
        positions[(start + 3) % 4],  # one step back
        positions[(start + 5) % 4],  # two steps ahead
        "center",
        positions[(start + 2) % 4],  # opposite
    ]
    all_pos, correct_label = shuffle_with_correct(correct_pos, wrong_positions)

    opt_files = []
    for i, pos in enumerate(all_pos):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, pos=pos):
            draw_shape_element(dwg, shape, 50, 50, r, "white")
            add_dot(dwg, pos, 50, 50, r)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"The dot moves clockwise around the corners. After {positions[(start+3)%4]}, it moves to {correct_pos}."
    }

def gen_rotation_series(qid):
    """Easy: shape rotates by fixed step. Distractors are close rotations."""
    shapes = ["triangle", "arrow", "cross", "pentagon", "star", "diamond"]
    shape = random.choice(shapes)
    color = random.choice(COLORS)
    step = random.choice([90, 45])
    rotations = [0, step, step*2, step*3]
    correct_rot = (step * 4) % 360
    r = 28

    seq_files = []
    for i, rot in enumerate(rotations):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, r, color, rotation=rot)
        make_svg(fname, draw)
        seq_files.append(fname)

    # Distractors: nearby rotations that look plausible
    wrong_rots = [
        (correct_rot + step) % 360,      # one step too many
        (correct_rot - step) % 360,      # one step back (last in sequence)
        (correct_rot + step//2) % 360,   # half step off
        (correct_rot + step*2) % 360,    # two steps too many
    ]
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
        "explanation": f"The {shape} rotates {step} degrees clockwise each step. After {step*3} degrees it completes a full cycle."
    }

def gen_dot_count_increases(qid):
    """Easy: dots increase by 1. Distractors are adjacent counts."""
    shapes = ["square", "circle", "pentagon", "hexagon"]
    shape = random.choice(shapes)
    color = random.choice(COLORS)
    counts = [1, 2, 3, 4]
    correct_count = 5
    r = 32

    seq_files = []
    for i, count in enumerate(counts):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, count=count):
            draw_shape_element(dwg, shape, 50, 50, r, "white", stroke=color)
            add_dots_count(dwg, count, 50, 50, r)
        make_svg(fname, draw)
        seq_files.append(fname)

    # Distractors: counts near 5 -- plausible
    wrong_counts = [4, 3, 6, 2]
    all_counts, correct_label = shuffle_with_correct(correct_count, wrong_counts)

    opt_files = []
    for i, count in enumerate(all_counts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, count=count):
            draw_shape_element(dwg, shape, 50, 50, r, "white", stroke=color)
            add_dots_count(dwg, count, 50, 50, r)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "The number of dots increases by one each step. After 4 dots, the next figure has 5."
    }

def gen_alternating_shapes(qid):
    """Easy: two shapes alternate. Distractor uses wrong shape or wrong color."""
    shape_pairs = [
        ("circle", "square"), ("triangle", "diamond"),
        ("pentagon", "hexagon"), ("star", "cross"), ("arrow", "circle")
    ]
    shape_a, shape_b = random.choice(shape_pairs)
    color_a, color_b = random.sample(COLORS, 2)
    r = 28

    seq = [(shape_a, color_a), (shape_b, color_b), (shape_a, color_a), (shape_b, color_b)]
    seq_files = []
    for i, (shape, color) in enumerate(seq):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, shape=shape, color=color):
            draw_shape_element(dwg, shape, 50, 50, r, color)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct = (shape_a, color_a)
    # Distractors: right shape wrong color, wrong shape right color, both wrong
    wrong_opts = [
        (shape_b, color_b),      # last in sequence -- tempting
        (shape_a, color_b),      # right shape wrong color
        (shape_b, color_a),      # wrong shape right color
        (shape_a, COLORS[2] if color_a != COLORS[2] else COLORS[3]),  # right shape different color
    ]
    all_opts, correct_label = shuffle_with_correct(correct, wrong_opts)

    opt_files = []
    for i, (shape, color) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, shape=shape, color=color):
            draw_shape_element(dwg, shape, 50, 50, r, color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"The sequence alternates between a {shape_a} and a {shape_b} with matching colors."
    }

def gen_odd_one_out_shape(qid):
    """Easy: four same shape, one different. Distractor is visually similar shape."""
    similar_groups = [
        (["circle"], ["oval-like shapes"], "diamond"),
        (["square"], ["rectangle-like"], "cross"),
        (["triangle"], ["angular shapes"], "arrow"),
        (["pentagon"], ["polygon shapes"], "hexagon"),
        (["star"], ["pointed shapes"], "cross"),
    ]
    group_shape = random.choice(ALL_SHAPES)
    similar = [s for s in ALL_SHAPES if s != group_shape]
    outlier = random.choice(similar)
    color = random.choice(COLORS)
    r = 28

    shapes_list = [group_shape] * 4 + [outlier]
    random.shuffle(shapes_list)
    correct_label = chr(65 + shapes_list.index(outlier))

    opt_files = []
    for i, shape in enumerate(shapes_list):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, shape=shape):
            draw_shape_element(dwg, shape, 50, 50, r, color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "odd_one_out",
        "question": "Which figure does NOT belong with the others?",
        "sequence_images": [], "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Four figures are {group_shape}s. The {outlier} does not share the same shape."
    }

def gen_odd_one_out_color(qid):
    """Easy: four same color, one different."""
    shape = random.choice(ALL_SHAPES)
    majority_color, outlier_color = random.sample(COLORS, 2)
    r = 28

    all_colors = [majority_color] * 4 + [outlier_color]
    random.shuffle(all_colors)
    correct_label = chr(65 + all_colors.index(outlier_color))

    opt_files = []
    for i, color in enumerate(all_colors):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, color=color):
            draw_shape_element(dwg, shape, 50, 50, r, color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "odd_one_out",
        "question": "Which figure does NOT belong with the others?",
        "sequence_images": [], "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "Four figures share the same color. One figure has a different color and does not belong."
    }

def gen_odd_one_out_size(qid):
    """Easy: four same size, one smaller."""
    shape = random.choice(ALL_SHAPES)
    color = random.choice(COLORS)
    majority_size, outlier_size = 30, 14

    sizes = [majority_size] * 4 + [outlier_size]
    random.shuffle(sizes)
    correct_label = chr(65 + sizes.index(outlier_size))

    opt_files = []
    for i, r in enumerate(sizes):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, r=r):
            draw_shape_element(dwg, shape, 50, 50, r, color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "easy",
        "type": "odd_one_out",
        "question": "Which figure does NOT belong with the others?",
        "sequence_images": [], "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "Four figures are the same size. One figure is significantly smaller."
    }

# ─── MEDIUM generators ────────────────────────────────────────────────────────

def gen_size_and_fill(qid):
    """Medium: grows AND alternates fill. Distractors match one rule not both."""
    shape = random.choice(["circle", "square", "diamond", "pentagon", "hexagon"])
    color = random.choice(COLORS)
    sizes = [12, 20, 28, 36]
    fills = ["white", color, "white", color]

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        r, fill = sizes[i], fills[i]
        def draw(dwg, size, r=r, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct = (44, "white")
    # Distractors: right size wrong fill, right fill wrong size, both slightly off
    wrong_opts = [
        (44, color),    # right size wrong fill -- most tempting trap
        (36, "white"),  # previous size right fill
        (36, color),    # previous size wrong fill
        (44, color),    # duplicate trap -- will be deduplicated by shuffle
    ]
    wrong_opts = list({str(w): w for w in wrong_opts}.values())[:4]
    if len(wrong_opts) < 4:
        wrong_opts.append((28, "white"))
    all_opts, correct_label = shuffle_with_correct(correct, wrong_opts)

    opt_files = []
    for i, (r, fill) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, r=r, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Two rules: the {shape} grows larger each step, AND alternates between empty and filled. Both rules must be satisfied."
    }

def gen_shape_inside_shape(qid):
    """Medium: inner rotates, outer fixed. Distractors use wrong rotation or wrong shape."""
    outers = ["square", "circle", "pentagon", "hexagon"]
    inners = ["triangle", "diamond", "arrow", "star", "cross"]
    outer = random.choice(outers)
    inner = random.choice(inners)
    color = random.choice(COLORS)
    step = 90
    rotations = [0, step, step*2, step*3]
    outer_r, inner_r = 35, 18

    seq_files = []
    for i, rot in enumerate(rotations):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, rot=rot):
            draw_shape_element(dwg, outer, 50, 50, outer_r, "white")
            draw_shape_element(dwg, inner, 50, 50, inner_r, color, rotation=rot)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct_rot = (step * 4) % 360
    # Distractors: one step off, wrong inner shape, wrong outer shape
    wrong_inner = random.choice([s for s in inners if s != inner])
    wrong_rots = [
        (outer, inner, (correct_rot + step) % 360),   # one step too far
        (outer, inner, (correct_rot - step) % 360),   # one step back
        (outer, wrong_inner, correct_rot),             # wrong inner shape right rotation
        (outer, inner, (correct_rot + 45) % 360),     # slightly off rotation
    ]

    all_opts, correct_label = shuffle_with_correct(
        (outer, inner, correct_rot), wrong_rots)

    opt_files = []
    for i, (o, inn, rot) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, o=o, inn=inn, rot=rot):
            draw_shape_element(dwg, o, 50, 50, outer_r, "white")
            draw_shape_element(dwg, inn, 50, 50, inner_r, color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"The outer {outer} stays fixed. The inner {inner} rotates 90 degrees clockwise each step."
    }

def gen_odd_one_out_fill(qid):
    """Medium: four filled, one empty. All same shape -- only fill differs."""
    shape = random.choice(ALL_SHAPES)
    color = random.choice(COLORS)
    r = 28

    fills = [color] * 4 + ["white"]
    random.shuffle(fills)
    correct_label = chr(65 + fills.index("white"))

    opt_files = []
    for i, fill in enumerate(fills):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "odd_one_out",
        "question": "Which figure does NOT belong with the others?",
        "sequence_images": [], "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "Four figures are filled. One figure is empty and does not belong."
    }

def gen_odd_one_out_rotation(qid):
    """Medium: four same rotation, one different. Distractors are close rotations."""
    shape = random.choice(["arrow", "triangle", "cross", "star", "pentagon"])
    color = random.choice(COLORS)
    majority_rot = random.choice([0, 90, 180, 270])
    outlier_rot = random.choice([r for r in [0, 45, 90, 135, 180, 225, 270, 315] if r != majority_rot])

    rots = [majority_rot] * 4 + [outlier_rot]
    random.shuffle(rots)
    correct_label = chr(65 + rots.index(outlier_rot))

    opt_files = []
    for i, rot in enumerate(rots):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, 28, color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "odd_one_out",
        "question": "Which figure does NOT belong with the others?",
        "sequence_images": [], "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Four {shape}s face the same direction. One is rotated differently."
    }

def gen_dot_moves_plus_fill(qid):
    """Medium: dot moves clockwise AND fill alternates. Two rules simultaneously."""
    shape = "square"
    positions = ["top-left", "top-right", "bottom-right", "bottom-left"]
    start = random.randint(0, 3)
    color = random.choice(COLORS)
    fills = ["white", color, "white", color]
    r = 28

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        pos = positions[(start + i) % 4]
        fill = fills[i]
        def draw(dwg, size, pos=pos, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color)
            add_dot(dwg, pos, 50, 50, r, fill="#ffffff" if fill != "white" else "#1e293b")
        make_svg(fname, draw)
        seq_files.append(fname)

    correct_pos = positions[(start + 4) % 4]
    correct_fill = "white"  # fills[4] would be white

    # Distractors: right pos wrong fill, wrong pos right fill, both wrong
    wrong_opts = [
        (positions[(start+3) % 4], correct_fill),   # wrong pos right fill
        (correct_pos, color),                         # right pos wrong fill -- TRAP
        (positions[(start+5) % 4], color),           # both wrong
        (positions[(start+2) % 4], correct_fill),    # wrong pos right fill
    ]
    all_opts, correct_label = shuffle_with_correct(
        (correct_pos, correct_fill), wrong_opts)

    opt_files = []
    for i, (pos, fill) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, pos=pos, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color)
            add_dot(dwg, pos, 50, 50, r, fill="#ffffff" if fill != "white" else "#1e293b")
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": "Two rules: the dot moves clockwise AND the background alternates between empty and filled. Both must be correct."
    }

# ─── HARD generators ─────────────────────────────────────────────────────────

def gen_rotation_plus_fill(qid):
    """Hard: rotates AND fill alternates. Distractors satisfy only one rule."""
    shape = random.choice(["triangle", "arrow", "diamond", "star", "cross"])
    color = random.choice(COLORS)
    rotations = [0, 90, 180, 270]
    fills = [color, "white", color, "white"]
    r = 28

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        rot, fill = rotations[i], fills[i]
        def draw(dwg, size, rot=rot, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color, rotation=rot)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct = (360 % 360, color)  # 0 degrees and filled
    # Distractors: each satisfies only ONE rule
    wrong_opts = [
        (0, "white"),    # right rotation wrong fill -- MAIN TRAP
        (90, color),     # wrong rotation right fill
        (270, color),    # last rotation right fill
        (0, "#94a3b8"),  # right rotation wrong color
    ]
    all_opts, correct_label = shuffle_with_correct(correct, wrong_opts)

    opt_files = []
    for i, (rot, fill) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, rot=rot, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Two rules operate simultaneously: the {shape} rotates 90 degrees AND alternates filled/empty. After 270 degrees empty, the next must be 0 degrees and filled."
    }

def gen_size_plus_rotation(qid):
    """Hard: grows AND rotates. Distractors match size OR rotation but not both."""
    shape = random.choice(["triangle", "arrow", "star", "cross", "pentagon"])
    color = random.choice(COLORS)
    sizes = [14, 22, 30, 38]
    rotations = [0, 90, 180, 270]

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        r, rot = sizes[i], rotations[i]
        def draw(dwg, size, r=r, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, r, color, rotation=rot)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct = (46, 0)  # largest and back to 0
    wrong_opts = [
        (46, 270),  # right size wrong rotation -- TRAP
        (38, 0),    # previous size right rotation
        (46, 90),   # right size wrong rotation
        (38, 270),  # previous size previous rotation
    ]
    all_opts, correct_label = shuffle_with_correct(correct, wrong_opts)

    opt_files = []
    for i, (r, rot) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, r=r, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, r, color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Two rules: the {shape} grows larger each step AND rotates 90 degrees. The next must be the largest size AND back to 0 degrees."
    }

def gen_matrix_3x3_shape(qid):
    """Hard: 3x3 matrix with shape and fill rules. Distractors match one axis not both."""
    shapes = random.sample(["circle", "triangle", "square", "diamond", "pentagon"], 3)
    color = random.choice(COLORS)
    fills = ["white", "#94a3b8", color]

    cells = []
    for row in range(3):
        for col in range(3):
            cells.append((shapes[col], fills[row]))

    missing_idx = random.randint(0, 8)
    correct_shape, correct_fill = cells[missing_idx]

    matrix_files = []
    for i, (shape, fill) in enumerate(cells):
        if i == missing_idx:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}_missing.svg"
            def draw(dwg, size):
                draw_question_mark(dwg)
        else:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}.svg"
            def draw(dwg, size, shape=shape, fill=fill):
                draw_shape_element(dwg, shape, 50, 50, 28, fill, stroke=color)
        make_svg(fname, draw)
        matrix_files.append(fname)

    # Distractors: right shape wrong fill, wrong shape right fill, both slightly off
    other_shapes = [s for s in shapes if s != correct_shape]
    other_fills = [f for f in fills if f != correct_fill]
    wrong_opts = [
        (correct_shape, other_fills[0]),    # right shape wrong fill -- TRAP
        (other_shapes[0], correct_fill),    # wrong shape right fill -- TRAP
        (other_shapes[1], correct_fill),    # wrong shape right fill
        (correct_shape, other_fills[1] if len(other_fills) > 1 else other_fills[0]),
    ]
    all_opts, correct_label = shuffle_with_correct(
        (correct_shape, correct_fill), wrong_opts)

    opt_files = []
    for i, (shape, fill) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, shape=shape, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, 28, fill, stroke=color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "matrix_3x3",
        "question": "Which figure completes the 3x3 matrix?",
        "sequence_images": matrix_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Each column uses a different shape ({', '.join(shapes)}). Each row uses a different fill. The missing piece must satisfy both rules: a {correct_fill} {correct_shape}."
    }

def gen_matrix_3x3_rotation(qid):
    """Hard: 3x3 matrix with rotation rules on both axes."""
    shape = random.choice(["triangle", "arrow", "cross", "star", "pentagon"])
    color = random.choice(COLORS)
    row_rots = [[0, 90, 180], [90, 180, 270], [180, 270, 0]]

    cells = []
    for row in range(3):
        for col in range(3):
            cells.append(row_rots[row][col])

    missing_idx = random.randint(0, 8)
    correct_rot = cells[missing_idx]

    matrix_files = []
    for i, rot in enumerate(cells):
        if i == missing_idx:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}_missing.svg"
            def draw(dwg, size):
                draw_question_mark(dwg)
        else:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}.svg"
            def draw(dwg, size, rot=rot):
                draw_shape_element(dwg, shape, 50, 50, 28, color, rotation=rot)
        make_svg(fname, draw)
        matrix_files.append(fname)

    # Distractors: adjacent rotations -- hard to distinguish quickly
    wrong_rots = [
        (correct_rot + 90) % 360,   # one step off
        (correct_rot - 90) % 360,   # one step back
        (correct_rot + 45) % 360,   # half step -- subtle
        (correct_rot + 180) % 360,  # opposite -- obvious but included
    ]
    all_rots, correct_label = shuffle_with_correct(correct_rot, wrong_rots)

    opt_files = []
    for i, rot in enumerate(all_rots):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, 28, color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "matrix_3x3",
        "question": "Which figure completes the 3x3 matrix?",
        "sequence_images": matrix_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Each row increases rotation by 90 degrees. Each column also increases by 90 degrees. Track both axes to find the missing {correct_rot}-degree {shape}."
    }

def gen_three_rule_series(qid):
    """Hard: shape changes AND rotates AND fill changes -- three simultaneous rules."""
    shape_seq = ["triangle", "square", "pentagon", "triangle"]
    color = random.choice(COLORS)
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

    correct = ("square", 0, color)
    wrong_opts = [
        ("square", 270, color),      # right shape right fill wrong rotation
        ("triangle", 0, color),      # wrong shape right rotation right fill
        ("square", 0, "white"),      # right shape right rotation wrong fill
        ("pentagon", 0, color),      # wrong shape right rotation right fill
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
        "explanation": "Three rules: shape cycles (triangle→square→pentagon→triangle→square), rotation increases 90 degrees, and fill alternates. All three must match."
    }

# ─── Generate 75 questions ────────────────────────────────────────────────────

final_plan = [
    # Easy: 30 questions
    (gen_dot_moves_clockwise, 6),
    (gen_rotation_series, 5),
    (gen_dot_count_increases, 4),
    (gen_alternating_shapes, 5),
    (gen_odd_one_out_shape, 4),
    (gen_odd_one_out_color, 3),
    (gen_odd_one_out_size, 3),
    # Medium: 25 questions
    (gen_size_and_fill, 5),
    (gen_shape_inside_shape, 5),
    (gen_odd_one_out_fill, 5),
    (gen_odd_one_out_rotation, 5),
    (gen_dot_moves_plus_fill, 5),
    # Hard: 20 questions
    (gen_matrix_3x3_shape, 6),
    (gen_matrix_3x3_rotation, 6),
    (gen_rotation_plus_fill, 4),
    (gen_size_plus_rotation, 2),
    (gen_three_rule_series, 2),
]

questions = []
qid = 1
for gen_fn, count in final_plan:
    for _ in range(count):
        q = gen_fn(qid)
        questions.append(q)
        qid += 1

with open("data/abstract_bank.json", "w") as f:
    json.dump(questions, f, indent=2)

easy = sum(1 for q in questions if q["difficulty"] == "easy")
medium = sum(1 for q in questions if q["difficulty"] == "medium")
hard = sum(1 for q in questions if q["difficulty"] == "hard")
print(f"Generated {len(questions)} abstract questions")
print(f"Easy: {easy}, Medium: {medium}, Hard: {hard}")
print(f"Images saved to {OUTPUT_DIR}")