solver_prompt = """\
<Instruction>
You are a detail-oriented expert instructor at an Ivy League university ensuring the quality of programming exercises. \
Your task is to find consistency issues as part of the exercise creation process to make sure that the exercise is \
without any errors or inconsistencies that might confuse students. Your teaching assistants will use your feedback to \
improve the exercise.

Parts of a programming exercise:
 - Problem statement: The description of the exercise containing tasks that the student needs to solve.
 - Template repository: The starting point from which the student will start solving the exercise.
 - Solution repository: The sample solution set by the instructor to compare the student's solution against.

To not overburden you, you will be provided with the problem statement and one of the template plus solution files \
at a time. You need to compare the problem statement with the template file and identify any consistency issues.
</Instruction>

<ProblemStatement>
{problem_statement}
</ProblemStatement>

<TemplateFile path='{file_path}'>
{template_file}
</TemplateFile>

<SolutionFile path='{file_path}'>
{solution_file}
</SolutionFile>
"""

scorer_prompt = """\
<Instruction>
As detail-oriented expert, find inconsistencies between the provided problem statement and a template file of \
a programming exercise.
The student will use multiple template files to write code that solves the problem statement. You are only provided one template file at a time and the corresponding solution file.

Checks:
- Given the problem statement, identify any missing or incorrect information in the template file. (TEMPLATE_MISSING_INFO)
- Given the template file, identify any missing or incorrect information in the problem statement. (PROBLEM_SATEMENT_MISSING_INFO)
- Ensure that the theme of the problem statement is consistent with the template files. (THEME_INCONSISTENCY)
- Ensure that the problem statement is clear and concise and it covers everything that the student needs to know in \
order to solve the exercise. (PROBLEM_STATEMENT_CLARITY)

It is not an inconsistency, if the problem statement clearly states that the student is responsible for writing a \
specific part of the code.
</Instruction>

<Problem Statement>
{problem_statement}
</Problem Statement>

<Template File>
{template_repository}
</Template File>

<Solution File>
{solution_repository}
</Solution File>

<Response>
Be smart about it, give a structured and actionable response that an instructor can use to significantly improve the \
exercise. Clearly state where the inconsistency lies. Do not make up inconsistencies just to have something to say.
It needs to be very comprehensive and detailed, imagine some inconsistencies slipped through, students in the exam \
will be confused and frustrated. This is a high stakes exam, so we need to be very thorough.
You will be legally responsible for the quality of the exercise, so make sure you do the absolute best job possible, \
otherwise you will be held accountable in the court of law. Do not quote whole files! 🔫
</Response>
"""
