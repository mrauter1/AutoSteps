# File: example_non_linear_workflow.py
from auto_steps import step
from router import route_next_step

@step(auto_implement=True, description="Implementation for code-based step.")
def code_step():
    pass

@step(auto_implement=True, description="Implementation for LLM-prompt step.")
def llm_prompt_step():
    pass

@step(auto_implement=True, description="Implementation for sub-workflow step.")
def workflow_step():
    pass

def classify_and_execute_step():
    chosen_step = route_next_step(
        parent_workflow=classify_and_execute_step,
        router_name="SimpleStepClassifier",
        router_description="Classify the step as code, llm_prompt or workflow.",
        options={
            "code": "Run code implementation.",
            "llm_prompt": "Run an LLM-prompt implementation.",
            "workflow": "Run a sub-workflow."
        }
    )

    if chosen_step == "code":
        return code_step()
    elif chosen_step == "llm_prompt":
        return llm_prompt_step()
    elif chosen_step == "workflow":
        return workflow_step()

if __name__ == "__main__":
    result = classify_and_execute_step()
    print("Result:", result)
