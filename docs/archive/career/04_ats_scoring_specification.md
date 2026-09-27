# 04. Deterministic ATS Scoring Specification

## 7-Factor Evaluation Dimensions

1. **Keyword Coverage & Semantic Alignment (25% Weight)**: Computes overlap between job description tokens and candidate competencies.
2. **Standard Section Recognition (20% Weight)**: Validates presence of standard headings (Summary, Experience, Education, Skills, Projects).
3. **Parsing Risk Analysis (15% Weight)**: Evaluates layout complexity, tables, uncommon unicode symbols, and contact field presence.
4. **Readability & Action Verb Ratio (15% Weight)**: Analyzes sentence length and presence of strong action verbs (Engineered, Architected, Deployed).
5. **Formatting Consistency (10% Weight)**: Checks date format uniformity and chronological ordering.
6. **Role Relevance (15% Weight)**: Evaluates target title and domain seniority match against job requirements.

## Letter Grade Scale
- **A+** (95.0 – 100.0%): Flawless ATS compliance and keyword alignment.
- **A** (85.0 – 94.9%): High-tier screening probability across enterprise parsers.
- **B** (72.0 – 84.9%): Solid structure; recommended keyword optimizations.
- **C** (55.0 – 71.9%): Missing standard sections or low keyword overlap.
- **D** (< 55.0%): Significant parsing risks or missing critical contact data.
