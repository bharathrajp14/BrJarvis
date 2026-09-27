# 08. Application Package Specification

## Deliverable Bundle Structure

Every job application generates an immutable deliverable package under `workspace/Applications/{package_id}/`:

```
workspace/Applications/pkg_anthropic_4928190/
├── resume.pdf                    # Verified tailored PDF resume
├── resume.docx                   # Formatted DOCX resume
├── resume.html                   # Responsive print HTML resume
├── cover_letter.pdf              # Tailored PDF cover letter
├── cover_letter.txt              # Plaintext cover letter
├── answers.json                  # Semantic form answers with confidence
├── job_description.html          # Snapshot of live job posting
└── application_metadata.json     # Package manifest registered in ArtifactManager
```
