import os
import re

def load_acupoint_data():
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_file_dir, "data", "acupoint.pos")

    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Split on either colon or Chinese colon
            parts = re.split(r'[:：]', line)
            if len(parts) != 2:
                continue

            symptom = parts[0].strip()
            rest = re.split(r'[，,]', parts[1])

            if len(rest) != 4:
                continue

            acupoint = rest[0].strip()
            file_name = rest[1].strip()
            try:
                x = int(rest[2].strip())
                y = int(rest[3].strip())
            except ValueError:
                continue

            data.append({
                'symptom': symptom,
                'acupoint': acupoint,
                'file_name': file_name,
                'x': x,
                'y': y
            })

    return data
