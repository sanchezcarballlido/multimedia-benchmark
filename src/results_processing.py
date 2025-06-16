# src/vaf/pipeline.py
import os
import pandas as pd
import xml.etree.ElementTree as ET
import re

def _extract_from_log(log_content, pattern):
    match = re.search(pattern, log_content)
    return float(match.group(1)) if match else None

def _extract_vmaf_from_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        vmaf_score = tree.find('.//metric[@name="vmaf"]').attrib['mean']
        return float(vmaf_score)
    except (ET.ParseError, FileNotFoundError, AttributeError):
        return None

def process_results(results_dir):
    all_data = []
    for root, _, files in os.walk(results_dir):
        for file in files:
            if file.endswith("_encoding.log"):
                parts = root.replace(results_dir, '').strip(os.sep).split(os.sep)
                if len(parts) < 3: continue

                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()

                data = {
                    'codec': parts[0],
                    'crf': parts[1],
                    'resolution': parts[2],
                    'preset': file.split('_')[1],
                    'bitrate_kbps': _extract_from_log(content, r"bitrate=\s*(\d+\.?\d*)\s*kbits/s"),
                    'vmaf': _extract_vmaf_from_xml(os.path.join(root, file.replace("_encoding.log", "_vmaf.log")))
                }
                all_data.append(data)
    
    if not all_data:
        print("Advertencia: No se procesaron datos. Verifica la estructura de carpetas y los logs.")
        return

    df = pd.DataFrame(all_data)
    df.to_csv(os.path.join(results_dir, "combined_data.csv"), index=False)