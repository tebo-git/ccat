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

def draw_shape_element(dwg, shape, cx, cy, r, fill, stroke="#1e293b", rotation=0):
    if shape == "circle":
        dwg.add(dwg.circle(center=(cx,cy), r=r, fill=fill, stroke=stroke, stroke_width=2))
    elif shape == "square":
        el = dwg.rect(insert=(cx-r, cy-r), size=(r*2, r*2), fill=fill, stroke=stroke, stroke_width=2)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "triangle":
        pts = [(cx, cy-r), (cx+r, cy+r), (cx-r, cy+r)]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=2)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "pentagon":
        pts = [(cx + r*math.cos(math.radians(90 + 72*i)),
                cy - r*math.sin(math.radians(90 + 72*i))) for i in range(5)]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=2)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "hexagon":
        pts = [(cx + r*math.cos(math.radians(60*i)),
                cy + r*math.sin(math.radians(60*i))) for i in range(6)]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=2)
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
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=2)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "diamond":
        pts = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=2)
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
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=2)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)
    elif shape == "star":
        outer, inner = r, r // 2
        pts = []
        for i in range(10):
            angle = math.radians(90 + i * 36)
            rad = outer if i % 2 == 0 else inner
            pts.append((cx + rad * math.cos(angle), cy - rad * math.sin(angle)))
        el = dwg.polygon(points=pts, fill=fill, stroke=stroke, stroke_width=2)
        el["transform"] = f"rotate({rotation},{cx},{cy})"
        dwg.add(el)

def add_dot(dwg, position, cx, cy, r, fill="#1e293b"):
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
    dwg.add(dwg.circle(center=(dx, dy), r=4, fill=fill))

def add_dots_count(dwg, count, cx, cy, r):
    all_positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
    for i in range(min(count, 5)):
        add_dot(dwg, all_positions[i], cx, cy, r)

def shuffle_with_correct(correct, wrong_list):
    all_opts = [correct] + wrong_list
    random.shuffle(all_opts)
    label = chr(65 + all_opts.index(correct))
    return all_opts, label

# ─── Question generators ──────────────────────────────────────────────────────

def gen_dot_moves_clockwise(qid, shape="square"):
    positions = ["top-left", "top-right", "bottom-right", "bottom-left"]
    start = random.randint(0, 3)
    r = 28

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        pos = positions[(start + i) % 4]
        def draw(dwg, size, pos=pos, shape=shape, r=r):
            draw_shape_element(dwg, shape, 50, 50, r, "white")
            add_dot(dwg, pos, 50, 50, r)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct_pos = positions[(start + 4) % 4]
    wrong_positions = [p for p in positions if p != correct_pos] + ["center"]
    wrong_positions = wrong_positions[:4]

    all_pos, correct_label = shuffle_with_correct(correct_pos, wrong_positions)

    opt_files = []
    for i, pos in enumerate(all_pos):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, pos=pos, shape=shape, r=r):
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
        "explanation": f"The dot moves clockwise around the corners of the {shape}. After bottom-left, it returns to top-left."
    }

def gen_rotation_series(qid):
    shapes = ["triangle", "arrow", "cross", "pentagon", "star", "diamond"]
    shape = random.choice(shapes)
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)
    step = random.choice([45, 90])
    rotations = [0, step, step*2, step*3]
    correct_rot = step * 4
    r = 28

    seq_files = []
    for i, rot in enumerate(rotations):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, r, color, rotation=rot)
        make_svg(fname, draw)
        seq_files.append(fname)

    wrong_rots = [step, step*2, step*3, step + 20]
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
        "explanation": f"The {shape} rotates {step} degrees clockwise each step. After {step*3} degrees, it returns to its original position."
    }

def gen_size_and_fill(qid):
    shapes = ["circle", "square", "diamond", "pentagon", "hexagon"]
    shape = random.choice(shapes)
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)
    sizes = [12, 20, 28, 36]
    fills = ["white", color, "white", color]

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        r, fill = sizes[i], fills[i]
        def draw(dwg, size, r=r, fill=fill, shape=shape, color=color):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct = (44, "white")
    wrong_opts = [(44, color), (36, "white"), (36, color), (28, "white")]
    all_opts, correct_label = shuffle_with_correct(correct, wrong_opts)

    opt_files = []
    for i, (r, fill) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, r=r, fill=fill, shape=shape, color=color):
            draw_shape_element(dwg, shape, 50, 50, r, fill, stroke=color)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"The {shape} grows larger each step while alternating between empty and filled."
    }

def gen_shape_inside_shape(qid):
    outers = ["square", "circle", "pentagon", "hexagon"]
    inners = ["triangle", "diamond", "arrow", "star", "cross"]
    outer = random.choice(outers)
    inner = random.choice(inners)
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)
    step = random.choice([90, 45])
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

    correct_rot = step * 4
    wrong_rots = [step, step*2, step*3, step + 30]
    all_rots, correct_label = shuffle_with_correct(correct_rot, wrong_rots)

    opt_files = []
    for i, rot in enumerate(all_rots):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, rot=rot):
            draw_shape_element(dwg, outer, 50, 50, outer_r, "white")
            draw_shape_element(dwg, inner, 50, 50, inner_r, color, rotation=rot)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "medium",
        "type": "next_in_series",
        "question": "Which figure comes next in the series?",
        "sequence_images": seq_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"The outer {outer} stays fixed while the inner {inner} rotates {step} degrees clockwise each step."
    }

def gen_dot_count_increases(qid):
    shapes = ["square", "circle", "pentagon", "hexagon"]
    shape = random.choice(shapes)
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)
    counts = [1, 2, 3, 4]
    r = 32

    seq_files = []
    for i, count in enumerate(counts):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        def draw(dwg, size, count=count):
            draw_shape_element(dwg, shape, 50, 50, r, "white", stroke=color)
            add_dots_count(dwg, count, 50, 50, r)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct_count = 5
    wrong_counts = [1, 2, 3, 4]
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
        "explanation": "The number of dots inside the shape increases by one each step. After 4 dots, the next figure has 5 dots."
    }

def gen_alternating_shapes(qid):
    shape_pairs = [
        ("circle", "square"), ("triangle", "diamond"),
        ("pentagon", "hexagon"), ("star", "cross"),
        ("arrow", "circle"), ("diamond", "triangle")
    ]
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    shape_a, shape_b = random.choice(shape_pairs)
    color_a = random.choice(colors)
    color_b = random.choice([c for c in colors if c != color_a])
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
    wrong_opts = [
        (shape_b, color_b),
        (shape_a, color_b),
        (shape_b, color_a),
        (shape_a, "#94a3b8")
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
        "explanation": f"The sequence alternates between a {shape_a} and a {shape_b}. After the {shape_b}, the next figure must be a {shape_a}."
    }

def gen_odd_one_out_shape(qid):
    all_shapes = ["circle", "square", "triangle", "diamond", "pentagon", "hexagon", "star", "cross", "arrow"]
    group_shape = random.choice(all_shapes)
    outlier = random.choice([s for s in all_shapes if s != group_shape])
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)
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
        "explanation": f"Four figures are {group_shape}s. The {outlier} does not belong."
    }

def gen_odd_one_out_fill(qid):
    shapes = ["circle", "square", "triangle", "pentagon", "diamond", "hexagon"]
    shape = random.choice(shapes)
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)
    r = 28

    majority_fill = color
    outlier_fill = "white"
    fills = [majority_fill] * 4 + [outlier_fill]
    random.shuffle(fills)
    correct_label = chr(65 + fills.index(outlier_fill))

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
        "explanation": "Four figures are filled and one is empty. The empty figure is the odd one out."
    }

def gen_odd_one_out_size(qid):
    shapes = ["circle", "square", "pentagon", "diamond", "triangle"]
    shape = random.choice(shapes)
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)

    majority_size = 28
    outlier_size = 14
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
        "explanation": "Four figures are the same size. One figure is significantly smaller and does not belong."
    }

def gen_odd_one_out_rotation(qid):
    shapes = ["arrow", "triangle", "cross", "star", "pentagon"]
    shape = random.choice(shapes)
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)

    majority_rot = 0
    outlier_rot = random.choice([45, 90, 135, 180])
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
        "explanation": f"Four figures face the same direction. One {shape} is rotated differently and does not belong."
    }

def gen_odd_one_out_color(qid):
    shapes = ["circle", "square", "triangle", "pentagon", "diamond"]
    shape = random.choice(shapes)
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    majority_color = random.choice(colors)
    outlier_color = random.choice([c for c in colors if c != majority_color])

    all_colors = [majority_color] * 4 + [outlier_color]
    random.shuffle(all_colors)
    correct_label = chr(65 + all_colors.index(outlier_color))

    opt_files = []
    for i, color in enumerate(all_colors):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, color=color):
            draw_shape_element(dwg, shape, 50, 50, 28, color)
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

def gen_matrix_3x3_shape(qid):
    shapes = random.sample(["circle", "triangle", "square", "diamond", "pentagon"], 3)
    colors = ["#2563eb", "#dc2626", "#16a34a"]
    fills = ["white", "#94a3b8", colors[0]]

    cells = []
    for row in range(3):
        for col in range(3):
            cells.append((shapes[col], fills[row]))

    missing_idx = random.randint(6, 8)
    correct_shape, correct_fill = cells[missing_idx]

    matrix_files = []
    for i, (shape, fill) in enumerate(cells):
        if i == missing_idx:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}_missing.svg"
            def draw(dwg, size):
                dwg.add(dwg.text("?", insert=(32, 65), font_size="45px",
                        fill="#94a3b8", font_family="Arial", font_weight="bold"))
        else:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}.svg"
            def draw(dwg, size, shape=shape, fill=fill):
                draw_shape_element(dwg, shape, 50, 50, 28, fill)
        make_svg(fname, draw)
        matrix_files.append(fname)

    wrong_opts = [
        (correct_shape, "#94a3b8"),
        (shapes[(shapes.index(correct_shape)+1) % 3], correct_fill),
        (shapes[(shapes.index(correct_shape)+2) % 3], correct_fill),
        (correct_shape, "white"),
    ]
    all_opts, correct_label = shuffle_with_correct((correct_shape, correct_fill), wrong_opts)

    opt_files = []
    for i, (shape, fill) in enumerate(all_opts):
        fname = f"{OUTPUT_DIR}/q{qid}_opt{chr(65+i)}.svg"
        def draw(dwg, size, shape=shape, fill=fill):
            draw_shape_element(dwg, shape, 50, 50, 28, fill)
        make_svg(fname, draw)
        opt_files.append(fname)

    return {
        "id": qid, "category": "abstract", "difficulty": "hard",
        "type": "matrix_3x3",
        "question": "Which figure completes the 3x3 matrix?",
        "sequence_images": matrix_files, "option_images": opt_files,
        "correct_answer": correct_label,
        "explanation": f"Each row uses a different fill pattern. Each column uses a different shape. The missing piece must be a {correct_fill} {correct_shape}."
    }

def gen_matrix_3x3_rotation(qid):
    shape = random.choice(["triangle", "arrow", "cross", "star", "pentagon"])
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)
    rotations_per_row = [[0, 90, 180], [90, 180, 270], [180, 270, 360]]

    cells = []
    for row in range(3):
        for col in range(3):
            cells.append(rotations_per_row[row][col])

    missing_idx = random.randint(6, 8)
    correct_rot = cells[missing_idx]

    matrix_files = []
    for i, rot in enumerate(cells):
        if i == missing_idx:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}_missing.svg"
            def draw(dwg, size):
                dwg.add(dwg.text("?", insert=(32, 65), font_size="45px",
                        fill="#94a3b8", font_family="Arial", font_weight="bold"))
        else:
            fname = f"{OUTPUT_DIR}/q{qid}_cell{i+1}.svg"
            def draw(dwg, size, rot=rot):
                draw_shape_element(dwg, shape, 50, 50, 28, color, rotation=rot)
        make_svg(fname, draw)
        matrix_files.append(fname)

    wrong_rots = [correct_rot + 45, correct_rot + 90, correct_rot - 45, correct_rot - 90]
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
        "explanation": f"Each row increases rotation by 90 degrees. Each column also increases by 90 degrees. The missing {shape} must be at {correct_rot} degrees."
    }

def gen_rotation_plus_fill(qid):
    shape = random.choice(["triangle", "arrow", "diamond", "star", "cross"])
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)
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

    correct = (360, color)
    wrong_opts = [(360, "white"), (270, color), (90, color), (180, "white")]
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
        "explanation": f"The {shape} rotates 90 degrees AND alternates between filled and empty. The next must be filled and back to 0 degrees."
    }

def gen_size_plus_rotation(qid):
    shape = random.choice(["triangle", "arrow", "star", "cross", "pentagon"])
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]
    color = random.choice(colors)
    sizes = [14, 22, 30, 38]
    rotations = [0, 90, 180, 270]
    r_base = 28

    seq_files = []
    for i in range(4):
        fname = f"{OUTPUT_DIR}/q{qid}_seq{i+1}.svg"
        r, rot = sizes[i], rotations[i]
        def draw(dwg, size, r=r, rot=rot):
            draw_shape_element(dwg, shape, 50, 50, r, color, rotation=rot)
        make_svg(fname, draw)
        seq_files.append(fname)

    correct = (46, 360)
    wrong_opts = [(46, 270), (38, 360), (38, 270), (46, 90)]
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
        "explanation": f"The {shape} grows larger AND rotates 90 degrees each step. The next must be largest and back to 0 degrees."
    }

# ─── Generate 75 questions ────────────────────────────────────────────────────

generators = [
    # Easy -- 25 questions
    (gen_dot_moves_clockwise, 10),
    (gen_rotation_series, 5),
    (gen_dot_count_increases, 5),
    (gen_alternating_shapes, 5),
    (gen_odd_one_out_shape, 3),
    (gen_odd_one_out_color, 3),
    (gen_odd_one_out_size, 4),  # total 35 -- adjusted below

    # Medium -- 25 questions
    (gen_size_and_fill, 8),
    (gen_shape_inside_shape, 8),
    (gen_odd_one_out_fill, 5),
    (gen_odd_one_out_rotation, 4),  # total 25

    # Hard -- 15 questions
    (gen_matrix_3x3_shape, 5),
    (gen_matrix_3x3_rotation, 5),
    (gen_rotation_plus_fill, 3),
    (gen_size_plus_rotation, 2),  # total 15 -- adjusted below
]

# Build generation plan with exact counts
plan = [
    (gen_dot_moves_clockwise, 8),
    (gen_rotation_series, 5),
    (gen_dot_count_increases, 4),
    (gen_alternating_shapes, 4),
    (gen_odd_one_out_shape, 3),
    (gen_odd_one_out_color, 3),
    (gen_odd_one_out_size, 3),     # easy total: 30
    (gen_size_and_fill, 7),
    (gen_shape_inside_shape, 7),
    (gen_odd_one_out_fill, 5),
    (gen_odd_one_out_rotation, 6), # medium total: 25
    (gen_matrix_3x3_shape, 6),
    (gen_matrix_3x3_rotation, 6),
    (gen_rotation_plus_fill, 2),
    (gen_size_plus_rotation, 1),   # hard total: 15 -- wait, 6+6+2+1=15 but we need 20
]

# Final plan: 30 easy + 25 medium + 20 hard = 75
final_plan = [
    (gen_dot_moves_clockwise, 8),
    (gen_rotation_series, 5),
    (gen_dot_count_increases, 4),
    (gen_alternating_shapes, 4),
    (gen_odd_one_out_shape, 4),
    (gen_odd_one_out_color, 3),
    (gen_odd_one_out_size, 2),      # easy: 30
    (gen_size_and_fill, 6),
    (gen_shape_inside_shape, 6),
    (gen_odd_one_out_fill, 5),
    (gen_odd_one_out_rotation, 4),
    (gen_odd_one_out_color, 4),     # medium: 25
    (gen_matrix_3x3_shape, 7),
    (gen_matrix_3x3_rotation, 7),
    (gen_rotation_plus_fill, 3),
    (gen_size_plus_rotation, 3),    # hard: 20
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

print(f"Generated {len(questions)} abstract questions")
easy = sum(1 for q in questions if q["difficulty"] == "easy")
medium = sum(1 for q in questions if q["difficulty"] == "medium")
hard = sum(1 for q in questions if q["difficulty"] == "hard")
print(f"Easy: {easy}, Medium: {medium}, Hard: {hard}")
print(f"Images saved to {OUTPUT_DIR}")