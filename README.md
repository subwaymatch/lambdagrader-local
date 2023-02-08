# LambdaGrader

Grade Jupyter notebooks on AWS Lambda

## Overview

This project aims to build a Jupyter notebook autograder that runs in a serverless environment. A single lambda invocation grades one Jupyter notebook.
Because AWS supports up to 1,000 concurrent executions by default, grading hundreds of submissions can be done simultaneously. 
The 1,000 concurrent execution limit can also be increased by request.

Another goal of this project is to make it easy for instructors to author a Jupyter notebook for teaching. 

### Workflow

![lambdagrader-diagram-01](https://user-images.githubusercontent.com/1064036/217484470-ab7406ce-bc0b-46a5-bbb2-17bb5fa8a2c7.png)

### Why not [nbgrader](https://github.com/jupyter/nbgrader)?

[nbgrader](https://github.com/jupyter/nbgrader) is widely used and is a great way to autograde Jupyter notebook assignments. 
I've personally used nbgrader in the past and it worked well.
However, there were a few limitations for our use case.

- Creating an nbgrader assignment requires the nbgrader Jupyter Lab extension.
- Working with multiple graders is challenging unless a JupyterHub shared by the instructional team is set up.
- nbgrader uses cell metadata, which cannot be viewed/edited in some Jupyter environments (e.g., [Google Colab](https://colab.research.google.com/)).
- There is a steep learning curve for graders who are not familiar with nbgrader.
- Concurrent grading occasionally crashed the server. For example, ~50 students submitting a graded quiz at the same time caused the grading to fail for multiple students. This may be specific to [Vocareum](https://vocareum.com/).

LambdaGrader uses regular code cells and text cells without an extension to author an autogradable Jupyter notebook.

## Jupyter notebook format

The instructor only authors one "solution" notebook. This notebook contains 

### Code cell for the learners

Any code between `# YOUR CODE BEGINS` and `# YOUR CODE ENDS` are stripped in the student version.

```python
import pandas as pd

# YOUR CODE BEGINS
sample_series = pd.Series([-20, -10, 10, 20])
# YOUR CODE ENDS

print(sample_series)
```

nbgrader syntax (`### BEGIN SOLUTION`, `### END SOLUTION`) is also supported.

```python
import pandas as pd

### BEGIN SOLUTION
sample_series = pd.Series([-20, -10, 10, 20])
### END SOLUTION

print(sample_series)
```

In the student-distributed notebook, the code cell will look like:

```python
import pandas as pd

# YOUR CODE BEGINS

# YOUR CODE ENDS

print(sample_series)
```

### Graded test cases

A graded test case requires the test case name and number of points.

`_test_case` variable should contain the name of the test case.
`_points` variable should contain the number of points (either in integer or float).

```python
_test_case = 'create-a-pandas-series'
_points = 2

pd.testing.assert_series_equal(sample_series, pd.Series([-20, -10, 10, 20]))
```

### Obfuscate test cases

You may wish to prevent the learners from seeing the test case code. To base64-encode the test cases, you can optionally add `_obfuscate = True`.
Note that this only offers a very basic obfuscation and a student can easily decode the encoded string to find the original code.
We may add an encryption method in the future.

**Instructor notebook**

```python
_test_case = 'create-a-pandas-series'
_points = 2
_obfuscate = True

pd.testing.assert_series_equal(sample_series, pd.Series([-20, -10, 10, 20]))
```

**Student notebook**

```
# DO NOT CHANGE THE CODE IN THIS CELL
_test_case = 'create-a-pandas-series'
_points = 2
_obfuscate = True

import base64 as _b64
_64 = _b64.b64decode('cGQudGVzdGluZy5hc3NlcnRfc2VyaWVzX2VxdWFsKHNhbXBsZV9zZXJpZXMsIHBkLlNlcmllcyhbLT\
IwLCAtMTAsIDEwLCAyMF0pKQ==')
eval(compile(_64, '<string>', 'exec'))
```

### Add hidden test cases

Hidden test cases only run while grading.

**Original test case**

```python
_test_case = 'create-a-pandas-series'
_points = 2

### BEGIN HIDDEN TESTS
pd.testing.assert_series_equal(sample_series, pd.Series([-20, -10, 10, 20]))
### END HIDDEN TESTS
```

**Converted** (before obfuscation)

```python
_test_case = 'create-a-pandas-series'
_points = 2

if 'is_lambdagrader_env' in globals():
    pd.testing.assert_series_equal(sample_series, pd.Series([-20, -10, 10, 20]))
```

## Roadmap

Our current goal is to build a working version using the [Serverless framework](https://www.serverless.com/). In the long term, we are looking to...

- Support filesystem (custom input files).
- Build a frontend with drag & drop box for graders.
- Enable encryption for hidden test cases.
- Detect any modifications to test cases using a hash.
- Add plagiarism detection.
