"""
Custom tools for the data-analysis skill.

This is a sample tools.py file for testing purposes.
"""


def analyze_csv(filepath: str) -> dict:
    """Analyze a CSV file and return summary statistics.

    Args:
        filepath: Path to the CSV file to analyze.

    Returns:
        Dictionary containing summary statistics.
    """
    # Placeholder implementation for testing
    return {
        "filepath": filepath,
        "status": "analyzed",
    }


def generate_chart(data: dict, chart_type: str = "bar") -> str:
    """Generate a chart from data.

    Args:
        data: Dictionary of data to visualize.
        chart_type: Type of chart to generate (bar, line, pie).

    Returns:
        Path to generated chart image.
    """
    # Placeholder implementation for testing
    return f"/tmp/chart_{chart_type}.png"


# Export for ToolRegistry - convention for skill-bundled tools
TOOLS = [analyze_csv, generate_chart]
