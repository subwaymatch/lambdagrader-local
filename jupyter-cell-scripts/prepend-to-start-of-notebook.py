# LambdaGrader Before File Code
# REMOVE_IN_HTML_OUTPUT
import traceback
import json
from datetime import datetime

grading_start_time = datetime.now()

_graded_result = {
    'grading_finished_at': None,
    'grading_duration_in_seconds': 0,
    'learner_score': 0,
    'total_available': 0,
    'num_test_cases': 0,
    'num_passed_cases': 0,
    'num_failed_cases': 0,
    'results': []
}

is_lambdagrader_env = True

def _record_test_case(test_case_name, did_pass, available_points, message=''):
    global _graded_result
    warning_message = ''
    
    if test_case_name in map(lambda x: x['test_case_name'], _graded_result['results']):
        warning_message = f'[Warning] LambdaGrader: An identical test case name "{test_case_name}" already exists. Test cases with identical test case names will be graded \n\n'

    _graded_result['results'].append({
        'test_case_name': test_case_name,
        'points': available_points if did_pass else 0,
        'available_points': available_points,
        'pass': did_pass,
        'message': warning_message + message,
    })