def system_prompt(
    exercise_name: str,
    course_name: str,
    course_description: str,
    problem_statement: str,
    start_date: str,
    end_date: str,
    current_date: str,
    current_answer: str,
) -> str:
    return """
        The student is working on a free-response exercise called '{exercise_name}' in the course '{course_name}'.
        The course has the following description:
        {course_description}

        The exercise has the following problem statement:
        {problem_statement}

        The exercise began on {start_date} and will end on {end_date}. The current date is {current_date}.

        This is what the student has written so far:
        {current_answer}

        You are a writing tutor. Provide feedback to the student on their response,
        giving specific tips to better answer the problem statement.
    """.format(
        exercise_name=exercise_name,
        course_name=course_name,
        course_description=course_description,
        problem_statement=problem_statement,
        start_date=start_date,
        end_date=end_date,
        current_date=current_date,
        current_answer=current_answer,
    )
