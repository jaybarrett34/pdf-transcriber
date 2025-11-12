#!/usr/bin/env python3
"""
Create test PDFs from text files for testing the PDF transcriber.
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import textwrap
import os

def create_pdf_from_text(text_file, output_pdf, font_size=11, line_spacing=14):
    """
    Convert a text file to a PDF with proper formatting.
    """
    # Read the text file
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create PDF
    c = canvas.Canvas(output_pdf, pagesize=letter)
    width, height = letter

    # Set margins
    left_margin = 1 * inch
    right_margin = width - 1 * inch
    top_margin = height - 0.75 * inch
    bottom_margin = 0.75 * inch

    # Calculate usable width for text
    usable_width = right_margin - left_margin
    chars_per_line = int(usable_width / (font_size * 0.5))  # Approximate

    # Current position
    y_position = top_margin

    # Process content line by line
    lines = content.split('\n')

    for line in lines:
        if not line.strip():
            # Empty line
            y_position -= line_spacing
            if y_position < bottom_margin:
                c.showPage()
                y_position = top_margin
            continue

        # Wrap long lines
        wrapped_lines = textwrap.wrap(line, width=chars_per_line)

        for wrapped_line in wrapped_lines:
            # Check if we need a new page
            if y_position < bottom_margin:
                c.showPage()
                y_position = top_margin

            # Draw the text
            c.setFont("Helvetica", font_size)
            c.drawString(left_margin, y_position, wrapped_line)
            y_position -= line_spacing

    # Save the PDF
    c.save()
    print(f"Created PDF: {output_pdf}")

if __name__ == "__main__":
    # Create output directory if it doesn't exist
    os.makedirs("test_pdfs", exist_ok=True)

    # Create PDFs from text files
    print("Creating test PDFs...")
    create_pdf_from_text("modern_english.txt", "test_pdfs/modern_english.pdf")
    create_pdf_from_text("old_english.txt", "test_pdfs/old_english.pdf")
    print("\nTest PDFs created successfully!")
    print("Files:")
    print("  - test_pdfs/modern_english.pdf")
    print("  - test_pdfs/old_english.pdf")
