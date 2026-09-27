# 03. Resume Engine & Native Templates Specification

## Native Production Templates (10 Catalogs)

1. **Executive Leadership**: Prestigious navy & slate serif styling with strategic impact metrics.
2. **Modern Minimal**: Clean typography with monochromatic contrast and ample breathing room.
3. **ATS Classic Standard**: Single-column, zero-table, standard bulleted layout for 100% parsing accuracy across Taleo, Workday, Greenhouse, and Lever.
4. **Technical Engineer**: Structured tech matrix with dual-column competencies and engineering metrics.
5. **Developer & Hacker**: Code-aesthetic monospaced highlights with GitHub links and stack badges.
6. **Fresh Graduate & Academic**: Prioritizes academic coursework, honors, and capstone projects.
7. **Startup & Product Innovator**: Vibrant accents with high-velocity product delivery highlights.
8. **AI & Machine Learning Architect**: Dedicated model architecture, training pipeline, and dataset sections.
9. **Cybersecurity & Defense Specialist**: Security certs (CISSP, CEH, OSCP), CVEs, and zero-trust framing.
10. **Compact One-Page**: High-density format fitted perfectly to 1 printed sheet.

## Multi-Format Rendering Pipeline

- **HTML**: Standalone responsive document with inline Google Fonts, CSS custom variables, and `@media print` rules.
- **DOCX**: Microsoft Word `.docx` generated via `python-docx` with native typography and bullet hierarchy.
- **PDF**: Direct vector PDF document generated via `fpdf2` with crisp text rendering.
