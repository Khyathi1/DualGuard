
import re


def extract_accuracy(text):

    matches = re.findall(
        r"\b\d+(?:\.\d+)?%",
        text
    )

    return matches


def verify_reward(agent_output, source_document):

    source_values = extract_accuracy(source_document)

    output_values = extract_accuracy(agent_output)

    if not source_values:
        return {
            "verified": False,
            "reward": 0.0,
            "reason": "No source accuracy found."
        }

    if not output_values:
        return {
            "verified": False,
            "reward": 0.0,
            "reason": "No accuracy found in agent output."
        }

    correct = any(
        value in source_values
        for value in output_values
    )

    return {
        "verified": correct,
        "reward": 1.0 if correct else 0.0,
        "reason": (
            "Output supported by source."
            if correct
            else "Output does not match source evidence."
        )
    }


if __name__ == "__main__":

    source = """
    The model achieved an accuracy of 87.4%.
    """

    outputs = [
        "Model accuracy: 87.4%",
        "Model accuracy: 99.9%"
    ]

    for output in outputs:

        print("\nOutput:", output)

        print(
            verify_reward(output, source)
        )
