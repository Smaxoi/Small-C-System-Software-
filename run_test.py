"""Run main.py with test_input.txt as stdin, capture output to test_output2.txt."""
import sys
import io
import os

# Change working directory to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Read all test input
with open('test_input.txt', 'r', encoding='utf-8') as f:
    test_input_data = f.read()

# Simulate stdin and stdout
original_stdin = sys.stdin
original_stdout = sys.stdout

sys.stdin = io.StringIO(test_input_data)
captured = io.StringIO()
sys.stdout = captured

# Import and run the shell
# We need to import fresh each time
try:
    from main import Shell
    shell = Shell()
    try:
        shell.run()
    except SystemExit:
        pass
    except Exception as e:
        sys.stdout = original_stdout
        sys.stderr.write(f"Unexpected error: {e}\n")
        import traceback; traceback.print_exc()
finally:
    sys.stdin = original_stdin
    sys.stdout = original_stdout

output = captured.getvalue()
with open('test_output2.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print(f"Done. Output: {len(output.splitlines())} lines written to test_output2.txt")
