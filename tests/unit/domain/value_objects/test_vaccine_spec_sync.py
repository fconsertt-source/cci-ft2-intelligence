import json
import yaml
import pytest
from pathlib import Path
from src.domain.value_objects.vaccine_specification import VACCINE_CATALOGUE

# ملاحظة: سنبحث عن ملف YAML أولاً، وإذا لم نتحقق سنبحث عن JSON (بما أن الـ repo اسمه Json)
CONFIG_DIR = Path("config")

def load_external_library():
    yaml_file = CONFIG_DIR / "vaccine_library.yaml"
    json_file = CONFIG_DIR / "vaccine_library.json"
    
    if yaml_file.exists():
        with open(yaml_file, "r") as f:
            return yaml.safe_load(f)
    elif json_file.exists():
        with open(json_file, "r") as f:
            return json.load(f)
    else:
        pytest.fail("لم يتم العثور على ملف vaccine_library.yaml أو .json في مجلد config")

def test_python_catalogue_matches_external_source_of_truth():
    """
    هذا الاختبار يضمن أن القيم المكتوبة (hardcoded) في VACCINE_CATALOGUE
    لا تتعارض مع مصدر الحقيقة الخارجي (SSOT).
    """
    external_lib = load_external_library()
    
    mismatches = []
    
    for vaccine_key, python_spec in VACCINE_CATALOGUE.items():
        if vaccine_key not in external_lib:
            # لقاح موجود في بايثون وغير موجود في الملف الخارجي
            continue
            
        ext_spec = external_lib[vaccine_key]
        
        # فحص Shelf Life
        if python_spec.shelf_life_days != ext_spec["shelf_life_days"]:
            mismatches.append(
                f"{vaccine_key} shelf_life_days: Python={python_spec.shelf_life_days}, External={ext_spec['shelf_life_days']}"
            )
            
        # فحص VVM Type
        if python_spec.vvm_type != ext_spec.get("vvm_type"):
            mismatches.append(
                f"{vaccine_key} vvm_type: Python={python_spec.vvm_type}, External={ext_spec.get('vvm_type')}"
            )

    if mismatches:
        error_msg = "تم اكتشاف تعارض بين Python Code والملف الخارجي:\n" + "\n".join(mismatches)
        pytest.fail(error_msg)