import glob
import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
import re
import textwrap
import pandas as pd
import black
import hashlib

test_case_name_pattern = r'^\s*_test_case\s*=\s*[\'"](.*)[\'"]'
test_case_points_pattern = r'^\s*_points\s*=\s*(.*)[\s#]*.*[\r\n]'
grader_only_pattern = r'^\s*_grader_only\s*=\s*(True|False)'

def extract_test_case_metadata_from_cell(source: str) -> str:
    tc_result = re.search(
        test_case_name_pattern,
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
        test_case_points_pattern,
        source,
        flags=re.MULTILINE
    )
    
    # if the test case code cell does not include _points
    # no points will be assigned (default of zero)
    if points_result and len(tc_result.groups()) > 0:
        metadata['points'] = float(points_result.groups()[0])
        
    grader_only_result = re.search(
        grader_only_pattern,
        source,
        flags=re.MULTILINE
    )
    
    if grader_only_result and len(grader_only_result.groups()) > 0:
        metadata['grader_only'] = bool(grader_only_result.groups()[0])
    
    return metadata



def extract_test_cases_metadata_from_notebook(nb) -> str:
    metadata_list = []

    for cell in nb.cells:
        if cell.cell_type == 'code':
            test_case_metadata = extract_test_case_metadata_from_cell(cell.source)
            
            if test_case_metadata:
                metadata_list.append(test_case_metadata)
                
    return metadata_list



def does_cell_contain_test_case(cell) -> bool:
    tc_result = re.search(
        test_case_name_pattern,
        cell.source,
        flags=re.MULTILINE
    )
    
    return tc_result and (len(tc_result.groups()) > 0)



def convert_to_grader_code(source: str) -> str:
    indented_source = textwrap.indent(source, '    ')
    
    with open('jupyter-cell-scripts/grader-template.py') as f:
        grader_template_code = f.read()
        
    converted_source = grader_template_code.replace('# TEST_CASE_REPLACE_HERE', indented_source)
    
    return converted_source



def add_grader_scripts(nb):
    with open('jupyter-cell-scripts/prepend-to-start-of-notebook.py') as f:
        prepend_script = f.read()
        prepend_cell = new_code_cell(prepend_script)
    
    with open('jupyter-cell-scripts/append-to-end-of-notebook.py') as f:
        append_script = f.read()
        append_cell = new_code_cell(append_script)
    
    nb.cells.insert(0, prepend_cell)
    nb.cells.append(append_cell)


    
def remove_grader_scripts(nb):
    # remove prepend, append cells added by LambdaGrader before storing to HTML
    nb.cells.pop(0)  # first cell (added by LambdaGrader)
    nb.cells.pop()   # last cell (added by LambdaGrader)
    
    return nb



# TODO: The current code only extracts code between # YOUR CODE BEGINS and # YOUR CODE ENDS
# This will not work if a learner changes or deletes the comments
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



def extract_user_code_from_notebook(nb) -> str:
    full_code = ''

    for cell in nb.cells:
        if cell.cell_type == 'code':
            student_code = extract_user_code_from_cell_source(cell.source)

            if student_code:
                full_code += student_code + '\n\n'
                
    return full_code



def remove_comments(source: str) -> str:
    pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|#[^\r\n]*$)"
    # first group captures quoted strings (double or single)
    # second group captures comments (# single-line or /* multi-line */)
    regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
    def _replacer(match):
        # if the 2nd group (capturing comments) is not None,
        # it means we have captured a non-quoted (real) comment string.
        if match.group(2) is not None:
            return "" # so we will return empty to remove the comment
        else: # otherwise, we will return the 1st group
            return match.group(1) # captured quoted-string
    return regex.sub(_replacer, source)



def get_test_cases_hash(nb) -> str:
    test_cases_code = ''

    for cell in nb.cells:
        if (cell.cell_type == 'code') and does_cell_contain_test_case(cell):
            # standardize code before hasing
            # by removing comments and formatting the code using the Black formatter
            standardized_code = remove_comments(cell.source)
            standardized_code = black.format_str(standardized_code, mode=black.Mode())
            
            # concatenate to test_cases_code
            test_cases_code += standardized_code
    
    # generate an MD5 hash
    hash_str = hashlib.md5(test_cases_code.encode('utf-8')).hexdigest()
    return hash_str



def generate_text_summary(graded_result) -> str:
    summary = ''
    summary += f"File: {graded_result['filename']}\n"
    summary += f"Score: {graded_result['learner_score']} out of {graded_result['total_available']}\n"
    summary += f"Passed {graded_result['num_passed_cases']} out of {graded_result['num_test_cases']} test cases\n"
    summary += f"Grading took {graded_result['grading_duration_in_seconds']} seconds\n\n"
    summary += 'Test Case Summary\n'

    for o in graded_result['results']:
        summary += "-----------------\n"
        summary += f"{o['test_case_name']} {'passed' if o['pass'] else 'failed'}: {o['points']} out of {o['available_points']} points\n"

        if not o['pass']:
            summary += f"[Autograder Output]\n{o['message']}\n\n"
            
    return summary



def add_graded_result(nb, graded_result):
    insert_index = 0
    graded_result_cells = []

    # add result summary
    graded_result_cells.append(new_markdown_cell('# 🧭 LambdaGrader Summary'))
    graded_result_cells.append(new_markdown_cell('## Metadata'))
    
    graded_result_dict_for_df = {
        'graded_filename': graded_result['filename'],
        'grading_finished_at': graded_result['grading_finished_at'],
        'grading_duration': f"{graded_result['grading_duration_in_seconds']} second{'' if graded_result['grading_duration_in_seconds'] == 0 else 's'}",
        '**learner_score**': f"**{graded_result['learner_score']}**",
        'max_score': graded_result['total_available'],
        'learner_score_in_percentage': f"{round(graded_result['learner_score'] / graded_result['total_available'] * 100, 2)}%",
        'num_test_cases': graded_result['num_test_cases'],
        'num_passed_cases': graded_result['num_passed_cases'],
        'num_failed_cases': graded_result['num_failed_cases'],
        'test_cases_hash': graded_result['test_cases_hash'],
        'grader_python_version': f"Python {graded_result['grader_python_version']}",
        'grader_platform': graded_result['grader_platform']
    }
    
    df_metadata = pd.DataFrame({
        'name': graded_result_dict_for_df.keys(),
        'value': graded_result_dict_for_df.values()
    })
    graded_result_cells.append(new_markdown_cell(df_metadata.to_markdown(index=False)))

    graded_result_cells.append(new_markdown_cell('## Test case results'))

    df_r = pd.DataFrame(graded_result['results'])
    df_r['pass'] = df_r['pass'].map({
        True: '✔️ Pass', False: '❌ Fail'
    })
    df_r.rename(columns={
        'available_points': 'max_score',
        'points': 'learner_score',
        'pass': 'result'
    }, inplace=True)

    graded_result_cells.append(new_markdown_cell(df_r.to_markdown()))
    graded_result_cells.append(new_markdown_cell('\n---\n'))
    
    nb.cells = graded_result_cells + nb.cells
    
    return nb