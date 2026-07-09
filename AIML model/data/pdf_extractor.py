"""
PDF Text Extractor — Extract structured text from government notification PDFs.

Indian government portals (UPSC, SSC, IBPS, etc.) publish notifications as PDFs.
This module extracts text, tables, and structured data from those PDFs for ML processing.
"""

import re
import os
from typing import Dict, List, Optional


def extract_text_from_pdf(pdf_path: str) -> Dict:
    """
    Extract text from a PDF file using pdfplumber (primary) or PyMuPDF (fallback).
    
    Returns:
        Dict with 'text', 'pages', 'tables', 'metadata'
    """
    result = {
        'text': '',
        'pages': [],
        'tables': [],
        'metadata': {},
        'page_count': 0,
        'extraction_method': None,
    }

    # Try pdfplumber first (better for table extraction)
    try:
        result = _extract_with_pdfplumber(pdf_path)
        result['extraction_method'] = 'pdfplumber'
        return result
    except Exception:
        pass

    # Fallback to PyMuPDF
    try:
        result = _extract_with_pymupdf(pdf_path)
        result['extraction_method'] = 'pymupdf'
        return result
    except Exception as e:
        result['error'] = str(e)
        return result


def _extract_with_pdfplumber(pdf_path: str) -> Dict:
    """Extract using pdfplumber — best for structured PDFs with tables."""
    import pdfplumber

    pages = []
    tables = []
    full_text = []

    with pdfplumber.open(pdf_path) as pdf:
        metadata = {
            'page_count': len(pdf.pages),
            'metadata': pdf.metadata or {},
        }

        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ''
            pages.append({
                'page_num': i + 1,
                'text': page_text,
                'width': page.width,
                'height': page.height,
            })
            full_text.append(page_text)

            # Extract tables
            page_tables = page.extract_tables()
            if page_tables:
                for table in page_tables:
                    cleaned_table = _clean_table(table)
                    if cleaned_table:
                        tables.append({
                            'page_num': i + 1,
                            'data': cleaned_table,
                        })

    return {
        'text': '\n\n'.join(full_text),
        'pages': pages,
        'tables': tables,
        'metadata': metadata,
        'page_count': len(pages),
    }


def _extract_with_pymupdf(pdf_path: str) -> Dict:
    """Extract using PyMuPDF — faster, better for image-heavy PDFs."""
    import fitz  # PyMuPDF

    pages = []
    full_text = []

    doc = fitz.open(pdf_path)
    metadata = {
        'page_count': len(doc),
        'metadata': doc.metadata or {},
    }

    for i, page in enumerate(doc):
        page_text = page.get_text("text")
        pages.append({
            'page_num': i + 1,
            'text': page_text,
            'width': page.rect.width,
            'height': page.rect.height,
        })
        full_text.append(page_text)

    doc.close()

    return {
        'text': '\n\n'.join(full_text),
        'pages': pages,
        'tables': [],
        'metadata': metadata,
        'page_count': len(pages),
    }


def _clean_table(table: List[List]) -> List[List[str]]:
    """Clean extracted table data — remove empty rows/cols, normalize text."""
    if not table:
        return []

    cleaned = []
    for row in table:
        if row is None:
            continue
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append('')
            else:
                cell_str = str(cell).strip()
                cell_str = re.sub(r'\s+', ' ', cell_str)
                cleaned_row.append(cell_str)
        # Skip completely empty rows
        if any(c for c in cleaned_row):
            cleaned.append(cleaned_row)

    return cleaned


def extract_pdf_from_url(url: str, save_dir: str = '/tmp/pdfs') -> Optional[Dict]:
    """
    Download a PDF from URL and extract text.
    
    Args:
        url: URL of the PDF
        save_dir: Directory to save downloaded PDFs
    
    Returns:
        Dict with extracted data, or None on failure
    """
    import requests

    os.makedirs(save_dir, exist_ok=True)
    filename = re.sub(r'[^\w\-.]', '_', url.split('/')[-1])
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    filepath = os.path.join(save_dir, filename)

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()

        # Verify it's actually a PDF
        if not response.content[:5] == b'%PDF-':
            return None

        with open(filepath, 'wb') as f:
            f.write(response.content)

        result = extract_text_from_pdf(filepath)
        result['source_url'] = url
        result['local_path'] = filepath
        return result

    except Exception as e:
        return {'error': str(e), 'source_url': url}


def extract_vacancy_table(tables: List[Dict]) -> List[Dict]:
    """
    Parse vacancy/post tables from extracted PDF tables.
    
    Government PDFs typically have tables like:
    | Post Name | Category | Vacancies | Pay Scale |
    | Scientist B | UR: 10, OBC: 5, SC: 3 | 18 | Level 10 |
    """
    vacancy_data = []

    for table_info in tables:
        table = table_info.get('data', [])
        if len(table) < 2:
            continue

        # Try to identify vacancy columns by header
        header = [str(h).lower() for h in table[0]]
        post_col = _find_column(header, ['post', 'name', 'designation', 'position'])
        vacancy_col = _find_column(header, ['vacanc', 'posts', 'no.', 'number', 'total'])
        category_col = _find_column(header, ['category', 'reservation', 'ur', 'gen'])
        pay_col = _find_column(header, ['pay', 'salary', 'scale', 'level', 'grade'])

        if post_col is None and vacancy_col is None:
            continue

        for row in table[1:]:
            if len(row) <= max(filter(None, [post_col, vacancy_col, category_col, pay_col]), default=0):
                continue

            entry = {}
            if post_col is not None and post_col < len(row):
                entry['post_name'] = row[post_col]
            if vacancy_col is not None and vacancy_col < len(row):
                # Extract number from vacancy cell
                vac_text = str(row[vacancy_col])
                nums = re.findall(r'\d+', vac_text)
                entry['vacancies'] = int(nums[0]) if nums else 0
                entry['vacancy_raw'] = vac_text
            if category_col is not None and category_col < len(row):
                entry['category_breakdown'] = row[category_col]
            if pay_col is not None and pay_col < len(row):
                entry['pay_scale'] = row[pay_col]

            if entry:
                vacancy_data.append(entry)

    return vacancy_data


def extract_cutoff_table(tables: List[Dict]) -> List[Dict]:
    """
    Parse cutoff/merit tables from extracted PDF tables.
    
    Typical cutoff tables:
    | Category | Tier-I Cutoff | Tier-II Cutoff | Final Cutoff |
    | General  | 142.50       | 305.25        | 447.75       |
    """
    cutoff_data = []

    for table_info in tables:
        table = table_info.get('data', [])
        if len(table) < 2:
            continue

        header = [str(h).lower() for h in table[0]]

        # Check if this looks like a cutoff table
        is_cutoff_table = any(
            keyword in ' '.join(header)
            for keyword in ['cutoff', 'cut-off', 'qualifying', 'marks', 'merit', 'score']
        )
        has_category = any(
            keyword in ' '.join(header)
            for keyword in ['category', 'general', 'ur', 'obc', 'sc', 'st', 'ews']
        )

        if not (is_cutoff_table or has_category):
            continue

        cat_col = _find_column(header, ['category', 'cat', 'class'])
        marks_cols = []
        for i, h in enumerate(header):
            if any(kw in h for kw in ['cutoff', 'cut-off', 'marks', 'score', 'qualifying', 'merit']):
                marks_cols.append(i)

        if not marks_cols:
            # Try to find numeric columns
            if len(table) > 1:
                for i in range(len(header)):
                    if i != cat_col and re.search(r'\d+\.?\d*', str(table[1][i]) if i < len(table[1]) else ''):
                        marks_cols.append(i)

        for row in table[1:]:
            entry = {}
            if cat_col is not None and cat_col < len(row):
                entry['category'] = row[cat_col]
            else:
                entry['category'] = 'General'

            for mc in marks_cols:
                if mc < len(row):
                    marks_text = str(row[mc])
                    marks_nums = re.findall(r'[\d.]+', marks_text)
                    if marks_nums:
                        col_name = header[mc] if mc < len(header) else f'marks_{mc}'
                        entry[col_name] = float(marks_nums[0])

            if entry and len(entry) > 1:
                cutoff_data.append(entry)

    return cutoff_data


def _find_column(header: List[str], keywords: List[str]) -> Optional[int]:
    """Find column index by matching keywords in header."""
    for i, h in enumerate(header):
        for kw in keywords:
            if kw in h:
                return i
    return None
