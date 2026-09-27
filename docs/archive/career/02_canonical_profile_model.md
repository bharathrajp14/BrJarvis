# 02. Canonical Career Profile Model Specification

## Canonical Data Structure

The `CareerProfile` serves as the authoritative single source of truth for candidate background, preferences, and verified achievements.

### Core Schemas
- `ContactInfo`: Full name, verified email, phone, location, LinkedIn, GitHub, portfolio URLs.
- `EducationEntry`: Institution, degree, field of study, dates, GPA/grade, honors.
- `ExperienceEntry`: Company, title, location, remote mode, responsibilities, quantifiable metrics, technologies used.
- `ProjectEntry`: Project title, description, architecture highlights, tech stack, live URLs.
- `SkillCategory`: Grouped technical competencies (e.g., Languages, Frameworks, Cloud, ML).
- `WorkPreferences`: Target roles, preferred industries, location preferences, remote status, work authorization.
- `SalaryPreferences`: Minimum acceptable salary, target annual base, currency.
- `ProfileFact`: Provenance record tracking value, source (User Input, Verified Doc, Resume Parse), verification status, and confidence score.

### Persistence Strategy
- Storage: `workspace/Career/master_profile.json` and SQLite database (`career_profiles` table).
- Synchronization: Verified skills, target roles, and executive pitch sync to `UnifiedMemory` (L3 vector & L4 persistent memory).
