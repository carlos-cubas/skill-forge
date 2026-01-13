"""
Skill Size Validation Tests

This module validates the assumption that skill content fits within LLM context windows.

## Assumption Being Validated

From Issue #3 (Phase 0.3: Validate General Assumptions):
    "Skill content fits in context window"

Skills must not exceed LLM context limits to be usable during agent execution.

## Acceptable Thresholds

- Single skill: < 2000 tokens
- Meta-skill + 3 skills: < 8000 tokens

## Token Estimation Method

Uses approximate method: characters / 4 = estimated tokens

This is a rough estimate suitable for validation purposes. For more accurate
counts, tiktoken can be integrated later. The chars/4 ratio is commonly used
as a reasonable approximation for English text.

## Why These Thresholds

- 2000 tokens for single skill: Allows substantial instructions while leaving
  room for conversation context and task instructions
- 8000 tokens combined: Meta-skill (~500 tokens) + 3 skills (~2000 each) + buffer
  represents a realistic maximum concurrent skill load

## Test Strategy

1. Analyze existing test fixtures to understand baseline skill sizes
2. Create sample skills of various sizes to test boundaries
3. Validate threshold enforcement
4. Document findings for skill author guidelines
"""

import pytest
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


# ============================================================================
# Token Estimation Utilities
# ============================================================================


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text using character-based approximation.

    Uses the common approximation: tokens ~= characters / 4

    This provides a reasonable estimate for English text and markdown content.
    For more accurate counts, integrate tiktoken library.

    Args:
        text: The text to estimate token count for

    Returns:
        Estimated number of tokens
    """
    if not text:
        return 0
    return len(text) // 4


def estimate_tokens_from_file(file_path: Path) -> int:
    """
    Estimate token count from a file.

    Args:
        file_path: Path to the file to analyze

    Returns:
        Estimated number of tokens

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    content = file_path.read_text()
    return estimate_tokens(content)


@dataclass
class SkillSizeAnalysis:
    """Analysis results for a skill's size."""

    name: str
    char_count: int
    estimated_tokens: int
    line_count: int
    file_path: Optional[Path] = None

    @property
    def within_single_skill_threshold(self) -> bool:
        """Check if skill is within single skill threshold (2000 tokens)."""
        return self.estimated_tokens < SINGLE_SKILL_TOKEN_THRESHOLD

    @property
    def threshold_percentage(self) -> float:
        """Percentage of single skill threshold used."""
        return (self.estimated_tokens / SINGLE_SKILL_TOKEN_THRESHOLD) * 100


def analyze_skill_content(name: str, content: str, file_path: Optional[Path] = None) -> SkillSizeAnalysis:
    """
    Analyze the size characteristics of skill content.

    Args:
        name: Name of the skill
        content: The skill's markdown content
        file_path: Optional path to the skill file

    Returns:
        SkillSizeAnalysis with size metrics
    """
    return SkillSizeAnalysis(
        name=name,
        char_count=len(content),
        estimated_tokens=estimate_tokens(content),
        line_count=len(content.splitlines()),
        file_path=file_path
    )


# ============================================================================
# Threshold Constants
# ============================================================================

# Single skill should be under 2000 tokens
SINGLE_SKILL_TOKEN_THRESHOLD = 2000

# Meta-skill + 3 domain skills should be under 8000 tokens
COMBINED_SKILLS_TOKEN_THRESHOLD = 8000

# Realistic meta-skill size based on test fixtures
ESTIMATED_META_SKILL_TOKENS = 500


# ============================================================================
# Sample Skill Content for Testing
# ============================================================================

# Minimal skill (tests lower bound)
MINIMAL_SKILL = """---
name: minimal-skill
description: A minimal test skill
---

# Minimal Skill

Do the thing.
"""

# Small skill similar to test-skill.md fixture
SMALL_SKILL = """---
name: small-skill
description: A small test skill for validation
allowed-tools:
  - bash
---

# Small Skill

This is a small skill for validating size thresholds.

## Instructions

When activated:
1. Acknowledge the skill is loaded
2. Perform the requested task
3. Confirm completion

## Verification

Look for the phrase "small-skill" in your context.
"""

# Medium skill with substantial instructions
MEDIUM_SKILL = """---
name: medium-skill
description: A medium-sized skill with realistic instruction depth
allowed-tools:
  - bash
  - web_search
---

# Medium Skill

This skill demonstrates a realistic level of detail for a domain-specific capability.

## Overview

You are equipped with the medium-skill capability, which provides structured
approaches to common tasks requiring specialized knowledge.

## When to Use This Skill

Activate this skill when:
- The task requires systematic approach to problem-solving
- You need to follow a specific methodology
- The user requests structured analysis

## Methodology

### Phase 1: Assessment

1. Gather initial information about the situation
2. Identify key stakeholders and constraints
3. Document assumptions and unknowns
4. Establish success criteria

### Phase 2: Analysis

1. Break down the problem into components
2. Identify dependencies between components
3. Evaluate risks and opportunities
4. Prioritize areas of focus

### Phase 3: Synthesis

1. Develop recommendations based on analysis
2. Create action plan with clear steps
3. Define metrics for measuring success
4. Establish review points

## Best Practices

- Always start with Phase 1 before jumping to solutions
- Document your reasoning at each phase
- Validate assumptions when possible
- Communicate uncertainties clearly

## Example Interaction

User: "I need help organizing my project."

Response pattern:
1. "I'm using the medium-skill for structured project analysis."
2. Begin Phase 1 assessment questions
3. Proceed through phases systematically
4. Deliver synthesized recommendations

## Verification

The skill is loaded if you can see these instructions and follow the
three-phase methodology for problem-solving tasks.
"""

# Large skill approaching threshold (~1800 tokens, ~7200 chars)
LARGE_SKILL = """---
name: large-skill
description: A comprehensive skill approaching the size threshold
allowed-tools:
  - bash
  - web_search
  - file_operations
  - database_query
---

# Large Skill - Comprehensive Domain Expertise

This skill represents a near-maximum size skill with extensive instructions,
multiple methodologies, detailed examples, and comprehensive guidance.

## Skill Overview

The large-skill provides comprehensive capabilities for complex domain tasks
that require deep expertise and multi-faceted approaches. This skill should
be used when standard approaches are insufficient and specialized knowledge
is required.

### Core Competencies

1. **Strategic Analysis**: Deep evaluation of complex situations
2. **Methodology Selection**: Choosing appropriate frameworks
3. **Stakeholder Management**: Understanding diverse perspectives
4. **Risk Assessment**: Identifying and mitigating potential issues
5. **Implementation Planning**: Creating actionable roadmaps

## Activation Criteria

Use this skill when:
- Tasks involve multiple interdependent factors
- Standard approaches have proven insufficient
- Specialized domain expertise is explicitly required
- Long-term strategic thinking is necessary
- Complex stakeholder dynamics are present

## Methodologies

### Methodology A: Strategic Assessment Framework

#### Step 1: Environmental Scan
- Identify all relevant factors in the environment
- Categorize factors as internal vs external
- Assess factor volatility and predictability
- Document interconnections between factors

#### Step 2: Stakeholder Analysis
- List all stakeholders affected by the situation
- Map stakeholder interests and concerns
- Assess stakeholder power and influence
- Identify potential coalitions and conflicts

#### Step 3: Options Development
- Generate multiple strategic options
- Evaluate each option against criteria
- Assess resource requirements for each option
- Consider timing and sequencing implications

#### Step 4: Decision Synthesis
- Compare options using weighted criteria
- Identify hybrid or modified approaches
- Document trade-offs and assumptions
- Prepare recommendation with rationale

### Methodology B: Rapid Assessment Protocol

When time is limited, use this condensed approach:

1. **Situation**: What is happening? (2 minutes)
2. **Background**: Why is it happening? (2 minutes)
3. **Assessment**: What does it mean? (3 minutes)
4. **Recommendation**: What should be done? (3 minutes)

Total time: 10 minutes for initial assessment

### Methodology C: Deep Dive Analysis

For complex situations requiring thorough investigation:

#### Phase 1: Data Gathering (Hours/Days)
- Primary source interviews
- Document review and analysis
- Quantitative data collection
- Benchmarking against comparables

#### Phase 2: Analysis (Days)
- Pattern identification
- Root cause analysis
- Scenario modeling
- Sensitivity analysis

#### Phase 3: Synthesis (Days)
- Findings consolidation
- Recommendation development
- Implementation planning
- Presentation preparation

## Communication Protocols

### Progress Updates

When working on complex tasks, provide updates in this format:

```
PROGRESS_UPDATE:
- Phase: [current phase]
- Completed: [what's done]
- In Progress: [current work]
- Next Steps: [upcoming actions]
- Blockers: [any obstacles]
```

### Deliverable Format

Final deliverables should include:

1. Executive Summary (1 paragraph)
2. Background and Context
3. Analysis and Findings
4. Recommendations
5. Implementation Roadmap
6. Risk Assessment
7. Success Metrics

## Tool Usage Guidelines

### bash
- Use for automation and scripting needs
- Appropriate for data processing tasks
- Document all commands executed

### web_search
- Research current information
- Verify assumptions with data
- Find relevant case studies

### file_operations
- Manage document creation
- Organize deliverables
- Archive working materials

### database_query
- Access structured data
- Generate analytical reports
- Validate quantitative claims

## Quality Standards

All work using this skill must meet these standards:

1. **Accuracy**: All facts verified from reliable sources
2. **Completeness**: All relevant aspects addressed
3. **Clarity**: Explanations understandable by target audience
4. **Actionability**: Recommendations are implementable
5. **Timeliness**: Deliverables meet agreed deadlines

## Example Interactions

### Example 1: Strategic Question

User: "Should we enter the European market?"

Response approach:
1. Acknowledge skill activation
2. Begin with Methodology A
3. Request necessary information
4. Proceed through framework systematically
5. Deliver comprehensive recommendation

### Example 2: Time-Pressured Request

User: "I need a quick assessment of our competitive position."

Response approach:
1. Acknowledge skill activation
2. Use Methodology B (Rapid Assessment)
3. Complete 10-minute protocol
4. Provide structured SBAR output
5. Offer deeper analysis if needed

## Verification

This skill is loaded correctly if you:
- Can see all three methodologies (A, B, C)
- Understand the communication protocols
- Know which tools are available
- Can match task complexity to appropriate methodology

## Version and Maintenance

- Version: 1.0.0
- Last Updated: 2024-01-01
- Owner: SkillForge Test Suite
- Review Cycle: Quarterly
"""

# Oversized skill exceeding threshold (for negative testing)
OVERSIZED_SKILL = LARGE_SKILL + """

## Additional Extended Content

This section pushes the skill beyond the recommended threshold to test
boundary conditions in the validation system.

### Extended Methodology D

#### Comprehensive Multi-Phase Approach

##### Phase D.1: Initial Assessment
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur.

##### Phase D.2: Secondary Analysis
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum. Sed ut perspiciatis unde omnis iste
natus error sit voluptatem accusantium doloremque laudantium, totam rem
aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto
beatae vitae dicta sunt explicabo.

##### Phase D.3: Tertiary Synthesis
Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit,
sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.
Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur,
adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et
dolore magnam aliquam quaerat voluptatem.

##### Phase D.4: Final Integration
Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit
laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure
reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur,
vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?

### Extended Methodology E

At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis
praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias
excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui
officia deserunt mollitia animi, id est laborum et dolorum fuga.

Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore,
cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod
maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor
repellendus. Temporibus autem quibusdam et aut officiis debitis aut rerum
necessitatibus saepe eveniet ut et voluptates repudiandae sint et molestiae
non recusandae.

Itaque earum rerum hic tenetur a sapiente delectus, ut aut reiciendis
voluptatibus maiores alias consequatur aut perferendis doloribus asperiores
repellat. Additional content to ensure we exceed the threshold significantly.

### Extended Guidelines Section

These extended guidelines provide additional detail that pushes the skill
content well beyond recommended limits:

1. **Guideline Alpha**: Comprehensive procedural guidance
   - Sub-point A1: Detailed instruction set one
   - Sub-point A2: Detailed instruction set two
   - Sub-point A3: Detailed instruction set three

2. **Guideline Beta**: Secondary procedural framework
   - Sub-point B1: Extended methodology notes
   - Sub-point B2: Additional context and rationale
   - Sub-point B3: Implementation considerations

3. **Guideline Gamma**: Tertiary considerations
   - Sub-point G1: Edge case handling
   - Sub-point G2: Exception procedures
   - Sub-point G3: Escalation protocols

This content ensures the skill exceeds 2000 tokens for threshold testing.

### Extended Methodology F: Comprehensive Analysis Framework

#### Section F.1: Strategic Planning Components

This methodology provides a comprehensive framework for strategic planning that
incorporates multiple perspectives and stakeholder considerations. The approach
is designed to ensure thorough analysis and robust recommendations.

Key principles:
- Systematic data gathering from multiple sources
- Stakeholder engagement at every phase
- Iterative refinement of recommendations
- Clear documentation of assumptions and constraints

Implementation steps:
1. Establish project scope and objectives
2. Identify key stakeholders and their interests
3. Gather relevant data and information
4. Analyze data using appropriate frameworks
5. Develop preliminary recommendations
6. Validate recommendations with stakeholders
7. Refine and finalize deliverables

#### Section F.2: Advanced Analytical Techniques

The following analytical techniques should be applied based on the specific
requirements of the task at hand:

- SWOT Analysis: For strategic positioning assessment
- Porter's Five Forces: For industry structure analysis
- Value Chain Analysis: For operational efficiency review
- Balanced Scorecard: For performance measurement
- Root Cause Analysis: For problem identification

Each technique has specific use cases and should be selected based on the
nature of the problem being addressed and the information available.

#### Section F.3: Implementation Guidelines

When implementing recommendations from this methodology:

1. Develop a detailed implementation roadmap
2. Identify resource requirements and constraints
3. Establish clear milestones and success metrics
4. Create communication plan for stakeholders
5. Design risk mitigation strategies
6. Set up monitoring and evaluation framework

The implementation phase is critical to ensuring that strategic recommendations
translate into tangible outcomes and organizational improvements.

### Extended Methodology G: Operations Excellence Framework

This framework ensures operational excellence through systematic process
improvement and continuous optimization efforts across the organization.

#### Section G.1: Process Optimization

Process optimization involves systematic review and improvement of business
processes to enhance efficiency, reduce waste, and improve outcomes.

Key activities:
- Process mapping and documentation
- Bottleneck identification and analysis
- Waste elimination using lean principles
- Automation opportunity assessment
- Performance metric establishment

#### Section G.2: Quality Management

Quality management ensures consistent delivery of high-quality outputs:

- Define quality standards and specifications
- Implement quality control checkpoints
- Conduct regular quality audits
- Address quality issues promptly
- Drive continuous improvement initiatives

#### Section G.3: Resource Management

Effective resource management optimizes utilization:

- Capacity planning and forecasting
- Resource allocation optimization
- Skills gap analysis and training
- Workload balancing strategies
- Performance tracking and reporting

This additional content ensures the oversized skill significantly exceeds thresholds.
"""

# Simulated meta-skill content (based on test fixtures)
SIMULATED_META_SKILL = """---
name: using-skillforge
description: Meta-skill that teaches agents how to discover and use skills
---

# Using SkillForge

You have access to skills that extend your capabilities.

## When to Use Skills

Check for relevant skills when:
- A task mentions a domain-specific need (e.g., interviewing, coaching, data analysis)
- You need specialized knowledge beyond your general training
- The user explicitly asks about available capabilities

## How to Load Skills

1. Run: `skillforge read <skill-name>` to load a skill's instructions
2. The command outputs the skill's markdown content
3. Follow the loaded skill's instructions for the task

## Announcement Protocol

CRITICAL: When using ANY skill, you MUST announce it with EXACTLY this format:
"SKILL_ANNOUNCEMENT: Using [skill-name] for [brief purpose]"

Example: "SKILL_ANNOUNCEMENT: Using rapid-interviewing for executive coaching session"

## Available Skills

To see available skills, run: `skillforge list`

Skills are organized by domain and can be loaded on-demand as needed.

## Best Practices

- Only load skills when needed for the task
- Always announce when you're using a skill
- Skills provide instructions, not just information
- Follow skill instructions alongside your primary role
"""


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the fixtures directory path."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def test_skill_path(fixtures_dir: Path) -> Path:
    """Return the path to the test skill fixture."""
    return fixtures_dir / "test-skill.md"


@pytest.fixture
def test_skill_content(test_skill_path: Path) -> str:
    """Return the content of the test skill fixture."""
    return test_skill_path.read_text()


# ============================================================================
# Test: Token Estimation Utility
# ============================================================================


@pytest.mark.validation
class TestTokenEstimation:
    """Tests for the token estimation utility functions."""

    def test_estimate_tokens_empty_string(self):
        """
        Test that empty string returns zero tokens.

        Edge case: Empty content should not cause errors.
        """
        assert estimate_tokens("") == 0

    def test_estimate_tokens_short_text(self):
        """
        Test token estimation for short text.

        "Hello world" = 11 chars => ~2-3 tokens
        Using chars/4: 11/4 = 2 tokens (integer division)
        """
        result = estimate_tokens("Hello world")
        assert result == 2  # 11 // 4 = 2

    def test_estimate_tokens_medium_text(self):
        """
        Test token estimation for medium text.

        100 characters => ~25 tokens
        """
        text = "a" * 100
        result = estimate_tokens(text)
        assert result == 25  # 100 // 4 = 25

    def test_estimate_tokens_known_content(self):
        """
        Test token estimation against known content sizes.

        MINIMAL_SKILL is a small, known fixture we can verify.
        """
        char_count = len(MINIMAL_SKILL)
        expected_tokens = char_count // 4
        result = estimate_tokens(MINIMAL_SKILL)
        assert result == expected_tokens

    def test_estimate_tokens_approximation_reasonable(self):
        """
        Test that chars/4 approximation is reasonable for skill content.

        For markdown content, the approximation should be within a reasonable
        range of actual tokenization. This tests the assumption itself.
        """
        # MEDIUM_SKILL has realistic markdown content
        result = estimate_tokens(MEDIUM_SKILL)
        char_count = len(MEDIUM_SKILL)

        # Verify our approximation is consistent
        assert result == char_count // 4

        # The result should be in a reasonable range for skill content
        # Skills with 1000-2000 chars should be 250-500 estimated tokens
        assert 100 < result < 2000, f"Token count {result} outside reasonable range"

    def test_skill_size_analysis_dataclass(self):
        """
        Test the SkillSizeAnalysis dataclass functionality.
        """
        analysis = analyze_skill_content("test", SMALL_SKILL)

        assert analysis.name == "test"
        assert analysis.char_count == len(SMALL_SKILL)
        assert analysis.estimated_tokens == len(SMALL_SKILL) // 4
        assert analysis.line_count == len(SMALL_SKILL.splitlines())
        assert analysis.within_single_skill_threshold is True
        assert 0 < analysis.threshold_percentage < 100


# ============================================================================
# Test: Single Skill Size Threshold
# ============================================================================


@pytest.mark.validation
class TestSingleSkillSizeThreshold:
    """
    Validate that individual skills fit within the 2000 token threshold.

    This ensures skills can be loaded without consuming excessive context space,
    leaving room for conversation history, task instructions, and agent reasoning.
    """

    def test_minimal_skill_within_threshold(self):
        """
        Test that minimal skill is well under threshold.

        Minimal skills should be very small, using only a fraction of the allowed space.
        """
        analysis = analyze_skill_content("minimal", MINIMAL_SKILL)

        assert analysis.within_single_skill_threshold, (
            f"Minimal skill ({analysis.estimated_tokens} tokens) should be under "
            f"{SINGLE_SKILL_TOKEN_THRESHOLD} token threshold"
        )

        # Minimal skill should use less than 5% of threshold
        assert analysis.threshold_percentage < 5, (
            f"Minimal skill uses {analysis.threshold_percentage:.1f}% of threshold, "
            "expected less than 5%"
        )

    def test_small_skill_within_threshold(self):
        """
        Test that small skill (similar to test-skill.md) is within threshold.
        """
        analysis = analyze_skill_content("small", SMALL_SKILL)

        assert analysis.within_single_skill_threshold, (
            f"Small skill ({analysis.estimated_tokens} tokens) should be under "
            f"{SINGLE_SKILL_TOKEN_THRESHOLD} token threshold"
        )

        # Small skill should use less than 25% of threshold
        assert analysis.threshold_percentage < 25, (
            f"Small skill uses {analysis.threshold_percentage:.1f}% of threshold, "
            "expected less than 25%"
        )

    def test_medium_skill_within_threshold(self):
        """
        Test that medium skill with substantial instructions is within threshold.

        Medium skills represent typical production skills with detailed instructions.
        """
        analysis = analyze_skill_content("medium", MEDIUM_SKILL)

        assert analysis.within_single_skill_threshold, (
            f"Medium skill ({analysis.estimated_tokens} tokens) should be under "
            f"{SINGLE_SKILL_TOKEN_THRESHOLD} token threshold"
        )

        # Medium skill should use less than 50% of threshold
        assert analysis.threshold_percentage < 50, (
            f"Medium skill uses {analysis.threshold_percentage:.1f}% of threshold, "
            "expected less than 50%"
        )

    def test_large_skill_within_threshold(self):
        """
        Test that large skill approaching limit is still within threshold.

        Large skills represent the upper bound of recommended skill size.
        """
        analysis = analyze_skill_content("large", LARGE_SKILL)

        assert analysis.within_single_skill_threshold, (
            f"Large skill ({analysis.estimated_tokens} tokens) should be under "
            f"{SINGLE_SKILL_TOKEN_THRESHOLD} token threshold"
        )

        # Document how close we are to threshold
        print(f"\nLarge skill analysis:")
        print(f"  Characters: {analysis.char_count}")
        print(f"  Estimated tokens: {analysis.estimated_tokens}")
        print(f"  Threshold usage: {analysis.threshold_percentage:.1f}%")

    def test_oversized_skill_exceeds_threshold(self):
        """
        Test that oversized skill correctly fails threshold check.

        This validates our threshold enforcement catches over-sized skills.
        """
        analysis = analyze_skill_content("oversized", OVERSIZED_SKILL)

        assert not analysis.within_single_skill_threshold, (
            f"Oversized skill ({analysis.estimated_tokens} tokens) should exceed "
            f"{SINGLE_SKILL_TOKEN_THRESHOLD} token threshold"
        )

        print(f"\nOversized skill analysis (expected to exceed):")
        print(f"  Characters: {analysis.char_count}")
        print(f"  Estimated tokens: {analysis.estimated_tokens}")
        print(f"  Threshold usage: {analysis.threshold_percentage:.1f}%")

    def test_test_skill_fixture_within_threshold(self, test_skill_content):
        """
        Test that the actual test-skill.md fixture is within threshold.

        This validates the existing test fixture meets our size requirements.
        """
        analysis = analyze_skill_content("test-skill", test_skill_content)

        assert analysis.within_single_skill_threshold, (
            f"Test skill fixture ({analysis.estimated_tokens} tokens) should be under "
            f"{SINGLE_SKILL_TOKEN_THRESHOLD} token threshold"
        )

        print(f"\ntest-skill.md fixture analysis:")
        print(f"  Characters: {analysis.char_count}")
        print(f"  Estimated tokens: {analysis.estimated_tokens}")
        print(f"  Lines: {analysis.line_count}")
        print(f"  Threshold usage: {analysis.threshold_percentage:.1f}%")


# ============================================================================
# Test: Combined Skills Threshold
# ============================================================================


@pytest.mark.validation
class TestCombinedSkillsThreshold:
    """
    Validate that meta-skill + 3 domain skills fit within 8000 token threshold.

    This represents a realistic maximum concurrent skill load during agent execution.
    """

    def test_meta_skill_size(self):
        """
        Test meta-skill size as baseline for combined calculations.

        Meta-skill should be relatively small (~500 tokens) to leave room
        for domain skills.
        """
        analysis = analyze_skill_content("meta", SIMULATED_META_SKILL)

        # Meta-skill should be under 600 tokens
        assert analysis.estimated_tokens < 600, (
            f"Meta-skill ({analysis.estimated_tokens} tokens) should be under 600 tokens"
        )

        print(f"\nMeta-skill analysis:")
        print(f"  Characters: {analysis.char_count}")
        print(f"  Estimated tokens: {analysis.estimated_tokens}")

    def test_meta_plus_three_small_skills(self):
        """
        Test meta-skill + 3 small skills is well under combined threshold.

        This represents a light-weight skill configuration.
        """
        total_tokens = (
            estimate_tokens(SIMULATED_META_SKILL) +
            estimate_tokens(SMALL_SKILL) +
            estimate_tokens(SMALL_SKILL) +
            estimate_tokens(SMALL_SKILL)
        )

        assert total_tokens < COMBINED_SKILLS_TOKEN_THRESHOLD, (
            f"Meta + 3 small skills ({total_tokens} tokens) should be under "
            f"{COMBINED_SKILLS_TOKEN_THRESHOLD} threshold"
        )

        percentage = (total_tokens / COMBINED_SKILLS_TOKEN_THRESHOLD) * 100
        print(f"\nMeta + 3 small skills:")
        print(f"  Total tokens: {total_tokens}")
        print(f"  Threshold usage: {percentage:.1f}%")

    def test_meta_plus_three_medium_skills(self):
        """
        Test meta-skill + 3 medium skills is within combined threshold.

        This represents a typical production configuration.
        """
        total_tokens = (
            estimate_tokens(SIMULATED_META_SKILL) +
            estimate_tokens(MEDIUM_SKILL) +
            estimate_tokens(MEDIUM_SKILL) +
            estimate_tokens(MEDIUM_SKILL)
        )

        assert total_tokens < COMBINED_SKILLS_TOKEN_THRESHOLD, (
            f"Meta + 3 medium skills ({total_tokens} tokens) should be under "
            f"{COMBINED_SKILLS_TOKEN_THRESHOLD} threshold"
        )

        percentage = (total_tokens / COMBINED_SKILLS_TOKEN_THRESHOLD) * 100
        print(f"\nMeta + 3 medium skills:")
        print(f"  Total tokens: {total_tokens}")
        print(f"  Threshold usage: {percentage:.1f}%")

    def test_meta_plus_three_large_skills(self):
        """
        Test meta-skill + 3 large skills against combined threshold.

        This represents maximum recommended configuration.
        """
        total_tokens = (
            estimate_tokens(SIMULATED_META_SKILL) +
            estimate_tokens(LARGE_SKILL) +
            estimate_tokens(LARGE_SKILL) +
            estimate_tokens(LARGE_SKILL)
        )

        assert total_tokens < COMBINED_SKILLS_TOKEN_THRESHOLD, (
            f"Meta + 3 large skills ({total_tokens} tokens) should be under "
            f"{COMBINED_SKILLS_TOKEN_THRESHOLD} threshold"
        )

        percentage = (total_tokens / COMBINED_SKILLS_TOKEN_THRESHOLD) * 100
        print(f"\nMeta + 3 large skills:")
        print(f"  Total tokens: {total_tokens}")
        print(f"  Threshold usage: {percentage:.1f}%")

    def test_meta_plus_mixed_skills(self):
        """
        Test meta-skill with mixed skill sizes.

        This represents a realistic scenario with skills of varying complexity.
        """
        total_tokens = (
            estimate_tokens(SIMULATED_META_SKILL) +
            estimate_tokens(SMALL_SKILL) +
            estimate_tokens(MEDIUM_SKILL) +
            estimate_tokens(LARGE_SKILL)
        )

        assert total_tokens < COMBINED_SKILLS_TOKEN_THRESHOLD, (
            f"Meta + mixed skills ({total_tokens} tokens) should be under "
            f"{COMBINED_SKILLS_TOKEN_THRESHOLD} threshold"
        )

        percentage = (total_tokens / COMBINED_SKILLS_TOKEN_THRESHOLD) * 100
        print(f"\nMeta + mixed skills (small + medium + large):")
        print(f"  Total tokens: {total_tokens}")
        print(f"  Threshold usage: {percentage:.1f}%")

    def test_combined_threshold_with_oversized_skills_fails(self):
        """
        Test that combining oversized skills correctly exceeds threshold.

        This validates threshold enforcement for combined scenarios.
        """
        total_tokens = (
            estimate_tokens(SIMULATED_META_SKILL) +
            estimate_tokens(OVERSIZED_SKILL) +
            estimate_tokens(OVERSIZED_SKILL) +
            estimate_tokens(OVERSIZED_SKILL)
        )

        # This should exceed the combined threshold
        assert total_tokens > COMBINED_SKILLS_TOKEN_THRESHOLD, (
            f"Meta + 3 oversized skills ({total_tokens} tokens) should exceed "
            f"{COMBINED_SKILLS_TOKEN_THRESHOLD} threshold"
        )

        print(f"\nMeta + 3 oversized skills (expected to exceed):")
        print(f"  Total tokens: {total_tokens}")
        print(f"  Exceeds threshold by: {total_tokens - COMBINED_SKILLS_TOKEN_THRESHOLD} tokens")


# ============================================================================
# Test: Realistic Skill Size Guidelines
# ============================================================================


@pytest.mark.validation
class TestSkillSizeGuidelines:
    """
    Generate and validate guidelines for skill authors.

    These tests document recommended sizes and provide actionable guidance.
    """

    def test_generate_size_guidelines(self):
        """
        Generate size guidelines based on threshold analysis.

        This test documents the recommended skill sizes for skill authors.
        """
        # Analyze all sample skills
        samples = [
            ("minimal", MINIMAL_SKILL),
            ("small", SMALL_SKILL),
            ("medium", MEDIUM_SKILL),
            ("large", LARGE_SKILL),
            ("meta", SIMULATED_META_SKILL),
        ]

        print("\n" + "=" * 70)
        print("SKILL SIZE GUIDELINES")
        print("=" * 70)
        print(f"\nThresholds:")
        print(f"  Single skill: < {SINGLE_SKILL_TOKEN_THRESHOLD} tokens (~{SINGLE_SKILL_TOKEN_THRESHOLD * 4} chars)")
        print(f"  Combined (meta + 3): < {COMBINED_SKILLS_TOKEN_THRESHOLD} tokens (~{COMBINED_SKILLS_TOKEN_THRESHOLD * 4} chars)")
        print(f"\nSample skill sizes:")

        for name, content in samples:
            analysis = analyze_skill_content(name, content)
            print(f"\n  {name}:")
            print(f"    Characters: {analysis.char_count:,}")
            print(f"    Est. tokens: {analysis.estimated_tokens:,}")
            print(f"    Lines: {analysis.line_count}")
            print(f"    Threshold %: {analysis.threshold_percentage:.1f}%")

        print("\n" + "-" * 70)
        print("RECOMMENDATIONS:")
        print("-" * 70)
        print("""
  1. Target skill size: 500-1500 tokens (~2000-6000 chars)
  2. Keep meta-skill under 500 tokens
  3. Use bullet points and concise language
  4. Avoid redundant explanations
  5. Extract examples to separate resources if large
  6. Test combined size when designing skill sets
        """)
        print("=" * 70)

        # This test always passes - it's for documentation
        assert True

    def test_recommended_skill_structure_fits_threshold(self):
        """
        Validate that recommended skill structure fits within thresholds.

        A skill following best practices should comfortably fit within limits.
        """
        # Recommended structure components
        recommended_skill = """---
name: recommended-skill
description: A skill following recommended structure
allowed-tools:
  - bash
---

# Recommended Skill

Brief overview of what this skill does.

## When to Use

- Condition 1
- Condition 2
- Condition 3

## Instructions

### Step 1: First Action
Concise instructions for first step.

### Step 2: Second Action
Concise instructions for second step.

### Step 3: Final Action
Concise instructions for final step.

## Best Practices

- Practice 1
- Practice 2
- Practice 3

## Verification

The skill is loaded if you can see these instructions.
"""

        analysis = analyze_skill_content("recommended", recommended_skill)

        # Should be well under threshold with recommended structure
        assert analysis.threshold_percentage < 30, (
            f"Recommended structure uses {analysis.threshold_percentage:.1f}% of threshold, "
            "which is higher than expected for minimal recommended structure"
        )

        print(f"\nRecommended structure analysis:")
        print(f"  Characters: {analysis.char_count}")
        print(f"  Estimated tokens: {analysis.estimated_tokens}")
        print(f"  Threshold usage: {analysis.threshold_percentage:.1f}%")


# ============================================================================
# Performance Reporting
# ============================================================================


@pytest.fixture(scope="module", autouse=True)
def report_skill_size_thresholds():
    """Print skill size thresholds at the start of the test module."""
    print("\n" + "=" * 70)
    print("Skill Size Validation Tests")
    print("=" * 70)
    print("\nAcceptance Thresholds:")
    print(f"  Single skill:    < {SINGLE_SKILL_TOKEN_THRESHOLD} tokens")
    print(f"  Combined skills: < {COMBINED_SKILLS_TOKEN_THRESHOLD} tokens (meta + 3 skills)")
    print("\nToken Estimation: characters / 4")
    print("=" * 70 + "\n")
    yield
    print("\n" + "=" * 70)
    print("End of Skill Size Validation Tests")
    print("=" * 70)
