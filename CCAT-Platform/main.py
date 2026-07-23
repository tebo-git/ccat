import json
import random
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import resend
from pydantic import BaseModel
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.platypus import KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics import renderPDF
import io
import base64
import csv
from datetime import datetime
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import requests

resend.api_key = "re_W6MpVkyn_4Kn45VhNfcsYkAysj7SNmp5o"
GUMROAD_ACCESS_TOKEN = "0fcCjaOQzZJKG7q4ej-JSAOCV5KUcjMVWCieUydpznA"
GUMROAD_PRODUCT_ID = "QTXdEOZxWcOA4N1XVYJPbg=="



#asss

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory="data/abstract_images"), name="images")

with open("data/verbal_bank.json") as f:
    verbal_questions = json.load(f)

with open("data/numerical_bank.json") as f:
    numerical_questions = json.load(f)

with open("data/abstract_bank.json") as f:
    abstract_questions = json.load(f)

for q in verbal_questions:
    q["uid"] = f"v-{q['id']}"

for q in numerical_questions:
    q["uid"] = f"n-{q['id']}"

for q in abstract_questions:
    q["uid"] = f"a-{q['id']}"
    q["sequence_images"] = [
        f"/images/{p.split('/')[-1]}" for p in q["sequence_images"]
    ]
    q["option_images"] = [
        f"/images/{p.split('/')[-1]}" for p in q["option_images"]
    ]

all_questions = verbal_questions + numerical_questions + abstract_questions

@app.get("/")
def root():
    return {"message": "CCAT Platform API is running"}

@app.get("/api/test")
def get_test(category: str = Query(default="mixed"), 
             count: int = Query(default=50),
             test_num: int = Query(default=1)):
    
    def get_pool_for_test(questions, test_num):
        n = len(questions)
        chunk = n // 3
        if test_num == 1:
            return questions[:chunk]
        elif test_num == 2:
            return questions[chunk:chunk*2]
        else:
            return questions[chunk*2:]

    if category == "verbal":
        pool = get_pool_for_test(verbal_questions, test_num)
    elif category == "numerical":
        pool = get_pool_for_test(numerical_questions, test_num)
    elif category == "abstract":
        pool = get_pool_for_test(abstract_questions, test_num)
    else:
        v_pool = get_pool_for_test(verbal_questions, test_num)
        n_pool = get_pool_for_test(numerical_questions, test_num)
        a_pool = get_pool_for_test(abstract_questions, test_num)
        pool = v_pool + n_pool + a_pool

    count = min(count, len(pool))
    questions_sample = random.sample(pool, count)
    return {"count": len(questions_sample), "questions": questions_sample}




class ResultItem(BaseModel):
    question: str
    category: str
    selected: Optional[str]
    correct_answer: str
    is_correct: bool
    explanation: Optional[str] = ""


class EmailRequest(BaseModel):
    email: str
    score: int
    total: int
    percentage: int
    results: List[ResultItem]





# ─── Brand colors ────────────────────────────────────────────────────────────
BLUE        = colors.HexColor("#2563eb")
BLUE_LIGHT  = colors.HexColor("#eff6ff")
BLUE_DARK   = colors.HexColor("#1e40af")
SLATE_900   = colors.HexColor("#0f172a")
SLATE_700   = colors.HexColor("#334155")
SLATE_500   = colors.HexColor("#64748b")
SLATE_200   = colors.HexColor("#e2e8f0")
SLATE_50    = colors.HexColor("#f8fafc")
EMERALD     = colors.HexColor("#16a34a")
EMERALD_BG  = colors.HexColor("#f0fdf4")
RED         = colors.HexColor("#dc2626")
RED_BG      = colors.HexColor("#fef2f2")
AMBER       = colors.HexColor("#d97706")
AMBER_BG    = colors.HexColor("#fffbeb")
WHITE       = colors.white

def generate_pdf_report(req: "EmailRequest") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    W = A4[0] - 40*mm  # usable width

    # ─── Styles ───────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    def style(name, **kw):
        s = ParagraphStyle(name, **kw)
        return s

    S_TITLE = style("Title",
        fontSize=26, leading=32, textColor=WHITE,
        fontName="Helvetica-Bold", alignment=TA_CENTER)

    S_SUBTITLE = style("Subtitle",
        fontSize=11, leading=14, textColor=colors.HexColor("#bfdbfe"),
        fontName="Helvetica", alignment=TA_CENTER)

    S_SECTION = style("Section",
        fontSize=13, leading=16, textColor=SLATE_900,
        fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=4)

    S_BODY = style("Body",
        fontSize=9, leading=13, textColor=SLATE_700,
        fontName="Helvetica")

    S_SMALL = style("Small",
        fontSize=8, leading=11, textColor=SLATE_500,
        fontName="Helvetica")

    S_LABEL = style("Label",
        fontSize=8, leading=10, textColor=SLATE_500,
        fontName="Helvetica", alignment=TA_CENTER)

    S_BIG_NUM = style("BigNum",
        fontSize=28, leading=32, textColor=BLUE,
        fontName="Helvetica-Bold", alignment=TA_CENTER)

    S_WHITE_BOLD = style("WhiteBold",
        fontSize=10, leading=13, textColor=WHITE,
        fontName="Helvetica-Bold")

    S_TIP_TITLE = style("TipTitle",
        fontSize=9, leading=12, textColor=BLUE_DARK,
        fontName="Helvetica-Bold")

    S_TIP_BODY = style("TipBody",
        fontSize=8, leading=11, textColor=SLATE_700,
        fontName="Helvetica")

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def spacer(h=4):
        return Spacer(1, h*mm)

    def rule(color=SLATE_200, thickness=0.5):
        return HRFlowable(width="100%", thickness=thickness,
                          color=color, spaceAfter=3*mm, spaceBefore=3*mm)

    def score_bar(label, correct, total, color):
        pct = correct / total if total else 0
        bar_w = W * 0.55
        filled = bar_w * pct

        d = Drawing(bar_w, 10)
        d.add(Rect(0, 2, bar_w, 6, rx=3, ry=3,
                   fillColor=SLATE_200, strokeColor=None))
        if filled > 0:
            d.add(Rect(0, 2, filled, 6, rx=3, ry=3,
                       fillColor=color, strokeColor=None))

        row = [
            Paragraph(label, S_BODY),
            d,
            Paragraph(f"<b>{correct}/{total}</b>", S_BODY),
            Paragraph(f"<b>{int(pct*100)}%</b>",
                      style("pct", fontSize=9, leading=13,
                            fontName="Helvetica-Bold",
                            textColor=color, alignment=TA_RIGHT)),
        ]
        t = Table([row], colWidths=[W*0.22, W*0.45, W*0.13, W*0.13],
                  rowHeights=[10*mm])
        t.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ("TOPPADDING", (0,0), (-1,-1), 2),
        ]))
        return t

    def colored_card(content_rows, bg=BLUE_LIGHT, radius=4):
        t = Table(content_rows, colWidths=[W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), bg),
            ("ROUNDEDCORNERS", [radius]),
            ("LEFTPADDING", (0,0), (-1,-1), 4*mm),
            ("RIGHTPADDING", (0,0), (-1,-1), 4*mm),
            ("TOPPADDING", (0,0), (-1,-1), 3*mm),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3*mm),
        ]))
        return t

    # ─── Compute analytics ────────────────────────────────────────────────────

    total = len(req.results)
    correct_count = sum(1 for r in req.results if r.is_correct)
    incorrect_count = sum(1 for r in req.results if r.selected and not r.is_correct)
    unanswered_count = total - correct_count - incorrect_count
    pct = req.percentage

    # By category
    cats = {"verbal": [], "numerical": [], "abstract": []}
    for r in req.results:
        cat = r.category if r.category in cats else "verbal"
        cats[cat].append(r)

    def cat_score(cat):
        qs = cats[cat]
        c = sum(1 for r in qs if r.is_correct)
        return c, len(qs)

    v_c, v_t = cat_score("verbal")
    n_c, n_t = cat_score("numerical")
    a_c, a_t = cat_score("abstract")

    # By difficulty
    diff_map = {"easy": [], "medium": [], "hard": []}
    for r in req.results:
        # difficulty not in ResultItem -- derive from category counts
        pass

    # Wrong answer patterns
    wrong = [r for r in req.results if r.selected and not r.is_correct]
    verbal_wrong = [r for r in wrong if r.category == "verbal"]
    numerical_wrong = [r for r in wrong if r.category == "numerical"]
    abstract_wrong = [r for r in wrong if r.category == "abstract"]

    # Percentile estimate
    if pct >= 90: percentile = "top 10%"
    elif pct >= 80: percentile = "top 20%"
    elif pct >= 70: percentile = "top 30%"
    elif pct >= 60: percentile = "top 40%"
    elif pct >= 48: percentile = "above average"
    else: percentile = "below average"

    # Weakest section
    scores = {}
    if v_t: scores["Verbal"] = v_c/v_t
    if n_t: scores["Numerical"] = n_c/n_t
    if a_t: scores["Abstract"] = a_c/a_t
    weakest = min(scores, key=scores.get) if scores else "Verbal"
    strongest = max(scores, key=scores.get) if scores else "Verbal"

    # Improvement tips per section
    tips = {
        "Verbal": [
            ("Analogies", "Focus on the relationship between word pairs -- function, part-to-whole, or degree of intensity."),
            ("Syllogisms", "Draw Venn diagrams mentally. Ask: does the conclusion HAVE to be true or just could be true?"),
            ("Odd One Out", "Look for the category that unites four words and find the one that breaks it."),
        ],
        "Numerical": [
            ("Sequences", "Always check differences between terms first, then ratios, then combined rules."),
            ("Percentages", "Remember: to reverse a percentage increase, divide by (1 + rate), not subtract the rate."),
            ("Ratios", "Find the value of one part first, then multiply. Never cross-multiply blindly."),
        ],
        "Abstract": [
            ("Next in Series", "Look for one rule at a time -- rotation, size, fill, position. Hard questions combine two or three."),
            ("Odd One Out", "Compare each figure to all others. The outlier breaks exactly one rule the others share."),
            ("3x3 Matrix", "Check rows AND columns independently. The answer must satisfy both axes simultaneously."),
        ],
    }

    # ─── Build story ──────────────────────────────────────────────────────────
    story = []

    # ── HEADER BANNER ─────────────────────────────────────────────────────────
    header_data = [
        [Paragraph("CCAT Practice Test", S_TITLE)],
        [Paragraph("Performance Report", S_SUBTITLE)],
    ]
    header = Table(header_data, colWidths=[W])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BLUE),
        ("ROUNDEDCORNERS", [6]),
        ("TOPPADDING", (0,0), (-1,-1), 6*mm),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6*mm),
        ("LEFTPADDING", (0,0), (-1,-1), 6*mm),
        ("RIGHTPADDING", (0,0), (-1,-1), 6*mm),
    ]))
    story.append(header)
    story.append(spacer(6))

    # ── SCORE SUMMARY CARDS ───────────────────────────────────────────────────
    def mini_card(value, label, bg, text_color):
        d = [
            [Paragraph(str(value), style("v", fontSize=22, leading=26,
                        fontName="Helvetica-Bold", textColor=text_color,
                        alignment=TA_CENTER))],
            [Paragraph(label, style("l", fontSize=8, leading=10,
                        fontName="Helvetica", textColor=text_color,
                        alignment=TA_CENTER))],
        ]
        t = Table(d, colWidths=[(W-12*mm)/3])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), bg),
            ("ROUNDEDCORNERS", [4]),
            ("TOPPADDING", (0,0), (-1,-1), 4*mm),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4*mm),
            ("LEFTPADDING", (0,0), (-1,-1), 2*mm),
            ("RIGHTPADDING", (0,0), (-1,-1), 2*mm),
        ]))
        return t

    cards = Table([[
        mini_card(f"{pct}%", "Overall Score", BLUE_LIGHT, BLUE),
        Spacer(6*mm, 1),
        mini_card(f"{correct_count}/{total}", "Correct Answers", EMERALD_BG, EMERALD),
        Spacer(6*mm, 1),
        mini_card(percentile, "Estimated Rank", AMBER_BG, AMBER),
    ]], colWidths=[(W-12*mm)/3, 6*mm, (W-12*mm)/3, 6*mm, (W-12*mm)/3])
    cards.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(cards)
    story.append(spacer(6))

    # ── SECTION BREAKDOWN ─────────────────────────────────────────────────────
    story.append(Paragraph("Section Breakdown", S_SECTION))
    story.append(rule())

    if v_t: story.append(score_bar("Verbal Reasoning", v_c, v_t, BLUE))
    if n_t: story.append(score_bar("Numerical Reasoning", n_c, n_t, EMERALD))
    if a_t: story.append(score_bar("Abstract Reasoning", a_c, a_t, AMBER))
    story.append(spacer(4))

    # Section insight
    insight = f"Your strongest section is <b>{strongest}</b>. Focus your remaining preparation on <b>{weakest} Reasoning</b> to maximize your overall score."
    story.append(colored_card([[Paragraph(insight, S_BODY)]], bg=BLUE_LIGHT))
    story.append(spacer(6))

    # ── RESULT SUMMARY ────────────────────────────────────────────────────────
    story.append(Paragraph("Answer Summary", S_SECTION))
    story.append(rule())

    summary_data = [
        [Paragraph("<b>Result</b>", S_BODY),
         Paragraph("<b>Count</b>", S_BODY),
         Paragraph("<b>%</b>", S_BODY)],
        [Paragraph("✓  Correct", style("c", fontSize=9, leading=13,
                    fontName="Helvetica", textColor=EMERALD)),
         Paragraph(str(correct_count), S_BODY),
         Paragraph(f"{int(correct_count/total*100)}%", S_BODY)],
        [Paragraph("✗  Incorrect", style("i", fontSize=9, leading=13,
                    fontName="Helvetica", textColor=RED)),
         Paragraph(str(incorrect_count), S_BODY),
         Paragraph(f"{int(incorrect_count/total*100)}%", S_BODY)],
        [Paragraph("—  Unanswered", style("u", fontSize=9, leading=13,
                    fontName="Helvetica", textColor=SLATE_500)),
         Paragraph(str(unanswered_count), S_BODY),
         Paragraph(f"{int(unanswered_count/total*100)}%", S_BODY)],
    ]
    summary_t = Table(summary_data,
                      colWidths=[W*0.55, W*0.22, W*0.23],
                      rowHeights=[8*mm]*4)
    summary_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), SLATE_50),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, SLATE_50]),
        ("LINEBELOW", (0,0), (-1,0), 0.5, SLATE_200),
        ("LINEBELOW", (0,1), (-1,-1), 0.3, SLATE_200),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 3*mm),
        ("RIGHTPADDING", (0,0), (-1,-1), 3*mm),
        ("ROUNDEDCORNERS", [3]),
    ]))
    story.append(summary_t)
    story.append(spacer(6))

    # ── IMPROVEMENT TIPS ──────────────────────────────────────────────────────
    story.append(Paragraph("Areas for Improvement", S_SECTION))
    story.append(rule())

    for section, section_tips in tips.items():
        wrong_in_section = sum(1 for r in wrong if r.category == section.lower())
        total_in_section = sum(1 for r in req.results if r.category == section.lower())
        if total_in_section == 0:
            continue

        section_pct = int((total_in_section - wrong_in_section) / total_in_section * 100)
        color = EMERALD if section_pct >= 70 else AMBER if section_pct >= 50 else RED
        bg = EMERALD_BG if section_pct >= 70 else AMBER_BG if section_pct >= 50 else RED_BG

        header_row = [[
            Paragraph(f"<b>{section} Reasoning</b>", S_WHITE_BOLD),
            Paragraph(f"<b>{section_pct}%</b>",
                      style("sp", fontSize=10, leading=13,
                            fontName="Helvetica-Bold",
                            textColor=WHITE, alignment=TA_RIGHT)),
        ]]
        header_t = Table(header_row, colWidths=[W*0.75, W*0.25])
        header_t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), color),
            ("ROUNDEDCORNERS", [3]),
            ("TOPPADDING", (0,0), (-1,-1), 2*mm),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2*mm),
            ("LEFTPADDING", (0,0), (-1,-1), 3*mm),
            ("RIGHTPADDING", (0,0), (-1,-1), 3*mm),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(header_t)

        tip_rows = []
        for tip_title, tip_body in section_tips:
            tip_rows.append([
                Paragraph(f"• <b>{tip_title}:</b>", S_TIP_TITLE),
                Paragraph(tip_body, S_TIP_BODY),
            ])

        tip_t = Table(tip_rows, colWidths=[W*0.22, W*0.78])
        tip_t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), bg),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 3*mm),
            ("RIGHTPADDING", (0,0), (-1,-1), 3*mm),
            ("TOPPADDING", (0,0), (-1,-1), 2*mm),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2*mm),
            ("LINEBELOW", (0,0), (-1,-2), 0.3, colors.HexColor("#e2e8f0")),
        ]))
        story.append(tip_t)
        story.append(spacer(4))

    story.append(spacer(2))

    # ── QUESTION BREAKDOWN ────────────────────────────────────────────────────
    story.append(Paragraph("Full Question Breakdown", S_SECTION))
    story.append(rule())

    q_header = [
        Paragraph("<b>#</b>", S_SMALL),
        Paragraph("<b>Category</b>", S_SMALL),
        Paragraph("<b>Question</b>", S_SMALL),
        Paragraph("<b>Your Answer</b>", S_SMALL),
        Paragraph("<b>Correct Answer</b>", S_SMALL),
    ]

    q_rows = [q_header]
    for i, r in enumerate(req.results):
        if r.category == "abstract":
            user_ans = f"Option {r.selected}" if r.selected else "—"
            correct_ans = f"Option {r.correct_answer}"
        else:
            user_ans = r.selected[:30] if r.selected else "—"
            correct_ans = r.correct_answer[:30]

        q_text = r.question[:60] + "..." if len(r.question) > 60 else r.question

        if r.is_correct:
            ans_color = EMERALD
            marker = "✓"
        elif r.selected:
            ans_color = RED
            marker = "✗"
        else:
            ans_color = SLATE_500
            marker = "—"

        row = [
            Paragraph(f"{marker} {i+1}",
                      style(f"m{i}", fontSize=8, leading=11,
                            fontName="Helvetica-Bold", textColor=ans_color)),
            Paragraph(r.category.capitalize(), S_SMALL),
            Paragraph(q_text, S_SMALL),
            Paragraph(user_ans,
                      style(f"u{i}", fontSize=8, leading=11,
                            fontName="Helvetica", textColor=ans_color)),
            Paragraph(correct_ans,
                      style(f"c{i}", fontSize=8, leading=11,
                            fontName="Helvetica", textColor=EMERALD)),
        ]
        q_rows.append(row)

    q_table = Table(q_rows,
                    colWidths=[W*0.07, W*0.10, W*0.40, W*0.22, W*0.21],
                    repeatRows=1)
    q_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), SLATE_50),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, SLATE_50]),
        ("LINEBELOW", (0,0), (-1,0), 0.5, SLATE_200),
        ("LINEBELOW", (0,1), (-1,-1), 0.3, SLATE_200),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 2*mm),
        ("RIGHTPADDING", (0,0), (-1,-1), 2*mm),
        ("TOPPADDING", (0,0), (-1,-1), 1.5*mm),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1.5*mm),
    ]))
    story.append(q_table)
    story.append(spacer(6))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    footer_data = [[
        Paragraph("CCAT Practice Platform  •  Keep practicing to improve your score",
                  style("ft", fontSize=8, leading=10,
                        fontName="Helvetica", textColor=SLATE_500,
                        alignment=TA_CENTER)),
    ]]
    footer = Table(footer_data, colWidths=[W])
    footer.setStyle(TableStyle([
        ("LINEABOVE", (0,0), (-1,-1), 0.5, SLATE_200),
        ("TOPPADDING", (0,0), (-1,-1), 3*mm),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(footer)

    # ─── Build ────────────────────────────────────────────────────────────────
    doc.build(story)
    buffer.seek(0)
    return buffer.read()



@app.post("/api/verify-license")
def verify_license(data: dict):
    license_key = data.get("license_key", "").strip()
    if not license_key:
        return {"success": False, "message": "No license key provided"}
    
    try:
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_id": GUMROAD_PRODUCT_ID,
                "license_key": license_key,
                "increment_uses_count": "true"
            },
            headers={"Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN}"}
        )
        result = response.json()
        if result.get("success"):
            return {"success": True, "message": "License key valid"}
        else:
            return {"success": False, "message": "Invalid license key"}
    except Exception as e:
        return {"success": False, "message": str(e)}





def save_email_to_csv(email: str, score: int, percentage: int):
    filepath = "data/email_list.csv"
    file_exists = os.path.exists(filepath)
    with open(filepath, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["email", "score", "percentage", "date"])
        writer.writerow([email, score, percentage, datetime.now().strftime("%Y-%m-%d %H:%M")])

@app.post("/api/send-results")
def send_results(req: EmailRequest):
    # Generate PDF
    pdf_bytes = generate_pdf_report(req)
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    try:
        # Send results to user (currently hardcoded to your email until domain verified)
        resend.Emails.send({
            "from": "results@prepaptitude.com",
            "to": req.email,
            "subject": f"Your CCAT Practice Results — {req.percentage}% ({req.score}/{req.total})",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #2563eb; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 24px;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">CCAT Practice Results</h1>
                    <p style="color: #bfdbfe; margin: 8px 0 0 0;">Your detailed performance report is attached</p>
                </div>
                <div style="display: flex; gap: 12px; margin-bottom: 24px;">
                    <div style="flex:1; background:#eff6ff; border-radius:8px; padding:16px; text-align:center;">
                        <div style="font-size:32px; font-weight:bold; color:#2563eb;">{req.percentage}%</div>
                        <div style="color:#1e40af; font-size:13px;">Overall Score</div>
                    </div>
                    <div style="flex:1; background:#f0fdf4; border-radius:8px; padding:16px; text-align:center;">
                        <div style="font-size:32px; font-weight:bold; color:#16a34a;">{req.score}/{req.total}</div>
                        <div style="color:#166534; font-size:13px;">Correct Answers</div>
                    </div>
                </div>
                <p style="color:#475569; font-size:14px;">Your full performance report is attached as a PDF. It includes your section breakdown, improvement tips, and complete question analysis.</p>
                <div style="background:#f8fafc; border-radius:8px; padding:16px; margin-top:16px; text-align:center;">
                    <p style="color:#475569; font-size:13px; margin:0 0 12px 0;">Want more practice? Unlock Tests 2 and 3.</p>
                    <a href="https://8396304264007.gumroad.com/l/eakpb" style="background:#2563eb; color:white; padding:10px 24px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:13px;">Unlock 2 More Tests — $25</a>
                </div>
                <p style="color:#94a3b8; font-size:11px; text-align:center; margin-top:20px;">Sent by CCAT Practice Platform</p>
            </div>
            """,
            "attachments": [
                {
                    "filename": f"CCAT_Results_{req.percentage}pct.pdf",
                    "content": pdf_b64,
                }
            ]
        })

        # Notify yourself of new signup
        resend.Emails.send({
                    "from": "results@prepaptitude.com",
                    "to": "ahmedeltayebi270@gmail.com",  # your Gmail
                    "subject": f"New CCAT signup: {req.email} — {req.percentage}%",
                    "html": f"<p>New user: <b>{req.email}</b> scored <b>{req.percentage}%</b> ({req.score}/{req.total})</p>"
                })


        # Save email to CSV
        save_email_to_csv(req.email, req.score, req.percentage)

        return {"success": True, "message": "Results sent successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}






@app.get("/api/emails")
def get_emails():
    filepath = "data/email_list.csv"
    if not os.path.exists(filepath):
        return {"message": "No emails collected yet"}
    return FileResponse(filepath, filename="ccat_emails.csv")


# @app.post("/api/send-results")
# def send_results(req: EmailRequest):
#     correct_rows = ""
#     incorrect_rows = ""
#     unanswered_rows = ""

#     for i, r in enumerate(req.results):
#         if r.category == "abstract":
#             question_display = r.question
#             user_ans = f"Option {r.selected}" if r.selected else "Not answered"
#             correct_ans = f"Option {r.correct_answer}"
#         else:
#             question_display = r.question
#             user_ans = r.selected if r.selected else "Not answered"
#             correct_ans = r.correct_answer

#         row = f"""
#         <tr style="border-bottom: 1px solid #e2e8f0;">
#             <td style="padding: 8px; font-size: 13px; color: #475569;">Q{i+1} ({r.category})</td>
#             <td style="padding: 8px; font-size: 13px;">{question_display[:80]}...</td>
#             <td style="padding: 8px; font-size: 13px; color: {'#16a34a' if r.is_correct else '#dc2626' if r.selected else '#94a3b8'};">{user_ans}</td>
#             <td style="padding: 8px; font-size: 13px; color: #16a34a;">{correct_ans}</td>
#         </tr>
#         """
#         if r.is_correct:
#             correct_rows += row
#         elif r.selected:
#             incorrect_rows += row
#         else:
#             unanswered_rows += row

#     html = f"""
#     <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
#         <div style="background: #2563eb; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px;">
#             <h1 style="color: white; margin: 0; font-size: 24px;">CCAT Practice Test Results</h1>
#             <p style="color: #bfdbfe; margin: 8px 0 0 0;">Your detailed performance breakdown</p>
#         </div>

#         <div style="display: flex; gap: 16px; margin-bottom: 30px;">
#             <div style="flex: 1; background: #f0fdf4; border-radius: 8px; padding: 20px; text-align: center;">
#                 <div style="font-size: 36px; font-weight: bold; color: #16a34a;">{req.percentage}%</div>
#                 <div style="color: #166534; font-size: 14px;">Overall Score</div>
#             </div>
#             <div style="flex: 1; background: #eff6ff; border-radius: 8px; padding: 20px; text-align: center;">
#                 <div style="font-size: 36px; font-weight: bold; color: #2563eb;">{req.score}/{req.total}</div>
#                 <div style="color: #1e40af; font-size: 14px;">Correct Answers</div>
#             </div>
#         </div>

#         <h2 style="color: #1e293b; font-size: 18px; margin-bottom: 16px;">Question Breakdown</h2>

#         <h3 style="color: #16a34a; font-size: 15px;">Correct ({len([r for r in req.results if r.is_correct])})</h3>
#         <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
#             <tr style="background: #f8fafc;">
#                 <th style="padding: 8px; text-align: left; font-size: 12px; color: #64748b;">#</th>
#                 <th style="padding: 8px; text-align: left; font-size: 12px; color: #64748b;">Question</th>
#                 <th style="padding: 8px; text-align: left; font-size: 12px; color: #64748b;">Your Answer</th>
#                 <th style="padding: 8px; text-align: left; font-size: 12px; color: #64748b;">Correct</th>
#             </tr>
#             {correct_rows}
#         </table>

#         <h3 style="color: #dc2626; font-size: 15px;">Incorrect ({len([r for r in req.results if r.selected and not r.is_correct])})</h3>
#         <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
#             <tr style="background: #f8fafc;">
#                 <th style="padding: 8px; text-align: left; font-size: 12px; color: #64748b;">#</th>
#                 <th style="padding: 8px; text-align: left; font-size: 12px; color: #64748b;">Question</th>
#                 <th style="padding: 8px; text-align: left; font-size: 12px; color: #64748b;">Your Answer</th>
#                 <th style="padding: 8px; text-align: left; font-size: 12px; color: #64748b;">Correct</th>
#             </tr>
#             {incorrect_rows}
#         </table>

#         <div style="background: #f8fafc; border-radius: 8px; padding: 20px; margin-top: 24px; text-align: center;">
#             <p style="color: #475569; font-size: 14px; margin: 0 0 12px 0;">Want more practice? Take Test 2 and Test 3 to keep improving.</p>
#             <a href="http://localhost:5173" style="background: #2563eb; color: white; padding: 10px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 14px;">Practice More</a>
#         </div>

#         <p style="color: #94a3b8; font-size: 12px; text-align: center; margin-top: 24px;">
#             Sent by CCAT Practice Platform
#         </p>
#     </div>
#     """

#     try:
#         resend.Emails.send({
#             "from": "onboarding@resend.dev",
#             "to": "ahmedeltayebi270@gmail.com",
#             "subject": f"Your CCAT Practice Results — {req.percentage}% ({req.score}/{req.total})",
#             "html": html
#         })
#         return {"success": True, "message": "Results sent successfully"}
#     except Exception as e:
#         return {"success": False, "message": str(e)}