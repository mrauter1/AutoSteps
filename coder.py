import inspect
import textwrap
from llm import get_llm  # Use factory to obtain an LLM instance
from log import Logger

logger = Logger.get_logger()

def generate_code_from_llm(func, step_name, description, max_retries=3):
    """
    Uses an LLM to generate code enclosed in a triple-backtick code block.
    If there's a syntax error, it feeds the error back to the LLM and retries.
    """
    llm = get_llm(provider="openai", api_key="", model="gpt-4o")
    
    parent_module = inspect.getmodule(func)
    parent_source =  inspect.getsource(parent_module)
    step_definition = inspect.getsource(func)
    step_definition = escape_decorator_line(step_definition)
    docstring = description or (inspect.getdoc(func) or "")
    syntax_error_msg = ""

    messages = []
    for attempt in range(max_retries):
        logger.info(f"Generating code from LLM for step: {step_name}, attempt {attempt+1}/{max_retries}")
        if attempt == 0:
            messages = [
                {
                    "role": "system",
                    "content": (
                        """
                        You are a perfect Python coding assistant. 
                        Given a parent workflow and the function's description, and signature 
                        output a Python function that fulfills the requirements. 
                        Wrap the code in triple backticks (```).            
                        """
                    )
                },
                {
                    "role": "user",
                    "content": build_prompt(parent_source, step_definition, step_name, docstring)
                }
            ]
        else:
            messages.append({
                "role": "user",
                "content": (
                    "There was a syntax error in the code you provided:\n"
                    f"{syntax_error_msg}\n"
                    "Please fix and provide new code wrapped in triple backticks."
                )
            })

        response_messages = llm.chat(messages)
        generated_code = extract_code_block(response_messages)

        if not generated_code:
            syntax_error_msg = "No code block found."
            logger.warning(f"Syntax error on attempt {attempt+1}: {syntax_error_msg}")
            continue

        try:
            compile(generated_code, "<string>", "exec")
            return generated_code
        except SyntaxError as e:
            syntax_error_msg = str(e)
            logger.warning(f"Syntax error on attempt {attempt+1}: {syntax_error_msg}")

    raise RuntimeError(
        f"Failed to generate valid code for step '{step_name}' after {max_retries} attempts."
    )

def escape_decorator_line(source_code):
    """
    Remove lines starting with '@step(' from the source code.
    """
    lines = source_code.splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith('@step(')]
    return "\n".join(filtered_lines)

def build_prompt(parent_module, step_definition, step_name, docstring):
    return textwrap.dedent(f"""
    The function to be implemented is:
    <function_definition>
    {step_definition}
    </function_definition>

    This function is part of the following parent module:
    <parent_module>
    {parent_module}
    </parent_module>

    Requirements:
    1) The function must be valid Python 3 code.
    2) Wrap the entire function in triple backticks (```).
    3) Make sure the final code is logically and syntactically correct.
    4) Only output the full working function code. Implement it fully and only output the function code.
    
    You must fully implement the function '{step_name}' that satisfies the following description:
    <docstring>
    {docstring}
    </docstring>
    """)

def extract_code_block(response_messages):
    """
    Finds the first triple backtick code block in LLM response.
    Returns the code as a string or None if not found.
    """
    full_text = ""
    for msg in response_messages:
        full_text += msg["content"] + "\n"

    start_idx = full_text.find("```")
    if start_idx == -1:
        return None
    end_idx = full_text.find("```", start_idx + 3)
    if end_idx == -1:
        return None

    code_block = full_text[start_idx + 3 : end_idx].strip()
    if "\n" in code_block and code_block.splitlines()[0].strip().startswith("python"):
        code_block = "\n".join(code_block.splitlines()[1:])
    return code_block.strip()
