# Skill Size Validation Analysis

**Date:** 2025-01-13
**Issue:** #3 (Phase 0.3: Validate General Assumptions)
**Assumption:** Skill content fits in context window

## Summary

**VALIDATED**: Skills can be designed to fit comfortably within LLM context windows using the established thresholds.

## Thresholds

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Single skill | < 2000 tokens (~8000 chars) | Leaves room for conversation context and task instructions |
| Combined (meta + 3 skills) | < 8000 tokens (~32000 chars) | Realistic maximum concurrent skill load |

## Token Estimation Method

Uses approximate method: `characters / 4 = estimated tokens`

This is a rough estimate suitable for validation purposes. The chars/4 ratio is commonly used as a reasonable approximation for English text and markdown content. For production use, tiktoken can be integrated for more accurate counts.

## Test Fixture Analysis

### Existing test-skill.md Fixture

```
Characters: 605
Estimated tokens: 151
Lines: 27
Threshold usage: 7.6%
```

The existing test fixture is well under the threshold, representing a minimal skill suitable for validation testing.

## Sample Skill Size Benchmarks

| Skill Type | Characters | Est. Tokens | Lines | Threshold % |
|------------|------------|-------------|-------|-------------|
| Minimal | 94 | 23 | 8 | 1.1% |
| Small | 357 | 89 | 21 | 4.5% |
| Medium | 1,736 | 434 | 68 | 21.7% |
| Large | 5,329 | 1,332 | 197 | 66.6% |
| Meta-skill | 1,258 | 314 | 41 | 15.7% |

### Skill Size Categories

- **Minimal (~25 tokens)**: Bare-bones skill with name, description, and single instruction
- **Small (~100 tokens)**: Simple skill with basic instructions and verification
- **Medium (~450 tokens)**: Realistic production skill with methodology and examples
- **Large (~1300 tokens)**: Comprehensive skill approaching recommended limit

## Combined Skills Analysis

| Configuration | Total Tokens | Threshold % | Status |
|---------------|--------------|-------------|--------|
| Meta + 3 small | ~580 | 7.3% | PASS |
| Meta + 3 medium | ~1,616 | 20.2% | PASS |
| Meta + 3 large | ~4,310 | 53.9% | PASS |
| Meta + mixed (small+medium+large) | ~2,169 | 27.1% | PASS |
| Meta + 3 oversized | ~9,500 | 118.8% | FAIL (expected) |

## Findings

### What Works

1. **Skills with 500-1500 tokens** fit comfortably within limits
2. **Multiple skills can coexist** - even 3 large skills + meta-skill stay under 8000 tokens
3. **The meta-skill overhead is minimal** (~314 tokens, 15.7% of single threshold)
4. **Markdown formatting doesn't significantly inflate token count**

### Risks Identified

1. **Very detailed skills** approaching 2000 tokens leave little headroom
2. **Skills with extensive examples** could exceed limits
3. **No enforcement mechanism yet** - skills exceeding thresholds won't be rejected

### Recommendations

1. **Target skill size**: 500-1500 tokens (~2000-6000 chars)
2. **Keep meta-skill under 500 tokens** to maximize space for domain skills
3. **Use bullet points and concise language** over verbose explanations
4. **Avoid redundant explanations** - assume LLM baseline knowledge
5. **Extract large examples** to separate resource files if needed
6. **Test combined size** when designing skill sets for agents

## Test Coverage

Created `tests/validation/general/test_skill_size.py` with:

| Test Class | Tests | Purpose |
|------------|-------|---------|
| TestTokenEstimation | 6 | Validate token estimation utility |
| TestSingleSkillSizeThreshold | 6 | Validate single skill < 2000 tokens |
| TestCombinedSkillsThreshold | 6 | Validate meta + 3 skills < 8000 tokens |
| TestSkillSizeGuidelines | 2 | Document size guidelines |

**Total: 20 tests, all passing**

## Implementation Notes

### Token Estimation Utility

```python
def estimate_tokens(text: str) -> int:
    """Estimate token count: tokens ~= characters / 4"""
    if not text:
        return 0
    return len(text) // 4
```

### SkillSizeAnalysis Dataclass

```python
@dataclass
class SkillSizeAnalysis:
    name: str
    char_count: int
    estimated_tokens: int
    line_count: int
    file_path: Optional[Path] = None

    @property
    def within_single_skill_threshold(self) -> bool:
        return self.estimated_tokens < 2000
```

## Future Work

1. **Integrate tiktoken** for precise token counting when needed
2. **Add skill linting** to warn about oversized skills during installation
3. **Create skill authoring guide** with size recommendations
4. **Consider skill compression** techniques for large skills (chunking, references)

## Conclusion

The assumption that "skill content fits in context window" is **validated**. With the established thresholds:

- Single skill: < 2000 tokens
- Combined (meta + 3 skills): < 8000 tokens

Skills can be designed to fit comfortably within LLM context limits while providing meaningful domain-specific instructions. The test suite provides ongoing validation and the utility functions enable size checking during skill development.
