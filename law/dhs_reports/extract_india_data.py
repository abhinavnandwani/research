#!/usr/bin/env python3
"""
Extract India student visa overstay data from DHS reports and create visualization
"""

import pdfplumber
import re
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def extract_india_student_data(pdf_path, fiscal_year):
    """Extract India student/exchange visitor overstay data from a DHS PDF report"""
    print(f"\nProcessing {pdf_path.name} (FY{fiscal_year})...")

    data = {
        'fiscal_year': fiscal_year,
        'total_expected_departures': None,
        'total_overstays': None,
        'overstay_rate': None,
        'suspected_in_country': None,
        'suspected_in_country_rate': None
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            # Look for India in student/exchange visitor tables
            # Common patterns in DHS reports:
            # - "India" followed by numbers
            # - Tables with country names and overstay statistics

            lines = full_text.split('\n')
            for i, line in enumerate(lines):
                # Look for India in the context of student/exchange visitors
                if 'India' in line or 'INDIA' in line:
                    # Check surrounding lines for context
                    context = '\n'.join(lines[max(0, i-3):min(len(lines), i+10)])

                    # Try to extract numbers from the line
                    # Look for patterns like: India 123,456 7,890 6.41 5,678 4.60
                    numbers = re.findall(r'[\d,]+\.?\d*', line)

                    if numbers and ('Student' in context or 'Exchange' in context or
                                   'F-1' in context or 'M-1' in context or 'J-1' in context):
                        print(f"Found India data: {line}")
                        print(f"Context:\n{context}")

                        # Try to parse the numbers
                        cleaned_numbers = [n.replace(',', '') for n in numbers]
                        if len(cleaned_numbers) >= 3:
                            try:
                                data['total_expected_departures'] = int(cleaned_numbers[0])
                                data['total_overstays'] = int(cleaned_numbers[1])

                                # Look for percentage rates
                                for num in cleaned_numbers[2:]:
                                    if '.' in num:
                                        rate = float(num)
                                        if 0 < rate < 100:  # Reasonable percentage range
                                            if data['overstay_rate'] is None:
                                                data['overstay_rate'] = rate
                                            elif data['suspected_in_country_rate'] is None:
                                                data['suspected_in_country_rate'] = rate

                                # Try to get suspected in-country count
                                if len(cleaned_numbers) >= 4:
                                    for num in cleaned_numbers[2:]:
                                        if '.' not in num and int(num) < data['total_overstays']:
                                            data['suspected_in_country'] = int(num)
                                            break

                            except (ValueError, IndexError) as e:
                                print(f"Error parsing numbers: {e}")

                        break

    except Exception as e:
        print(f"Error processing {pdf_path.name}: {e}")

    return data

def main():
    # List of PDF files to process
    pdf_files = [
        ('fy2018.pdf', 2018),
        ('fy2019.pdf', 2019),
        ('fy2020.pdf', 2020),
        ('fy2022.pdf', 2022),
        ('fy2023.pdf', 2023),
        ('fy2024.pdf', 2024),
    ]

    results = []
    base_path = Path('.')

    for pdf_file, fy in pdf_files:
        pdf_path = base_path / pdf_file
        if pdf_path.exists():
            data = extract_india_student_data(pdf_path, fy)
            results.append(data)
        else:
            print(f"Warning: {pdf_file} not found")

    # Create DataFrame
    df = pd.DataFrame(results)
    print("\n" + "="*80)
    print("EXTRACTED DATA:")
    print("="*80)
    print(df.to_string(index=False))
    print("\n")

    # Save to CSV
    df.to_csv('india_student_overstay_data.csv', index=False)
    print("Data saved to india_student_overstay_data.csv")

    # Create visualization
    if not df['overstay_rate'].isna().all():
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # Plot 1: Overstay Rate over years
        valid_data = df[df['overstay_rate'].notna()]
        if len(valid_data) > 0:
            ax1.plot(valid_data['fiscal_year'], valid_data['overstay_rate'],
                    marker='o', linewidth=2, markersize=8, color='#2E86AB')
            ax1.set_xlabel('Fiscal Year', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Overstay Rate (%)', fontsize=12, fontweight='bold')
            ax1.set_title('India Student Visa Overstay Rate Over Time\n(DHS Entry/Exit Overstay Reports)',
                         fontsize=14, fontweight='bold', pad=20)
            ax1.grid(True, alpha=0.3)
            ax1.set_xticks(valid_data['fiscal_year'])

            # Add value labels on points
            for _, row in valid_data.iterrows():
                ax1.annotate(f"{row['overstay_rate']:.2f}%",
                           xy=(row['fiscal_year'], row['overstay_rate']),
                           xytext=(0, 10), textcoords='offset points',
                           ha='center', fontsize=9, fontweight='bold')

        # Plot 2: Total overstays (absolute numbers)
        valid_data2 = df[df['total_overstays'].notna()]
        if len(valid_data2) > 0:
            ax2.bar(valid_data2['fiscal_year'], valid_data2['total_overstays'],
                   color='#A23B72', alpha=0.7, width=0.6)
            ax2.set_xlabel('Fiscal Year', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Total Overstays (Count)', fontsize=12, fontweight='bold')
            ax2.set_title('India Student Visa Total Overstays\n(Absolute Numbers)',
                         fontsize=14, fontweight='bold', pad=20)
            ax2.grid(True, alpha=0.3, axis='y')
            ax2.set_xticks(valid_data2['fiscal_year'])

            # Add value labels on bars
            for _, row in valid_data2.iterrows():
                ax2.text(row['fiscal_year'], row['total_overstays'],
                        f"{int(row['total_overstays']):,}",
                        ha='center', va='bottom', fontsize=9, fontweight='bold')

        plt.tight_layout()
        plt.savefig('india_student_overstay_plot.png', dpi=300, bbox_inches='tight')
        print("Plot saved to india_student_overstay_plot.png")
        plt.close()
    else:
        print("Not enough data to create visualization")

    return df

if __name__ == '__main__':
    main()
