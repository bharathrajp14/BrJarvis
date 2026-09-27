# 06. Job Engine & Platform Adapters Specification

## Supported Discovery Adapters

- **Greenhouse Adapter**: Direct API board integration (`boards-api.greenhouse.io`) across leading technology organizations.
- **Lever Adapter**: Postings API integration (`api.lever.co/v0/postings`) extracting structured job descriptions and question requirements.
- **Ashby Adapter**: Public job board API integration (`api.ashbyhq.com/posting-api/job-board`).
- **Generic Browser Adapter**: Playwright-powered career portal discovery respecting anti-bot boundaries.

## Deduplication Pipeline
Uses composite signature hashing (`hashlib.sha256(company|title|location)`) and canonical URL normalization to strip tracking parameters (`utm_source`, `ref`, `gh_src`) and prevent duplicate listings.
