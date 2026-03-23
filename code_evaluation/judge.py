import subprocess
import tempfile
import os
import time
import psutil
from .models import TestCase, SubmissionTestCase


def normalize_output(text):
    """Normalize output for safe comparison"""
    return "\n".join(line.strip() for line in text.strip().splitlines())


def clean_input(text):
    """Normalize testcase input"""
    lines = text.splitlines()
    lines = [line.rstrip() for line in lines if line.strip() != ""]
    return "\n".join(lines) + "\n"


def judge_submission(submission):

    print("===== JUDGE STARTED =====")
    print("Submission ID:", submission.id)

    problem = submission.problem
    testcases = TestCase.objects.filter(problem=problem)

    max_execution_time = 0
    max_memory_used = 0

    process = psutil.Process(os.getpid())  # NEW

    with tempfile.TemporaryDirectory() as tmpdir:

        language = submission.language.lower()
        print("Language:", language)
        print("Temp Directory:", tmpdir)

        # -----------------------
        # Create source file
        # -----------------------

        if language == "python":
            source_file = os.path.join(tmpdir, "solution.py")

        elif language == "c":
            source_file = os.path.join(tmpdir, "solution.c")

        elif language == "cpp":
            source_file = os.path.join(tmpdir, "solution.cpp")

        elif language == "java":
            source_file = os.path.join(tmpdir, "Main.java")

        else:
            print("Unsupported language")
            submission.status = "RE"
            submission.save()
            return

        print("Source file:", source_file)

        with open(source_file, "w", encoding="utf-8") as f:
            f.write(submission.code)

        print("Code written successfully")

        executable = None

        # -----------------------
        # Compile step
        # -----------------------

        try:

            if language == "python":
                executable = ["python", source_file]

            elif language == "c":

                executable_file = os.path.join(tmpdir, "solution")

                print("Compiling C code...")

                compile = subprocess.run(
                    ["gcc", source_file, "-O2", "-o", executable_file],
                    capture_output=True,
                    text=True
                )

                if compile.returncode != 0:
                    print("=== COMPILE ERROR ===")
                    print(compile.stderr)

                    submission.status = "CE"
                    submission.save()
                    return

                print("C compilation successful")
                executable = [executable_file]

            elif language == "cpp":

                executable_file = os.path.join(tmpdir, "solution")

                print("Compiling C++ code...")

                compile = subprocess.run(
                    ["g++", source_file, "-O2", "-std=c++17", "-o", executable_file],
                    capture_output=True,
                    text=True
                )

                if compile.returncode != 0:
                    print("=== COMPILE ERROR ===")
                    print(compile.stderr)

                    submission.status = "CE"
                    submission.save()
                    return

                print("C++ compilation successful")
                executable = [executable_file]

            elif language == "java":

                print("Compiling Java code...")

                compile = subprocess.run(
                    ["javac", source_file],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True
                )

                if compile.returncode != 0:
                    print("=== COMPILE ERROR ===")
                    print(compile.stderr)

                    submission.status = "CE"
                    submission.save()
                    return

                print("Java compilation successful")

                executable = ["java", "-cp", tmpdir, "Main"]

        except Exception as e:

            print("=== COMPILATION FAILURE ===")
            print(e)

            submission.status = "CE"
            submission.save()
            return

        # -----------------------
        # Run testcases
        # -----------------------

        print("Total Testcases:", testcases.count())

        for i, tc in enumerate(testcases, start=1):

            print("\n------ Running Testcase", i, "------")

            try:

                testcase_input = clean_input(tc.input_data or "")

                print("Input:")
                print(repr(testcase_input))

                start_time = time.perf_counter()

                # MEMORY BEFORE
                mem_before = process.memory_info().rss // 1024

                result = subprocess.run(
                    executable,
                    input=testcase_input,
                    text=True,
                    capture_output=True,
                    timeout=float(problem.time_limit)
                )

                # MEMORY AFTER
                mem_after = process.memory_info().rss // 1024

                end_time = time.perf_counter()

                execution_time = end_time - start_time
                max_execution_time = max(max_execution_time, execution_time)

                memory_used = max(0, mem_after - mem_before)
                max_memory_used = max(max_memory_used, memory_used)

                print("Execution Time:", execution_time)
                print("Memory Used:", memory_used, "KB")

                if result.returncode != 0:

                    print("=== RUNTIME ERROR ===")
                    print(result.stderr)

                    SubmissionTestCase.objects.create(
                        submission=submission,
                        testcase=tc,
                        user_output=result.stderr,
                        expected_output=tc.output_data,
                        status="RE",
                        execution_time=execution_time
                    )

                    submission.status = "RE"
                    submission.execution_time = max_execution_time
                    submission.memory_used = max_memory_used
                    submission.save()
                    return

                output = normalize_output(result.stdout)
                expected = normalize_output(tc.output_data or "")

                print("User Output:", repr(output))
                print("Expected Output:", repr(expected))

                if output != expected:

                    print("=== WRONG ANSWER ===")

                    SubmissionTestCase.objects.create(
                        submission=submission,
                        testcase=tc,
                        user_output=output,
                        expected_output=expected,
                        status="WA",
                        execution_time=execution_time
                    )

                    submission.status = "WA"
                    submission.execution_time = max_execution_time
                    submission.memory_used = max_memory_used
                    submission.save()
                    return
                
                SubmissionTestCase.objects.create(
                    submission=submission,
                    testcase=tc,
                    user_output=output,
                    expected_output=expected,
                    status="AC",
                    execution_time=execution_time
                )

                print("Testcase", i, "PASSED")

            except subprocess.TimeoutExpired:

                print("=== TIME LIMIT EXCEEDED ===")

                SubmissionTestCase.objects.create(
                    submission=submission,
                    testcase=tc,
                    user_output="",
                    expected_output=tc.output_data,
                    status="TLE",
                    execution_time=max_execution_time
                )

                submission.status = "TLE"
                submission.execution_time = max_execution_time
                submission.memory_used = max_memory_used
                submission.save()
                return

            except Exception as e:

                print("=== JUDGE ERROR ===")
                print(e)

                SubmissionTestCase.objects.create(
                    submission=submission,
                    testcase=tc,
                    user_output=str(e),
                    expected_output=tc.output_data,
                    status="RE",
                    execution_time=max_execution_time
                )

                submission.status = "RE"
                submission.execution_time = max_execution_time
                submission.memory_used = max_memory_used
                submission.save()
                return

    print("\n===== ALL TESTCASES PASSED =====")
    print("Max Execution Time:", max_execution_time)
    print("Max Memory Used:", max_memory_used, "KB")

    submission.status = "AC"
    submission.execution_time = max_execution_time
    submission.memory_used = max_memory_used
    submission.save()