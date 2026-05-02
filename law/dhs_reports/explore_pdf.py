#!/usr/bin/env python3
"""
Explore PDF structure to understand data format
"""

import pdfplumber
import sys

def explore_pdf(pdf_path):
    """Extract and print text from PDF to understand structure"""
    print(f"\n{'='*80}")
    print(f"Exploring: {pdf_path}")
    print(f"{'='*80}\n")

    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}\n")

        # Search for pages containing "India"
        india_pages = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and 'India' in text:
                india_pages.append((i+1, text))

        if india_pages:
            print(f"Found 'India' on {len(india_pages)} page(s): {[p[0] for p in india_pages]}\n")

            # Print text from first few pages containing India
            for page_num, text in india_pages[:3]:
                print(f"\n{'='*80}")
                print(f"PAGE {page_num} TEXT:")
                print(f"{'='*80}")
                print(text[:3000])  # Print first 3000 chars
                print("\n...")

                # Try extracting tables
                page = pdf.pages[page_num-1]
                tables = page.extract_tables()
                if tables:
                    print(f"\nTABLES FOUND ON PAGE {page_num}:")
                    for table_idx, table in enumerate(tables):
                        print(f"\nTable {table_idx + 1}:")
                        for row in table[:10]:  # Print first 10 rows
                            print(row)
        else:
            print("No pages containing 'India' found")

            # Print first few pages to understand structure
            print("\nFirst page text sample:")
            print(pdf.pages[0].extract_text()[:2000])

if __name__ == '__main__':
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else 'fy2024.pdf'
    explore_pdf(pdf_file)
