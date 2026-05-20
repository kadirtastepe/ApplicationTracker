#!/usr/bin/env python3
"""Generate PhDApplications.html from PhDApplications.csv"""

import csv
import sys
from datetime import date

# ── CSS ──────────────────────────────────────────────────────────────────────

CSS = """\
        body {
            font-family: Arial, sans-serif;
            margin: 10px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
            font-size: 1.5em;
            margin: 10px 0;
        }
        table {
            width: 100%;
            max-width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 0.85em;
        }
        th, td {
            padding: 8px 6px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #2c3e50;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
            cursor: pointer;
            user-select: none;
        }
        th:hover {
            background-color: #34495e;
        }
        th.sortable::after {
            content: ' ↕';
            opacity: 0.5;
        }
        th.sort-asc::after {
            content: ' ↑';
            opacity: 1;
        }
        th.sort-desc::after {
            content: ' ↓';
            opacity: 1;
        }
        .num-cell {
            text-align: center;
            font-weight: bold;
            color: #666;
            width: 30px;
        }
        tr.highlight-row {
            background-color: #fffde7;  /* very light yellow */
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        .days-cell {
            font-weight: bold;
            text-align: center;
            padding: 6px;
            border-radius: 4px;
            white-space: nowrap;
        }
        /* Color scheme based on days */
        .days-0-7   { background-color: #d4edda; color: #155724; }
        .days-8-14  { background-color: #d1ecf1; color: #0c5460; }
        .days-15-30 { background-color: #cce5ff; color: #004085; }
        .days-31-50 { background-color: #fff3cd; color: #856404; }
        .days-51-75 { background-color: #ffe0b2; color: #e65100; }
        .days-76-100 { background-color: #ffccbc; color: #d84315; }
        .days-101-plus { background-color: #f8d7da; color: #721c24; }"""

# ── JavaScript ───────────────────────────────────────────────────────────────

JS = """\
        function parseDate(dateStr) {
            if (!dateStr || dateStr.trim() === '') return null;

            // Handle formats like "7.6.2025" or "01.01.26"
            const parts = dateStr.split('.');
            if (parts.length === 3) {
                let day = parseInt(parts[0]);
                let month = parseInt(parts[1]) - 1; // Month is 0-indexed
                let year = parseInt(parts[2]);

                // Handle 2-digit years
                if (year < 100) {
                    year += 2000;
                }

                return new Date(year, month, day);
            }
            return null;
        }

        function calculateDays(appDateStr, respDateStr) {
            const appDate = parseDate(appDateStr);
            if (!appDate) return null;

            const endDate = respDateStr && respDateStr.trim() !== ''
                ? parseDate(respDateStr)
                : new Date();

            if (!endDate) return null;

            const diffTime = Math.abs(endDate - appDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            return diffDays;
        }

        function getColorClass(days) {
            if (days <= 7)   return 'days-0-7';
            if (days <= 14)  return 'days-8-14';
            if (days <= 30)  return 'days-15-30';
            if (days <= 50)  return 'days-31-50';
            if (days <= 75)  return 'days-51-75';
            if (days <= 100) return 'days-76-100';
            return 'days-101-plus';
        }

        function updateDays() {
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length < 8) return;

                const appDateCell = cells[5]; // Date of Application
                const respDateCell = cells[6]; // Date of Response
                const daysCell = cells[7];     // Days Past

                const appDateStr = appDateCell.textContent.trim();
                const respDateStr = respDateCell.textContent.trim();

                const days = calculateDays(appDateStr, respDateStr);

                if (days !== null) {
                    daysCell.textContent = days + (days === 1 ? ' day' : ' days');

                    // Only apply color if no response date (pending application)
                    if (!respDateStr || respDateStr === '') {
                        daysCell.className = 'days-cell ' + getColorClass(days);
                    } else {
                        daysCell.className = '';
                    }
                }
            });
        }

        function sortTable(columnIndex, th) {
            const table = document.querySelector('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            // Determine sort direction
            const currentSort = th.classList.contains('sort-asc') ? 'asc' :
                               th.classList.contains('sort-desc') ? 'desc' : null;
            let newSort = currentSort === 'asc' ? 'desc' : 'asc';

            // Remove sort classes from all headers
            document.querySelectorAll('th').forEach(header => {
                header.classList.remove('sort-asc', 'sort-desc');
            });

            // Add sort class to current header
            th.classList.add('sort-' + newSort);

            // Sort rows
            rows.sort((a, b) => {
                let aValue = a.cells[columnIndex].textContent.trim();
                let bValue = b.cells[columnIndex].textContent.trim();

                // Handle empty values
                if (!aValue && !bValue) return 0;
                if (!aValue) return 1;
                if (!bValue) return -1;

                // Try to parse as number (for Days Past column)
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return newSort === 'asc' ? aNum - bNum : bNum - aNum;
                }

                // Try to parse as date
                const aDate = parseDate(aValue);
                const bDate = parseDate(bValue);
                if (aDate && bDate) {
                    return newSort === 'asc' ? aDate - bDate : bDate - aDate;
                }

                // Default to string comparison
                return newSort === 'asc' ?
                    aValue.localeCompare(bValue) :
                    bValue.localeCompare(aValue);
            });

            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));

            // Update row numbers
            rows.forEach((row, index) => {
                row.querySelector('.num-cell').textContent = index + 1;
            });
        }

        function initializeSorting() {
            const headers = document.querySelectorAll('th');
            headers.forEach((th, index) => {
                th.classList.add('sortable');
                th.addEventListener('click', () => sortTable(index, th));
            });
        }

        // Update on page load
        window.addEventListener('DOMContentLoaded', () => {
            updateDays();
            initializeSorting();
        });"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_date(date_str):
    """Parse D.M.YYYY or D.M.YY date strings."""
    if not date_str or not date_str.strip():
        return None
    parts = date_str.strip().split('.')
    if len(parts) == 3:
        try:
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])
            if year < 100:
                year += 2000
            return date(year, month, day)
        except (ValueError, TypeError):
            return None
    return None


def calculate_days(app_date_str, resp_date_str):
    """Days from application to response (or today if still pending)."""
    app_date = parse_date(app_date_str)
    if not app_date:
        return None
    end_date = parse_date(resp_date_str) if resp_date_str and resp_date_str.strip() else date.today()
    if not end_date:
        return None
    return abs((end_date - app_date).days)


def get_color_class(days):
    if days <= 7:   return 'days-0-7'
    if days <= 14:  return 'days-8-14'
    if days <= 30:  return 'days-15-30'
    if days <= 50:  return 'days-31-50'
    if days <= 75:  return 'days-51-75'
    if days <= 100: return 'days-76-100'
    return 'days-101-plus'


def h(text):
    """Minimal HTML escaping."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


# ── HTML generation ───────────────────────────────────────────────────────────

def build_row(index, row):
    position    = h(row[0].strip())                           if len(row) > 0 else ''
    preselected = h(row[1].strip())                           if len(row) > 1 else ''
    interview   = h(row[2].strip())                           if len(row) > 2 else ''
    final       = h(row[3].strip())                           if len(row) > 3 else ''
    app_date    = h(row[4].strip())                           if len(row) > 4 else ''
    resp_date   = h(row[5].strip())                           if len(row) > 5 else ''

    # Decide if this row should be highlighted: has "Successful" but no "Failed"
    raw_success = any("Successful" in (c or "") for c in row)
    raw_failed  = any("Failed"     in (c or "") for c in row)
    row_class = ' class="highlight-row"' if raw_success and not raw_failed else ''

    days = calculate_days(app_date, resp_date)
    days_text = (f'{days} day' if days == 1 else f'{days} days') if days is not None else ''
    is_pending = not (row[5].strip() if len(row) > 5 else '')

    if is_pending and days is not None:
        days_td = f'<td class="days-cell {get_color_class(days)}">{days_text}</td>'
    else:
        days_td = f'<td>{days_text}</td>'

    return (
        f'            <tr{row_class}>\n'
        f'                <td class="num-cell">{index}</td>\n'
        f'                <td>{position}</td>\n'
        f'                <td>{preselected}</td>\n'
        f'                <td>{interview}</td>\n'
        f'                <td>{final}</td>\n'
        f'                <td>{app_date}</td>\n'
        f'                <td>{resp_date}</td>\n'
        f'                {days_td}\n'
        f'            </tr>'
    )


def generate_html(rows):
    tbody = '\n'.join(build_row(i, r) for i, r in enumerate(rows, 1))
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhD Applications Tracker</title>
    <style>
{CSS}
    </style>
    <script>
{JS}
    </script>
</head>
<body>
    <h1>PhD Applications Status Tracker</h1>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Position</th>
                <th>Pre-selected</th>
                <th>Interview</th>
                <th>Final Status</th>
                <th>Date of Application</th>
                <th>Date of Response</th>
                <th>Days Past</th>
            </tr>
        </thead>
        <tbody>
{tbody}
        </tbody>
    </table>
</body>
</html>
"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <input.csv> <output.html>', file=sys.stderr)
        sys.exit(1)

    csv_path, html_path = sys.argv[1], sys.argv[2]

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)  # skip header row
        rows = list(reader)

    html = generate_html(rows)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'Generated {html_path} ({len(rows)} entries).')


if __name__ == '__main__':
    main()
