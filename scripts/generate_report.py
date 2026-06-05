"""
Generate the academic report (Word .docx) for the
Cameroon Malnutrition Atlas -- CEC 420 project.

Formatting spec:
  - Font: Times New Roman throughout
  - Headings: 16 pt bold black
  - Subheadings (H2): 14 pt bold black
  - Body text: 12 pt black, 1.5 line spacing
  - Tables: plain borders, no shading, no colour
  - TOC: dot leaders
  - Target: <= 28 pages
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES = os.path.join(BASE, "reports", "figures")
OUT     = os.path.join(BASE, "reports", "CEC420_Malnutrition_Atlas_Report_v5.docx")

BLACK = RGBColor(0, 0, 0)


# ──────────────────────────────────────────────────────────────────────────────
# LOW-LEVEL HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _set_spacing(para_fmt, lines=1.5):
    para_fmt.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    para_fmt.line_spacing = Pt(12 * lines)


def hline(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(0)
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "6")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), "000000")
    pBdr.append(bot)
    pPr.append(pBdr)


def page_break(doc):
    doc.add_page_break()


def _run(p, text, size=12, bold=False, italic=False):
    run = p.add_run(text)
    run.font.name   = "Times New Roman"
    run.font.size   = Pt(size)
    run.font.bold   = bold
    run.font.italic = italic
    run.font.color.rgb = BLACK
    return run


def heading(doc, text, level=1):
    size = {1: 16, 2: 14, 3: 13}.get(level, 12)
    align = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(4)
    _set_spacing(p.paragraph_format, 1.0)
    _run(p, text, size=size, bold=True)
    return p


def para(doc, text, size=12, bold=False, italic=False,
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    _set_spacing(p.paragraph_format)
    _run(p, text, size=size, bold=bold, italic=italic)
    return p


def bullet(doc, text, size=12):
    p = doc.add_paragraph()
    p.style = doc.styles["List Bullet"]
    p.paragraph_format.left_indent = Cm(1.2)
    p.paragraph_format.space_after = Pt(3)
    _set_spacing(p.paragraph_format)
    _run(p, text, size=size)
    return p


def plain_table(doc, headers, rows_data, caption=None):
    """Plain bordered table — no shading, all black text."""
    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.style     = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = tbl.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        r = hdr_cells[i].paragraphs[0].runs[0]
        r.font.name  = "Times New Roman"
        r.font.size  = Pt(11)
        r.font.bold  = True
        r.font.color.rgb = BLACK
    for row_vals in rows_data:
        cells = tbl.add_row().cells
        for i, v in enumerate(row_vals):
            cells[i].text = str(v)
            r = cells[i].paragraphs[0].runs[0]
            r.font.name  = "Times New Roman"
            r.font.size  = Pt(11)
            r.font.color.rgb = BLACK
    if caption:
        cp = doc.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        cp.paragraph_format.space_after = Pt(10)
        _run(cp, caption, size=10, bold=True)
    doc.add_paragraph()
    return tbl


def figure(doc, caption, fig_num, filename=None):
    path = os.path.join(FIGURES, filename) if filename else None
    if path and os.path.exists(path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(path, width=Inches(5.0))
    else:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(p, f"[Figure {fig_num}: {caption}]", size=10, italic=True)
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(10)
    _run(cap, f"Figure {fig_num}: {caption}", size=10, italic=True)


def section_title(doc, text):
    """Standalone pre-chapter title (Abstract, TOC, etc.) — centred 15 pt bold."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(10)
    _run(p, text, size=15, bold=True)


def toc_entry(doc, label, pg, indent=False):
    p = doc.add_paragraph()
    _set_spacing(p.paragraph_format, 1.0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Cm(1.0) if indent else Cm(0)
    # Use a tab stop for right-aligned page numbers
    pPr = p._p.get_or_add_pPr()
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"),    "right")
    tab.set(qn("w:leader"), "dot")
    tab.set(qn("w:pos"),    "8640")   # ~15 cm from margin
    tabs.append(tab)
    pPr.append(tabs)
    r1 = p.add_run(label)
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(11)
    r1.font.color.rgb = BLACK
    r2 = p.add_run(f"\t{pg}")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(11)
    r2.font.color.rgb = BLACK


def _rm_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ["top","left","bottom","right","insideH","insideV"]:
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"),   "none")
        b.set(qn("w:sz"),    "0")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "auto")
        borders.append(b)
    tbl_pr.append(borders)


# ──────────────────────────────────────────────────────────────────────────────
# DOCUMENT SETUP
# ──────────────────────────────────────────────────────────────────────────────
doc = Document()
for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(3.0)
    section.right_margin  = Cm(2.5)

style = doc.styles["Normal"]
style.font.name      = "Times New Roman"
style.font.size      = Pt(12)
style.font.color.rgb = BLACK


# ══════════════════════════════════════════════════════════════════════════════
# COVER PAGE  (SkillMap bilateral style)
# ══════════════════════════════════════════════════════════════════════════════
def _cover_col(cell, lines):
    cell.paragraphs[0].clear()
    for i, line in enumerate(lines):
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line)
        r.font.name      = "Times New Roman"
        r.font.size      = Pt(11)
        r.font.bold      = True
        r.font.color.rgb = BLACK

cover_tbl = doc.add_table(rows=1, cols=2)
_rm_borders(cover_tbl)
_cover_col(cover_tbl.cell(0, 0), [
    "REPUBLIC OF CAMEROON",
    "Peace - Work - Fatherland",
    "***",
    "UNIVERSITY OF BUEA",
    "COLLEGE OF TECHNOLOGY",
    "DEPARTMENT OF COMPUTER ENGINEERING",
])
_cover_col(cover_tbl.cell(0, 1), [
    "REPUBLIQUE DU CAMEROUN",
    "Paix - Travail - Patrie",
    "***",
    "UNIVERSITE DE BUEA",
    "COLLEGE DE TECHNOLOGIE",
    "DEPARTEMENT DE GENIE INFORMATIQUE",
])

doc.add_paragraph()
hline(doc)
doc.add_paragraph()

title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
title_r = title_p.add_run(
    "CAMEROON MALNUTRITION ATLAS:\n"
    "A DATA MINING APPROACH TO PREDICTING\n"
    "AND MAPPING CHILD STUNTING HOTSPOTS"
)
title_r.font.name      = "Times New Roman"
title_r.font.size      = Pt(16)
title_r.font.bold      = True
title_r.font.color.rgb = BLACK
title_p.paragraph_format.space_before = Pt(6)
title_p.paragraph_format.space_after  = Pt(6)

doc.add_paragraph()

sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub_r = sub_p.add_run(
    "A Project Report Submitted to the Department of Computer Engineering "
    "of the College of Technology of the University of Buea in Partial "
    "Fulfilment of the Requirements for the Award of the Bachelor of Technology "
    "Degree in Computer Engineering (Software Engineering Option)"
)
sub_r.font.name      = "Times New Roman"
sub_r.font.size      = Pt(11)
sub_r.font.color.rgb = BLACK

doc.add_paragraph()

for text in [
    "PRESENTED BY:",
    "SEPO PERRY-BRADLEY DINGA  -  CT23A145",
    "",
    "DEPARTMENT OF COMPUTER ENGINEERING",
    "COURSE CODE: CEC 420 - DATA MINING",
    "2025/2026 ACADEMIC YEAR",
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(3)
    if text:
        r = p.add_run(text)
        r.font.name      = "Times New Roman"
        r.font.size      = Pt(12)
        r.font.bold      = True
        r.font.color.rgb = BLACK

page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CERTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
section_title(doc, "Certification")
para(doc,
    "This is to certify that this project report entitled \"Cameroon Malnutrition Atlas: "
    "A Data Mining Approach to Predicting and Mapping Child Stunting Hotspots\" was carried "
    "out by SEPO PERRY-BRADLEY DINGA (CT23A145) and is hereby approved for submission in "
    "partial fulfilment of the requirements for the award of the Bachelor of Technology "
    "Degree in Computer Engineering, University of Buea.")
doc.add_paragraph()
para(doc, "Supervisor's Name: ___________________________________    Date: _______________")
para(doc, "Supervisor's Signature: _______________________________")
para(doc, "Head of Department: __________________________________    Date: _______________")
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# ATTESTATION
# ══════════════════════════════════════════════════════════════════════════════
section_title(doc, "Attestation")
para(doc,
    "I hereby declare that this project report is my own original work and has not been "
    "submitted for any degree or examination at this or any other institution. "
    "All sources consulted have been duly acknowledged.")
doc.add_paragraph()
para(doc, "Name:       SEPO PERRY-BRADLEY DINGA")
para(doc, "Student ID: CT23A145")
para(doc, "Date:       June 2026")
doc.add_paragraph()
para(doc, "Signature: _______________________________")
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# ABSTRACT
# ══════════════════════════════════════════════════════════════════════════════
section_title(doc, "Abstract")
para(doc,
    "Child stunting affects approximately 29% of children under five in Cameroon, with the "
    "burden heavily concentrated in the northern regions. This project applies the CRISP-DM "
    "data mining framework to Demographic and Health Survey (DHS) sub-national data "
    "(1991–2018) to predict regional stunting rates, classify regions by WHO risk band, "
    "and identify which areas need urgent intervention.")
para(doc,
    "A Random Forest regression model achieved a cross-validated RMSE of 3.64 percentage "
    "points — a 71% improvement over the mean-prediction baseline. A Random Forest "
    "classifier assigned WHO risk bands (Low / Medium / High / Critical) with 80% accuracy. "
    "K-Means clustering grouped regions into two profiles: a high-risk northern cluster "
    "(37% stunting) and a low-risk southern cluster (24% stunting). Healthcare access and "
    "WASH infrastructure emerged as the strongest drivers of stunting. Results are published "
    "through an interactive web dashboard.")
para(doc,
    "Keywords: data mining, CRISP-DM, child stunting, Cameroon, regression, "
    "classification, clustering, hotspot mapping.",
    italic=True)
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# LIST OF ABBREVIATIONS
# ══════════════════════════════════════════════════════════════════════════════
section_title(doc, "List of Abbreviations")
plain_table(doc,
    ["Abbreviation", "Full Form"],
    [
        ("CRISP-DM", "Cross-Industry Standard Process for Data Mining"),
        ("CV",       "Cross-Validation"),
        ("DHS",      "Demographic and Health Survey"),
        ("HDX",      "Humanitarian Data Exchange"),
        ("RMSE",     "Root Mean Square Error"),
        ("WASH",     "Water, Sanitation and Hygiene"),
        ("WHO",      "World Health Organization"),
    ]
)
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# LIST OF FIGURES
# ══════════════════════════════════════════════════════════════════════════════
section_title(doc, "List of Figures")
for label, cap in [
    ("Figure 3.1", "The six phases of the CRISP-DM methodology"),
    ("Figure 3.2", "System architecture — Python pipeline and Next.js web application"),
    ("Figure 4.1", "Stunting rate distribution across all region-year observations"),
    ("Figure 4.2", "Stunting rate by region — median-sorted box plot (1991–2018)"),
    ("Figure 4.3", "Spearman correlation between features and stunting rate"),
    ("Figure 4.4", "Trend of stunting rates over survey years per region"),
    ("Figure 4.5", "Regression model leaderboard — 5-fold CV RMSE comparison"),
    ("Figure 4.6", "Confusion matrix — WHO risk band classifier (Random Forest)"),
    ("Figure 4.7", "K-Means clustering visualised in PCA space (k = 2)"),
    ("Figure 4.8", "Stunting rate forecasts to 2026 and 2028 — top hotspot regions"),
    ("Figure 4.9", "Home page — Cameroon Malnutrition Atlas web dashboard"),
    ("Figure 4.10","Hotspots page — choropleth map and ranked region table"),
]:
    p = doc.add_paragraph()
    _set_spacing(p.paragraph_format, 1.0)
    p.paragraph_format.space_after = Pt(3)
    _run(p, f"{label}:  {cap}", size=11)
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# LIST OF TABLES
# ══════════════════════════════════════════════════════════════════════════════
section_title(doc, "List of Tables")
for label, cap in [
    ("Table 1.1", "Definition of key terms"),
    ("Table 3.1", "Dataset overview — feature groups and sources"),
    ("Table 3.2", "Web application pages"),
    ("Table 4.1", "Regression model results — CV RMSE comparison"),
    ("Table 4.2", "Hypothesis test results"),
    ("Table 4.3", "K-Means cluster profiles"),
    ("Table 4.4", "Top 10 predicted stunting hotspots (2018)"),
]:
    p = doc.add_paragraph()
    _set_spacing(p.paragraph_format, 1.0)
    p.paragraph_format.space_after = Pt(3)
    _run(p, f"{label}:  {cap}", size=11)
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ══════════════════════════════════════════════════════════════════════════════
section_title(doc, "Table of Contents")
entries = [
    ("Certification",                                          "ii",   False),
    ("Attestation",                                            "iii",  False),
    ("Abstract",                                               "iv",   False),
    ("List of Abbreviations",                                  "v",    False),
    ("List of Figures",                                        "vi",   False),
    ("List of Tables",                                         "vii",  False),
    ("CHAPTER ONE: GENERAL INTRODUCTION",                      "1",    False),
    ("1.1  Introduction",                                      "1",    True),
    ("1.2  Background of the Study",                           "1",    True),
    ("1.3  Statement of the Problem",                          "2",    True),
    ("1.4  Objectives of the Study",                           "2",    True),
    ("1.5  Significance of the Study",                         "3",    True),
    ("1.6  Scope of the Study",                                "3",    True),
    ("1.7  Definition of Key Terms",                           "3",    True),
    ("1.8  Organisation of the Study",                         "4",    True),
    ("CHAPTER TWO: LITERATURE REVIEW",                         "5",    False),
    ("2.1  Introduction",                                      "5",    True),
    ("2.2  Data Mining Concepts",                              "5",    True),
    ("2.3  Review of Existing Systems",                        "7",    True),
    ("2.4  Proposed Solution",                                 "7",    True),
    ("CHAPTER THREE: MATERIALS AND METHODS",                   "8",    False),
    ("3.1  Introduction",                                      "8",    True),
    ("3.2  Methodology — CRISP-DM",                            "8",    True),
    ("3.3  Dataset",                                           "10",   True),
    ("3.4  Data Preparation",                                  "11",   True),
    ("3.5  System Design",                                     "11",   True),
    ("CHAPTER FOUR: IMPLEMENTATION, RESULTS AND DISCUSSION",   "13",   False),
    ("4.1  Introduction",                                      "13",   True),
    ("4.2  Exploratory Data Analysis",                         "13",   True),
    ("4.3  Regression — Predicting Stunting Rate",             "15",   True),
    ("4.4  Classification — WHO Risk Bands",                   "16",   True),
    ("4.5  Clustering — Regional Profiles",                    "17",   True),
    ("4.6  Hypothesis Tests",                                  "18",   True),
    ("4.7  Forecasting",                                       "19",   True),
    ("4.8  Hotspot Ranking",                                   "19",   True),
    ("4.9  Web Application",                                   "21",   True),
    ("CHAPTER FIVE: CONCLUSIONS AND RECOMMENDATIONS",          "23",   False),
    ("5.1  Conclusions",                                       "23",   True),
    ("5.2  Limitations",                                       "24",   True),
    ("5.3  Perspectives for Further Study",                    "24",   True),
    ("References",                                             "25",   False),
]
for label, pg, indent in entries:
    toc_entry(doc, label, pg, indent)
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER ONE
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, "CHAPTER ONE: GENERAL INTRODUCTION")

heading(doc, "1.1  Introduction", level=2)
para(doc,
    "Stunting — defined as height-for-age more than two standard deviations below the WHO "
    "Child Growth Standards median — is the most widespread form of chronic malnutrition. "
    "In Cameroon, the 2018 Demographic and Health Survey (DHS) recorded a national stunting "
    "prevalence of 29%, but this figure conceals wide regional disparities: the North and "
    "Far North regions exceed 39%, while the Littoral region records just 18%. "
    "Identifying and ranking the regions that most urgently need nutrition intervention "
    "requires a systematic, data-driven approach.")
para(doc,
    "This project — the Cameroon Malnutrition Atlas — uses data mining techniques to analyse "
    "DHS survey data and produce a ranked hotspot map of child stunting across Cameroon's "
    "ten regions. Results are published through an interactive web dashboard.")

heading(doc, "1.2  Background of the Study", level=2)
para(doc,
    "The DHS Programme has collected sub-national health and nutrition data in Cameroon "
    "across five survey rounds: 1991, 1998, 2004, 2011, and 2018. Each round captures "
    "indicators such as child stunting rates, maternal education levels, access to clean "
    "water and sanitation (WASH), and healthcare utilisation for each of the country's "
    "ten administrative regions.")
para(doc,
    "Despite this rich longitudinal dataset, no systematic data mining study had been "
    "applied to produce a predictive, ranked hotspot analysis at the regional level. "
    "This project fills that gap by applying regression, classification, and clustering "
    "to produce actionable targeting intelligence.")

heading(doc, "1.3  Statement of the Problem", level=2)
para(doc,
    "Budget allocation for nutrition interventions in Cameroon is not currently guided "
    "by a data-driven ranking of regional risk. As a result, the regions with the greatest "
    "need may not receive proportionally greater investment. "
    "The specific problems this project addresses are:")
bullet(doc, "No predictive model exists for estimating regional stunting rates from observable indicators.")
bullet(doc, "Regions are not systematically classified into WHO risk categories for targeting purposes.")
bullet(doc, "No cluster-based profiles exist to guide differentiated intervention strategies across regions.")

heading(doc, "1.4  Objectives of the Study", level=2)
heading(doc, "1.4.1  General Objective", level=3)
para(doc,
    "To apply data mining techniques to Cameroon DHS data in order to predict regional "
    "stunting rates, classify regions by WHO risk band, cluster regions by driver profile, "
    "and publish a ranked hotspot map through an interactive web dashboard.")

heading(doc, "1.4.2  Specific Objectives", level=3)
bullet(doc, "To collect and prepare five waves of DHS sub-national data for Cameroon (1991–2018).")
bullet(doc, "To train and evaluate regression models for stunting rate prediction.")
bullet(doc, "To train a classifier that assigns each region to a WHO public-health risk band.")
bullet(doc, "To apply K-Means clustering to group regions by their socio-economic profiles.")
bullet(doc, "To test hypotheses about the drivers of stunting using statistical tests.")
bullet(doc, "To forecast regional stunting trends to 2026 and 2028.")
bullet(doc, "To deploy results through an interactive web application.")

heading(doc, "1.5  Significance of the Study", level=2)
para(doc,
    "This project gives the Ministry of Public Health a simple, ranked list of regions by "
    "predicted stunting risk, directly informing where to invest nutrition and WASH budgets. "
    "It also demonstrates how standard data mining methods can be applied to a real "
    "African public-health problem using publicly available DHS data.")

heading(doc, "1.6  Scope of the Study", level=2)
para(doc,
    "The analysis covers Cameroon's ten administrative regions across five DHS survey rounds "
    "(1991–2018). The data mining tasks performed are: regression, classification, clustering, "
    "hypothesis testing, and linear trend forecasting. Results are deployed as a Next.js web "
    "application. The project does not cover district-level analysis or causal modelling.")

heading(doc, "1.7  Definition of Key Terms", level=2)
plain_table(doc,
    ["Term", "Definition"],
    [
        ("Stunting",       "Height-for-age below 2 standard deviations of the WHO median. Indicator of chronic malnutrition."),
        ("Data Mining",    "The process of discovering patterns and knowledge from large datasets (Kometa, 2026)."),
        ("Regression",     "Predicts a continuous numeric value (stunting rate %) from input features."),
        ("Classification", "Assigns observations to predefined categories (WHO risk bands)."),
        ("Clustering",     "Groups regions into profiles based on similarity in their socio-economic indicators."),
        ("CRISP-DM",       "Cross-Industry Standard Process for Data Mining — a six-phase project methodology."),
        ("Hotspot",        "A region with a predicted stunting rate above the national average, requiring priority action."),
        ("WHO Risk Band",  "Low (<20%), Medium (20-29%), High (30-39%), Critical (>=40%) stunting categories."),
    ],
    caption="Table 1.1: Definition of key terms"
)

heading(doc, "1.8  Organisation of the Study", level=2)
para(doc,
    "This report is organised into five chapters. Chapter One introduces the project. "
    "Chapter Two reviews data mining concepts and related work. Chapter Three describes "
    "the dataset and methodology. Chapter Four presents and discusses the results. "
    "Chapter Five presents conclusions and recommendations.")
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER TWO
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, "CHAPTER TWO: LITERATURE REVIEW")

heading(doc, "2.1  Introduction", level=2)
para(doc,
    "This chapter reviews the data mining concepts applied in this project and surveys "
    "existing tools that address related problems.")

heading(doc, "2.2  Data Mining Concepts", level=2)

heading(doc, "2.2.1  Data Mining", level=3)
para(doc,
    "Data mining is the process of discovering patterns and relationships in large datasets. "
    "It involves six common classes of tasks: anomaly detection, association rule learning, "
    "clustering, classification, regression, and summarisation (Kometa, 2026). This project "
    "applies the three most relevant tasks for a quantitative prediction problem: regression, "
    "classification, and clustering.")

heading(doc, "2.2.2  Regression and Classification", level=3)
para(doc,
    "Classification is the process of finding a model that describes and distinguishes data "
    "classes, so it can be used to predict the class of new, unseen objects (Kometa, 2026). "
    "The model is constructed from a labelled training set and evaluated on a separate test "
    "set. When the output is a discrete label the task is classification; when the output is "
    "a continuous number, the task is regression (prediction).")
para(doc,
    "In this project, regression is used to predict the stunting rate (a continuous percentage) "
    "for each region, while classification is used to assign each region to a WHO risk band "
    "(a discrete label). Random Forest — an ensemble of decision trees — is used for both "
    "tasks because it handles small datasets and mixed feature types well, and is robust to "
    "outliers.")

heading(doc, "2.2.3  Clustering", level=3)
para(doc,
    "Clustering is the task of grouping data points so that items within a group are more "
    "similar to each other than to items in other groups (Kometa, 2026). It is unsupervised — "
    "no class labels are needed. K-Means is the most widely used algorithm: it partitions "
    "observations into k groups by iteratively assigning each point to its nearest centroid "
    "and recomputing centroids until the assignments stop changing.")
para(doc,
    "The optimal number of clusters k is chosen using the elbow method, which plots the "
    "within-cluster sum of squares against k and looks for the point where adding more "
    "clusters gives diminishing returns.")

heading(doc, "2.2.4  Hypothesis Testing", level=3)
para(doc,
    "Hypothesis tests are used to validate whether patterns found in the data are statistically "
    "significant. The Spearman rank-correlation coefficient is used here because the data are "
    "not normally distributed. A p-value below 0.05 indicates that the observed association is "
    "unlikely to have arisen by chance.")

heading(doc, "2.2.5  CRISP-DM", level=3)
para(doc,
    "CRISP-DM (Cross-Industry Standard Process for Data Mining) is the standard framework for "
    "structuring data mining projects (Chapman et al., 2000). It defines six phases: Business "
    "Understanding, Data Understanding, Data Preparation, Modelling, Evaluation, and "
    "Deployment. This project follows all six phases.")

heading(doc, "2.3  Review of Existing Systems", level=2)
para(doc,
    "Existing tools such as the DHS STATcompiler and UNICEF Joint Malnutrition Estimates "
    "provide descriptive statistics on stunting but are not predictive and do not rank "
    "regions by risk. No existing system applies regression, classification, and clustering "
    "jointly to Cameroon sub-national DHS data to produce a ranked hotspot list.")

heading(doc, "2.4  Proposed Solution", level=2)
para(doc,
    "This project addresses the gap by building a CRISP-DM pipeline that trains predictive "
    "models on DHS data, clusters regions by socio-economic profile, tests key hypotheses, "
    "and publishes all results through an interactive web dashboard.")
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER THREE
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, "CHAPTER THREE: MATERIALS AND METHODS")

heading(doc, "3.1  Introduction", level=2)
para(doc,
    "This chapter describes the methodology, dataset, and data preparation steps used "
    "in this project.")

heading(doc, "3.2  Methodology — CRISP-DM", level=2)
para(doc,
    "The project follows the six CRISP-DM phases illustrated in Figure 3.1.")
figure(doc, "The six phases of the CRISP-DM methodology", "3.1")

heading(doc, "Phase 1 — Business Understanding", level=3)
para(doc,
    "The goal is to rank Cameroon's regions by predicted child stunting risk to guide "
    "intervention budget allocation. Success criteria: regression CV RMSE below 5 percentage "
    "points; classifier accuracy above 75%; clustering silhouette score above 0.40.")

heading(doc, "Phase 2 — Data Understanding", level=3)
para(doc,
    "Five waves of DHS/MICS sub-national survey data for Cameroon were sourced from the "
    "Humanitarian Data Exchange (HDX). The data cover ten regions across survey years "
    "1991, 1998, 2004, 2011, and 2018. Key indicators explored include stunting rate, "
    "maternal education, WASH access, and healthcare utilisation.")

heading(doc, "Phase 3 — Data Preparation", level=3)
para(doc,
    "Raw DHS long-format CSV files were stitched into a wide analysis table of 50 rows "
    "(10 regions x 5 survey years). Missing values were imputed using the region-year "
    "median, falling back to the global median where needed. Data were split 80/20 into "
    "training and hold-out test sets.")

heading(doc, "Phase 4 — Modelling", level=3)
para(doc,
    "Three modelling tasks were performed: regression to predict the stunting rate, "
    "classification to assign a WHO risk band, and K-Means clustering to group regions "
    "by driver profile. A linear trend model was also fitted to each region for forecasting.")

heading(doc, "Phase 5 — Evaluation", level=3)
para(doc,
    "Models were evaluated using five-fold cross-validation on the training set. "
    "Regression used RMSE; classification used accuracy and macro F1; clustering used "
    "the silhouette coefficient. Six hypothesis tests were run at alpha = 0.05.")

heading(doc, "Phase 6 — Deployment", level=3)
para(doc,
    "All results were saved as CSV files, converted to JSON, and served through a Next.js "
    "web application covering hotspot ranking, regression, classification, clustering, "
    "hypothesis tests, and forecasts.")

heading(doc, "3.3  Dataset", level=2)
para(doc,
    "The analysis dataset consists of 50 observations — one per region-year combination — "
    "and a target variable (stunting rate, %) plus four groups of predictor features "
    "summarised in Table 3.1.")
plain_table(doc,
    ["Feature Group", "Examples", "Source"],
    [
        ("Maternal Education",  "% women with secondary schooling, literacy rate",             "DHS"),
        ("WASH",                "% households with improved water and sanitation",             "DHS"),
        ("Healthcare Access",   "% facility deliveries, skilled birth attendance",             "DHS"),
        ("Disease Burden",      "Child anaemia prevalence, malaria prevalence",                "DHS / WHO"),
    ],
    caption="Table 3.1: Dataset overview — feature groups, examples, and source"
)

heading(doc, "3.3.1  Tools and Technologies", level=3)
bullet(doc, "Python 3.11 — pandas, numpy, scipy, scikit-learn, xgboost, lightgbm")
bullet(doc, "Web application — Next.js 16, React 19, TypeScript, Tailwind CSS 4")
bullet(doc, "Version control — Git / GitHub")
bullet(doc, "Development environment — Visual Studio Code")

heading(doc, "3.4  Data Preparation", level=2)
bullet(doc, "Region name normalisation: DHS label variants mapped to ten canonical region names.")
bullet(doc, "Missing value imputation: region-year median first, then global median as fallback.")
bullet(doc, "Composite feature: a WASH score derived as the mean of water and sanitation access.")
bullet(doc, "Train/test split: 80% training, 20% hold-out test set, stratified by WHO risk band.")

heading(doc, "3.5  System Design", level=2)
para(doc,
    "The system has two layers: a Python analysis pipeline and a Next.js web application. "
    "The pipeline (under the src/ directory) loads and cleans the DHS data, trains models, "
    "runs hypothesis tests, and saves all results as CSV files. "
    "The web application reads these outputs and displays them across seven pages, "
    "as described in Table 3.2.")
figure(doc, "System architecture — Python pipeline and Next.js web application", "3.2")
plain_table(doc,
    ["Page", "Content"],
    [
        ("Home",           "Key statistics, Cameroon choropleth map, top-10 hotspot table."),
        ("Hotspots",       "Full ranked table with predicted stunting, WHO band, and 2028 forecast."),
        ("Regression",     "Model leaderboard showing CV RMSE for all models."),
        ("Classification", "Confusion matrix and WHO risk band distribution."),
        ("Clustering",     "Cluster profiles and PCA visualisation."),
        ("Forecasts",      "Per-region trend lines with 2026 and 2028 projections."),
        ("Hypotheses",     "H1–H6 results with Spearman rho, p-value, and outcome."),
    ],
    caption="Table 3.2: Web application pages"
)
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER FOUR
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, "CHAPTER FOUR: IMPLEMENTATION, RESULTS AND DISCUSSION")

heading(doc, "4.1  Introduction", level=2)
para(doc,
    "This chapter presents the implementation of the data mining pipeline and the results "
    "of all analyses: exploratory data analysis, regression, classification, clustering, "
    "hypothesis testing, forecasting, the hotspot ranking, and the web application.")

heading(doc, "4.2  Exploratory Data Analysis", level=2)
para(doc,
    "Before building any model, the dataset was explored to understand the distribution of "
    "the target variable, regional patterns, feature correlations, and trends over time. "
    "This EDA phase directly informed the choice of models and features.")

heading(doc, "4.2.1  Target Distribution", level=3)
para(doc,
    "Stunting rates across the 50 region-year observations range from 18% (Littoral, 2018) "
    "to approximately 44% in the northern regions during earlier survey years. The mean is "
    "approximately 29% — at the WHO 'High' risk threshold. About 40% of observations "
    "fall above 30%, indicating that high stunting is the norm for the northern regions "
    "across all survey waves.")
figure(doc, "Stunting rate distribution across all region-year observations", "4.1",
       "01_target_distribution.png")

heading(doc, "4.2.2  Regional Patterns", level=3)
para(doc,
    "The box plot in Figure 4.2 — sorted by regional median — confirms a clear and "
    "persistent north-south gradient. The Far North, North, and Adamawa consistently "
    "record the highest medians (above 36%), while Littoral, South, and Centre record "
    "the lowest (below 24%). This pattern is consistent across all five survey waves, "
    "indicating structural rather than temporary disparities.")
figure(doc, "Stunting rate by region — median-sorted box plot (1991-2018)", "4.2",
       "02_region_boxplot.png")

heading(doc, "4.2.3  Feature Correlations", level=3)
para(doc,
    "A Spearman rank-correlation analysis was computed between all features and the "
    "target variable. Healthcare access (facility delivery rate) showed the strongest "
    "negative correlation (rho = -0.77), meaning regions with higher rates of "
    "facility-based deliveries have significantly lower stunting. WASH access "
    "(rho = -0.50) and socio-economic status (rho = -0.39) followed. These findings "
    "directly guided hypothesis design.")
figure(doc, "Spearman correlation between features and stunting rate", "4.3",
       "03_correlation_heatmap.png")

heading(doc, "4.2.4  Trends Over Time", level=3)
para(doc,
    "Plotting stunting rates over the five survey years shows a general downward trend "
    "for all regions, but the pace of improvement varies widely. Littoral and Centre "
    "improve by roughly 0.3 percentage points per year, while Far North and North "
    "improve by only 0.1 pp per year. This slow improvement in the north motivates the "
    "forecasting analysis in Section 4.7.")
figure(doc, "Trend of stunting rates over survey years per region", "4.4",
       "04_trend_over_time.png")

heading(doc, "4.3  Regression — Predicting Stunting Rate", level=2)
para(doc,
    "Several regression models were trained and compared using five-fold cross-validation. "
    "Table 4.1 shows the key results. Random Forest achieved the best cross-validated RMSE "
    "of 3.64 percentage points — a 71% improvement over the simple mean-prediction baseline "
    "of 12.72 pp. This improvement is statistically significant (p < 0.001).")

plain_table(doc,
    ["Model", "CV RMSE (pp)", "Hold-out RMSE (pp)"],
    [
        ("Random Forest",     "3.64", "3.51"),
        ("XGBoost",           "3.67", "3.42"),
        ("Gradient Boosting", "3.71", "3.56"),
        ("Linear Regression", "3.92", "3.94"),
        ("Baseline (mean)",   "12.72", "11.89"),
    ],
    caption="Table 4.1: Regression model results — CV RMSE comparison (lower is better)"
)
para(doc,
    "All trained models substantially outperform the baseline, confirming that stunting rates "
    "can be predicted from observable socio-economic and health indicators. Ensemble models "
    "(Random Forest, XGBoost, Gradient Boosting) perform best, which is consistent with their "
    "known strength on small, structured datasets.")
figure(doc, "Regression model leaderboard — 5-fold CV RMSE comparison", "4.5",
       "06_model_leaderboard.png")

heading(doc, "4.4  Classification — WHO Risk Bands", level=2)
para(doc,
    "Each region-year observation was assigned to one of four WHO public-health risk bands "
    "based on its stunting rate: Low (< 20%), Medium (20-29%), High (30-39%), "
    "and Critical (>= 40%). A Random Forest classifier was trained on the same features "
    "used for regression and achieved 80% accuracy on the hold-out test set, with a "
    "macro F1 score of 0.80 — indicating balanced performance across all four bands.")
para(doc,
    "The confusion matrix in Figure 4.4 shows that errors are confined to adjacent risk "
    "bands only. No observation is misclassified across more than one band, which is "
    "expected given that the underlying stunting rate is continuous.")
figure(doc, "Confusion matrix — WHO risk band classifier (Random Forest)", "4.6",
       "11_confusion_matrix.png")

heading(doc, "4.5  Clustering — Regional Profiles", level=2)
para(doc,
    "K-Means clustering was applied to group regions by their socio-economic and "
    "health-system profiles, independent of their stunting rate. The elbow method "
    "identified k = 2 as the optimal number of clusters, confirmed by a silhouette "
    "score of 0.52.")
figure(doc, "K-Means clustering visualised in PCA space (k = 2)", "4.7",
       "13_clusters_pca.png")
para(doc,
    "The two clusters are clearly separated and directly interpretable:")
plain_table(doc,
    ["Cluster", "Label", "Regions", "Mean Stunting"],
    [
        ("0", "Northern-rural (high risk)",
         "North, Far North, Adamawa, East", "37%"),
        ("1", "Southern (lower risk)",
         "Centre, Littoral, South, West, Northwest, Southwest", "24%"),
    ],
    caption="Table 4.3: K-Means cluster profiles"
)
para(doc,
    "The northern cluster is characterised by very low female secondary education (2% "
    "vs 10%), much lower literacy rates (44% vs 87%), and poorer WASH and healthcare "
    "access. This means interventions in northern regions must address multiple drivers "
    "simultaneously rather than targeting any single indicator.")

heading(doc, "4.6  Hypothesis Tests", level=2)
para(doc,
    "Six null hypotheses were tested at significance level alpha = 0.05 using the "
    "Spearman rank-correlation test (H1-H5) and a one-sided paired t-test (H6).")
plain_table(doc,
    ["Hypothesis", "Driver", "Spearman rho / Effect", "p-value", "Result"],
    [
        ("H1", "Maternal education",   "rho = -0.28", "0.046",  "Confirmed"),
        ("H2", "WASH access",          "rho = -0.50", "0.0002", "Confirmed"),
        ("H3", "Socio-economic status","rho = -0.39", "0.005",  "Confirmed"),
        ("H4", "Healthcare access",    "rho = -0.77", "< 0.001","Confirmed"),
        ("H5", "Malaria prevalence",   "rho = +0.18", "0.225",  "Not confirmed"),
        ("H6", "ML beats baseline",    "-71% RMSE",   "< 0.001","Confirmed"),
    ],
    caption="Table 4.2: Hypothesis test results (alpha = 0.05)"
)
para(doc,
    "Five of the six hypotheses were confirmed. Healthcare access is the strongest "
    "correlate of stunting (rho = -0.77), followed by WASH access (rho = -0.50) and "
    "socio-economic status (rho = -0.39). Hypothesis H5 — malaria prevalence — was "
    "not confirmed, likely because the malaria indicator has limited sub-national "
    "coverage in the dataset.")

heading(doc, "4.7  Forecasting", level=2)
para(doc,
    "A linear trend was fitted to each region's historical stunting series (1991-2018) "
    "and extrapolated to 2026 and 2028. The slope in percentage points per year is the "
    "key metric — a negative slope indicates improvement.")
figure(doc, "Stunting rate forecasts to 2026 and 2028 for top hotspot regions", "4.8",
       "14_forecasts_top5.png")
para(doc,
    "At current improvement rates, the North region is projected to reach 40.6% by 2026 "
    "and 40.4% by 2028 — still in the WHO Critical band. The Far North is projected at "
    "39.2% by 2028. Without accelerated intervention the three northern regions will remain "
    "above the 30% High threshold through at least 2028.")

heading(doc, "4.8  Hotspot Ranking", level=2)
para(doc,
    "The main output of the pipeline is a ranked table of all ten regions by their "
    "predicted stunting rate in 2018, combining the regression prediction, WHO risk band, "
    "cluster assignment, and 2028 forecast. Table 4.4 shows the full ranking.")
plain_table(doc,
    ["Rank", "Region", "Predicted Stunting", "WHO Band", "Cluster", "Forecast 2028"],
    [
        ("1",  "North",     "40.8%", "Critical", "Northern-rural", "40.4%"),
        ("2",  "Far North", "39.4%", "Critical", "Northern-rural", "39.2%"),
        ("3",  "Adamawa",   "39.3%", "High",     "Northern-rural", "37.1%"),
        ("4",  "East",      "34.3%", "High",     "Northern-rural", "33.8%"),
        ("5",  "South",     "27.3%", "Medium",   "Southern",       "26.7%"),
        ("6",  "Northwest", "23.7%", "Medium",   "Southern",       "23.4%"),
        ("7",  "West",      "21.5%", "Medium",   "Southern",       "21.2%"),
        ("8",  "Centre",    "21.0%", "Medium",   "Southern",       "20.5%"),
        ("9",  "Southwest", "20.9%", "Medium",   "Southern",       "20.5%"),
        ("10", "Littoral",  "18.1%", "Low",      "Southern",       "17.5%"),
    ],
    caption="Table 4.4: Top 10 predicted stunting hotspots (2018, Random Forest model)"
)
para(doc,
    "The North, Far North, and Adamawa regions are the clear priorities for intervention. "
    "These three regions form the Northern-rural cluster and are projected to remain in "
    "the High or Critical WHO band through 2028. The remaining six regions fall in the "
    "Southern cluster with Medium or Low stunting rates.")

heading(doc, "4.9  Web Application", level=2)
para(doc,
    "The project results are published through a Next.js web application. "
    "The home page shows key statistics, a choropleth map of Cameroon, and "
    "a top-10 hotspot table. Six analysis pages cover Hotspots, Regression, "
    "Classification, Clustering, Forecasts, and Hypothesis tests. "
    "The application is deployed on Railway and reads static JSON files "
    "generated from the pipeline output CSVs.")
figure(doc, "Home page — Cameroon Malnutrition Atlas web dashboard", "4.9")
figure(doc, "Hotspots page — choropleth map and ranked region table", "4.10")
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER FIVE
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, "CHAPTER FIVE: CONCLUSIONS AND RECOMMENDATIONS")

heading(doc, "5.1  Conclusions", level=2)
para(doc,
    "This project applied a CRISP-DM data mining pipeline to Cameroon DHS sub-national "
    "data and produced a ranked, predictive hotspot map of child stunting. "
    "The following conclusions are drawn:")
bullet(doc,
    "Random Forest achieved the best regression performance with a CV RMSE of 3.64 pp — "
    "a 71% improvement over the mean-prediction baseline (p < 0.001).")
bullet(doc,
    "A Random Forest classifier assigned WHO risk bands with 80% accuracy, enabling "
    "categorical targeting decisions.")
bullet(doc,
    "K-Means clustering (k = 2, silhouette = 0.52) identified a clear high-risk northern "
    "cluster (37% mean stunting) and a lower-risk southern cluster (24% mean stunting).")
bullet(doc,
    "Five of six hypotheses were confirmed: healthcare access (rho = -0.77), WASH (rho = -0.50), "
    "socio-economic status (rho = -0.39), and maternal education (rho = -0.28) are all "
    "significant negative correlates of stunting.")
bullet(doc,
    "Linear forecasts project that North and Far North will remain in the WHO Critical or "
    "High band through 2028, underscoring the urgency of accelerated intervention.")
bullet(doc,
    "The North region is the single highest-priority target, with a predicted stunting "
    "rate of 40.8% in 2018 and a very slow improvement trajectory.")

heading(doc, "5.2  Limitations", level=2)
bullet(doc,
    "The dataset contains only 50 observations (10 regions x 5 years), which limits "
    "the statistical power of the models.")
bullet(doc,
    "All associations are correlational. The study does not establish causation.")
bullet(doc,
    "Linear forecasts assume a constant rate of change and do not capture policy shocks "
    "or abrupt improvements.")

heading(doc, "5.3  Perspectives for Further Study", level=2)
bullet(doc,
    "Incorporate the upcoming 2024/2025 DHS wave to update and re-validate predictions.")
bullet(doc,
    "Apply spatial regression models to account for geographic spillover effects "
    "between neighbouring regions.")
bullet(doc,
    "Extend the web application with a reporting module so that district health officers "
    "can generate printable risk summaries directly from the dashboard.")
page_break(doc)


# ══════════════════════════════════════════════════════════════════════════════
# REFERENCES
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, "REFERENCES")
refs = [
    "Chapman, P., Clinton, J., Kerber, R., Khabaza, T., Reinartz, T., Shearer, C., & Wirth, R. "
    "(2000). CRISP-DM 1.0: Step-by-step data mining guide. SPSS Inc.",

    "DHS Programme. (2018). Cameroon Demographic and Health Survey 2018. ICF International.",

    "DHS Programme. (2011). Cameroon Demographic and Health Survey 2011. ICF International.",

    "Humanitarian Data Exchange (HDX). (2024). Cameroon datasets. OCHA. https://data.humdata.org",

    "Kometa, N. (2026). CEC 420: Data Mining — Unit 2: Classification, Prediction and Clustering. "
    "University of Buea, College of Technology.",

    "Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. "
    "Journal of Machine Learning Research, 12, 2825-2830.",

    "UNICEF, WHO & World Bank. (2023). Levels and Trends in Child Malnutrition: "
    "Joint Child Malnutrition Estimates 2023 Edition. World Health Organization.",

    "WHO. (2014). Global Nutrition Targets 2025: Stunting Policy Brief. World Health Organization.",
]
for i, ref in enumerate(refs, 1):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent       = Cm(1.25)
    p.paragraph_format.first_line_indent = Cm(-1.25)
    p.paragraph_format.space_after       = Pt(6)
    _set_spacing(p.paragraph_format)
    r = p.add_run(ref)
    r.font.name      = "Times New Roman"
    r.font.size      = Pt(11)
    r.font.color.rgb = BLACK


# ──────────────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUT), exist_ok=True)
doc.save(OUT)
print(f"Saved -> {OUT}")
