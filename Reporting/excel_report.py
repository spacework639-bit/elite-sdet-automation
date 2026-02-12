import os
from datetime import datetime
from openpyxl import Workbook


def generate_report(session):
    os.makedirs("reports", exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Test Results"

    # Headers
    ws.append(["Test Name", "Outcome"])

    for item in session.items:
        outcome = "UNKNOWN"

        if hasattr(item, "rep_call"):
            if item.rep_call.passed:
                outcome = "PASSED"
            elif item.rep_call.failed:
                outcome = "FAILED"
            elif hasattr(item.rep_call, "wasxfail"):
                outcome = "XFAILED"
            elif item.rep_call.skipped:
                outcome = "SKIPPED"

        ws.append([item.name, outcome])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"reports/test_report_{timestamp}.xlsx"

    wb.save(report_path)
