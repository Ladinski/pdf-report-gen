import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.reports import get_report_data


data = get_report_data()

print(json.dumps(data, indent=2))