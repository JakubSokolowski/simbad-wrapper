import ntpath
import os
from typing import List

from reportlab.lib import utils
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image

from models.simulation import Artifact

IMAGE_WIDTH_CM = 13 * cm
LABEL_FONT_SIZE = 10
SUMMARY_REPORT_NAME = "simulation_report.pdf"


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def get_image(path: str, width=1 * cm) -> Image:
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect))


def build_label(text: str, styles) -> list:
    story = []
    label = '<font size={}>{}</font>'.format(LABEL_FONT_SIZE, text)
    story.append(Spacer(1, 12))
    story.append(Paragraph(label, styles["Center"]))
    story.append(Spacer(1, 12))
    return story


def build_labeled_plot(path: str, styles) -> list:
    plot = get_image(path, IMAGE_WIDTH_CM)
    plot_name = get_plot_name(path)
    label = build_label(plot_name, styles)
    return [plot] + label + [Spacer(1, 12)]


def get_plot_name(path: str) -> str:
    leaf = path_leaf(path)
    return os.path.splitext(leaf)[0]


def build_report_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    return styles


def build_summary_report(plots: List[Artifact], workdir: str) -> None:
    report_path = os.path.join(workdir, SUMMARY_REPORT_NAME)
    report = SimpleDocTemplate(report_path, pagesize=letter,
                               rightMargin=30, leftMargin=30,
                               topMargin=18, bottomMargin=18)
    styles = build_report_styles()
    story = []
    for plot in plots:
        story.extend(build_labeled_plot(plot.path, styles))
    report.build(story)
