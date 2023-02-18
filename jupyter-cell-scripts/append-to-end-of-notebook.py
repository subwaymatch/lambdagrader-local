# LambdaGrader After File Code
# REMOVE_IN_HTML_OUTPUT
grader_output_file_name = 'lambdagrader-result.json'
grading_end_time = datetime.now()

_graded_result['grading_finished_at'] = grading_end_time.isoformat()
_graded_result['grading_duration_in_seconds'] = round((grading_end_time - grading_start_time).total_seconds(), 2)
_graded_result['learner_score'] = 0
_graded_result['total_available'] = 0
_graded_result['num_test_cases'] = len(_graded_result['results'])
_graded_result['num_passed_cases'] = 0
_graded_result['num_failed_cases'] = 0

for test_case_result in _graded_result['results']:
    _graded_result['learner_score'] += test_case_result['points']
    _graded_result['total_available'] += test_case_result['available_points']
    
    if test_case_result['pass']:
        _graded_result['num_passed_cases'] += 1
    else:
        _graded_result['num_failed_cases'] += 1

print(_graded_result)
    
with open(grader_output_file_name, 'w') as fp:
    json.dump(_graded_result, fp)