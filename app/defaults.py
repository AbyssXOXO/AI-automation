##Default Scraping Targets & Exclusions.
#Contains the built-in list of Microsoft, Google, and IBM developer hubs 
#that the bot monitors out-of-the-box. It also includes a blacklist of 
#generic website headings (like "Learn More" or "Home") so the scraper 
#knows to ignore useless navigation links.

from __future__ import annotations

from typing import Any


GENERIC_SECTION_TITLES = {
    "all events",
    "applied skills",
    "career paths",
    "certification challenges",
    "certifications",
    "codelabs",
    "connect",
    "course catalog",
    "courses",
    "developer consoles",
    "discover your path",
    "events",
    "expand your horizons",
    "explore available learning",
    "featured events",
    "featured news",
    "get started by selecting a learning path",
    "get started",
    "join our student community",
    "languages",
    "learning paths",
    "more",
    "new and recently updated",
    "opportunities",
    "options",
    "our current favorites",
    "popular learning paths and modules",
    "products",
    "programs",
    "recent events",
    "resources",
    "source",
    "student essentials for microsoft",
    "student hub",
    "student resources",
    "technical skills",
    "topics",
    "upcoming events",
    "workplace skills",
}


DEFAULT_BIG_TECH_SCRAPE_TARGETS: list[dict[str, Any]] = [
    {
        "name": "Google for Developers Events",
        "url": "https://developers.google.com/events/",
        "company": "Google",
        "category": "events and hackathons",
        "limit": 8,
    },
    {
        "name": "Google Cloud Skills Boost Paths",
        "url": "https://www.cloudskillsboost.google/paths/?locale=en",
        "company": "Google",
        "category": "free courses",
        "limit": 8,
    },
    {
        "name": "Google Developers Codelabs",
        "url": "https://developers.google.com/codelabs",
        "company": "Google",
        "category": "codelabs and tutorials",
        "limit": 6,
    },
    {
        "name": "Microsoft Learn Student Hub",
        "url": "https://learn.microsoft.com/en-us/training/student-hub/",
        "company": "Microsoft",
        "category": "student opportunities",
        "limit": 8,
    },
    {
        "name": "Microsoft Learn Hack Together",
        "url": "https://learn.microsoft.com/en-us/training/student-hub/hack-together",
        "company": "Microsoft",
        "category": "hackathons",
        "limit": 6,
    },
    {
        "name": "Microsoft Credentials AI Challenge",
        "url": "https://learn.microsoft.com/en-us/credentials/microsoft-credentials-ai-challenge",
        "company": "Microsoft",
        "category": "free challenges and vouchers",
        "limit": 8,
    },
    {
        "name": "Microsoft Student Credentials",
        "url": "https://learn.microsoft.com/en-us/training/student-hub/credentials",
        "company": "Microsoft",
        "category": "free credentials",
        "limit": 8,
    },
    {
        "name": "IBM SkillsBuild",
        "url": "https://skillsbuild.org/",
        "company": "IBM",
        "category": "free courses and events",
        "limit": 8,
    },
    {
        "name": "IBM SkillsBuild Course Catalog",
        "url": "https://skillsbuild.org/students/course-catalog",
        "company": "IBM",
        "category": "free course catalog",
        "limit": 8,
    },
    {
        "name": "IBM Free Digital Learning",
        "url": "https://www.ibm.com/new/training/free-digital-learning",
        "company": "IBM",
        "category": "free learning",
        "limit": 6,
    },
]

