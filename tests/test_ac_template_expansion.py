import json
import os
import glob
import pytest
from src.adaptive_cards_templating_py import Template

# Discover all template files in the tests/templates subfolder
template_files = sorted(glob.glob('tests/templates/*.json'))

@pytest.mark.parametrize("template_path", template_files)
def test_adaptive_card_template_expansion(template_path):
    test_file_name = os.path.basename(template_path)
    # Load template
    with open(f'tests/templates/{test_file_name}', 'r') as file:
        template = json.load(file)

    # Load optional data and host_data
    root_data = None
    data_path = f'tests/root_data/{test_file_name}'
    if os.path.exists(data_path):
        with open(data_path, 'r') as file:
            root_data = json.load(file)

    host_data = None
    host_data_path = f'tests/host_data/{test_file_name}'
    if os.path.exists(host_data_path):
        with open(host_data_path, 'r') as file:
            host_data = json.load(file)

    act = Template(template)
    expanded = act.expand({'$root': root_data, '$host': host_data })
    print (f"\nExpanded template for {test_file_name}:\n{json.dumps(expanded, indent=2, ensure_ascii=False)}")

    expected_path = f'tests/expected_output/{test_file_name}'
    with open(expected_path, 'r') as file:
        expected = json.load(file)
    assert expanded == expected