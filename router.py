# File: router.py
import inspect
from llm import get_llm
from log import Logger

logger = Logger.get_logger()

def router(router_description, options, provider="openai", model="gpt-4o"):
    """
    Calls an LLM to choose the next step from the given options.
    Returns the chosen option's key or None if not found.
    """
    parent_workflow = None
    stack = inspect.stack()
    # The calling function is usually at stack level 2 or higher
    for frame in stack:
        # Skip built-in functions and decorators; get only user-defined function names
        if frame.function not in ('<module>', '<lambda>', 'wrapper', 'decorator'):
            parent_function = frame.function
            break

    return router_step(parent_workflow, router_description, options, provider=provider, model=model)

def router_step(parent_workflow, router_description, options, provider="openai", model="gpt-4o"):
    """
    Calls an LLM to choose the next step from the given options.
    Returns the chosen option's key or None if not found.
    """
    if callable(parent_workflow):
        parent_workflow_code = inspect.getsource(parent_workflow)
    else:
        parent_workflow_code = str(parent_workflow)

    logger.info(f"Routing next step: {router_description}")
    llm = get_llm(provider=provider, model=model)

    system_prompt = """You are a perfect workflow router. 
            Given the workflow and context, your task is to select the most appropriate next step / action. """
    prompt = build_router_prompt(router_description, parent_workflow_code, options)

    response = llm.chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ])

    logger.info(f"Router raw response: {response}")
    chosen_step = parse_router_response(response, options)
    logger.info(f"Chosen step: {chosen_step}")
    return chosen_step

def build_router_prompt(router_description, parent_workflow_code, options):
    opts_list = "\n".join([f"- {k}: {v}" for k, v in options.items()])
    return f"""
Router Description: {router_description}

Parent Workflow Code:
{parent_workflow_code}

Possible next steps:
{opts_list}

Return only the single best step key from the above options.
"""

def parse_router_response(response_messages, options):
    combined_text = "".join(msg["content"] for msg in response_messages).strip()
    for key in options.keys():
        if key in combined_text:
            return key
    return None
