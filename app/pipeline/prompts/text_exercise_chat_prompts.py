def fmt_guard_prompt(
    exercise_name: str,
    course_name: str,
    course_description: str,
    problem_statement: str,
    user_input: str,
) -> str:
    return """
    You check whether a user's input is on-topic and appropriate discourse in the context of a writing exercise.
    The exercise is called '{exercise_name}' in the course '{course_name}'.
    The course has the following description:
    {course_description}
    The exercise has the following problem statement:
    {problem_statement}
    The user says:
    {user_input}
    If this is on-topic and appropriate discussion, respond with "Yes".
    If the user's input is clearly about something else or inappropriate, respond with "No".
    """.format(
        exercise_name=exercise_name,
        course_name=course_name,
        course_description=course_description,
        problem_statement=problem_statement,
        user_input=user_input,
    )


def fmt_system_prompt(
    exercise_name: str,
    course_name: str,
    course_description: str,
    problem_statement: str,
    start_date: str,
    end_date: str,
    current_date: str,
    current_submission: str,
) -> str:
    return """
        The student is working on a free-response exercise called '{exercise_name}' in the course '{course_name}'.
        The course has the following description:
        {course_description}

        The exercise has the following problem statement:
        {problem_statement}

        The exercise began on {start_date} and will end on {end_date}. The current date is {current_date}.

        This is what the student has written so far:
        {current_submission}

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
        current_submission=current_submission,
    )


def fmt_rejection_prompt(
    exercise_name: str,
    course_name: str,
    course_description: str,
    problem_statement: str,
    user_input: str,
) -> str:
    return """
    The user is working on a free-response exercise called '{exercise_name}' in the course '{course_name}'.
    The course has the following description:
    {course_description}
    The exercise has the following problem statement:
    {problem_statement}
    The user has asked the following question:
    {user_input}
    The question is off-topic or inappropriate.
    Briefly explain that you cannot help with their query, and prompt them to focus on the exercise.
    """.format(
        exercise_name=exercise_name,
        course_name=course_name,
        course_description=course_description,
        problem_statement=problem_statement,
        user_input=user_input,
    )
