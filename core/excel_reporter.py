from datetime import datetime
from openpyxl import Workbook
import os

class ExcelReporter:
    def __init__(self):
        os.makedirs("reports", exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.file_path = f"reports/test_execution_{timestamp}.xlsx"

        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.title = "Test Results"

        self.ws.append([
            "Test Name",
            "Status",
            "Layer",
            "Endpoint",
            "Severity",
            "Business Impact",
            "Release Blocker"
        ])

    def record(self, **data):
        self.ws.append([
            data.get("test_name"),
            data.get("status"),
            data.get("layer"),
            data.get("endpoint"),
            data.get("severity"),
            data.get("business_impact"),
            data.get("release_blocker")
        ])

        try:
            self.wb.save(self.file_path)
        except PermissionError:
            print(f"⚠️ Excel file locked, skipping save: {self.file_path}")
