import glob
import nbformat
from nbformat.v4 import new_code_cell
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
import re
import textwrap

def extract_test_case_metadata(source: str) -> str:
    tc_result = re.search(
        r'^\s*_test_case\s*=\s*[\'"](.*)[\'"]',
        source,
        flags=re.MULTILINE
    )
    
    if not tc_result or len(tc_result.groups()) == 0:
        return None
    
    metadata = {
        'test_case': tc_result.groups()[0],
        'points': 0,
        'grader_only': False
    }
    
    points_result = re.search(
        r'^\s*_points\s*=\s*(.*)[\s#]*.*[\r\n]',
        source,
        flags=re.MULTILINE
    )
    
    if points_result and len(tc_result.groups()) > 0:
        metadata['points'] = float(points_result.groups()[0])
        
    grader_only_result = re.search(
        r'^\s*_grader_only\s*=\s*(True|False)',
        source,
        flags=re.MULTILINE
    )
    
    if grader_only_result and len(grader_only_result.groups()) > 0:
        metadata['grader_only'] = bool(grader_only_result.groups()[0])
    
    return metadata



def convert_to_grader_code(source: str) -> str:
    indented_source = textwrap.indent(source, '    ')
    
    with open('jupyter-cell-scripts/grader-template.py') as f:
        grader_template_code = f.read()
        
    converted_source = grader_template_code.replace('# TEST_CASE_REPLACE_HERE', indented_source)
    
    return converted_source



def add_scripts_to_notebook(nb):
    with open('jupyter-cell-scripts/prepend-to-start-of-notebook.py') as f:
        prepend_script = f.read()
        prepend_cell = new_code_cell(prepend_script)
    
    with open('jupyter-cell-scripts/append-to-end-of-notebook.py') as f:
        append_script = f.read()
        append_cell = new_code_cell(append_script)
    
    nb.cells.insert(0, prepend_cell)
    nb.cells.append(append_cell)



def extract_user_code_from_cell_source(source: str) -> str:
    tc_result = re.search(
        r'.*# YOUR CODE BEGINS[\s\n]*(.*)# YOUR CODE ENDS',
        source,
        flags=re.MULTILINE | re.DOTALL
    )
    
    if not tc_result or len(tc_result.groups()) == 0:
        return None
    
    user_code = tc_result.groups()[0]
    
    user_code = user_code.rstrip()
    
    return user_code



def extract_user_code_from_notebook(notebook_path: str) -> str:
    full_code = ''
    nb = nbformat.read(notebook_path, as_version=4)

    for cell in nb.cells:
        if cell.cell_type == 'code':
            student_code = extract_user_code_from_cell_source(cell.source)

            if student_code:
                full_code += student_code + '\n\n'
                
    return full_code