"""
India jurisdiction legal checklist.

Each category encodes:
  - what the Critic should look for
  - what good language looks like (drafter guidance)
  - India-specific statutory hooks

Coverage > 7 categories (brief mandates minimum 7).
"""

from __future__ import annotations
from typing import TypedDict


class ChecklistItem(TypedDict):
    category: str
    title: str
    must_have: list[str]
    must_avoid: list[str]
    good_language_examples: list[str]
    statutory_hooks: list[str]


INDIA_CHECKLIST: list[ChecklistItem] = [
    {
        "category": "indemnity",
        "title": "Indemnification",
        "must_have": [
            "Mutual indemnity for third-party IP infringement claims",
            "Indemnity must be capped (not unlimited) — 1x to 2x annual fees is market for SaaS in India",
            "Carve-outs for indemnity cap: gross negligence, wilful misconduct, breach of confidentiality, IP infringement",
            "Notice and control-of-defence procedure",
        ],
        "must_avoid": [
            "Uncapped one-sided indemnities running only against the supplier",
            "Indemnification triggered by 'any claim' rather than third-party claims",
        ],
        "good_language_examples": [
            "Each Party shall indemnify the other against third-party claims arising out of...",
            "The indemnifying Party's aggregate liability under this clause shall not exceed [X]...",
        ],
        "statutory_hooks": [
            "Indian Contract Act, 1872, Sections 124-125 (contract of indemnity)",
        ],
    },
    {
        "category": "liability",
        "title": "Limitation of Liability",
        "must_have": [
            "Mutual liability cap (typically 1x to 2x fees paid in trailing 12 months)",
            "Exclusion of indirect, consequential, special, punitive damages",
            "Carve-outs from cap: confidentiality breach, IP infringement, indemnification, gross negligence, fraud",
        ],
        "must_avoid": [
            "One-sided liability cap protecting only the larger party",
            "Caps that purport to exclude liability for fraud or wilful misconduct (unenforceable in India)",
        ],
        "good_language_examples": [
            "Neither Party shall be liable for any indirect, incidental, consequential, or punitive damages...",
            "Each Party's aggregate liability shall not exceed the fees paid in the 12 months preceding the claim.",
        ],
        "statutory_hooks": [
            "Indian Contract Act, 1872, Section 23 (unlawful agreements)",
        ],
    },
    {
        "category": "termination",
        "title": "Termination",
        "must_have": [
            "Termination for convenience (with notice period, typically 30-90 days)",
            "Termination for cause with cure period (typically 30 days)",
            "Termination on insolvency / bankruptcy",
            "Survival clause for confidentiality, IP, indemnity, payment obligations",
            "Effects of termination: data return / deletion, final invoicing",
        ],
        "must_avoid": [
            "One-sided termination rights",
            "Penalty clauses for termination (Indian Contract Act §74 — only reasonable compensation)",
            "Auto-renewal without express opt-out window",
        ],
        "good_language_examples": [
            "Either Party may terminate this Agreement for convenience by giving 60 days' written notice.",
            "On termination, Supplier shall return or destroy all Customer Data within 30 days...",
        ],
        "statutory_hooks": [
            "Indian Contract Act, 1872, Section 74 (penalty vs liquidated damages)",
        ],
    },
    {
        "category": "confidentiality",
        "title": "Confidentiality",
        "must_have": [
            "Definition of Confidential Information including marking and oral disclosure rules",
            "Standard exceptions: public domain, independently developed, lawful third-party receipt, legal compulsion",
            "Term of confidentiality (3-5 years post-termination, perpetual for trade secrets)",
            "Standard of care (at least the standard the Receiving Party uses for its own confidential information, but no less than reasonable care)",
            "Permitted disclosures (employees, advisors, on a need-to-know basis with binding obligations)",
        ],
        "must_avoid": [
            "Indefinite confidentiality term for non-trade-secret information (problematic under India's evolving data laws)",
            "No carve-out for legally compelled disclosure",
        ],
        "good_language_examples": [
            "Receiving Party shall protect Confidential Information using at least the same degree of care as it uses for its own confidential information, but no less than reasonable care.",
        ],
        "statutory_hooks": [
            "Indian Contract Act, 1872 (general)",
            "Sections 72/72A, IT Act 2000 (penalties for breach of confidentiality)",
        ],
    },
    {
        "category": "governing_law",
        "title": "Governing Law & Dispute Resolution",
        "must_have": [
            "Express choice of governing law (e.g., 'laws of India')",
            "Seat and venue for dispute resolution",
            "Arbitration mechanism (Arbitration and Conciliation Act 1996) with seat, language, and rules",
            "Carve-out for injunctive relief in court for IP / confidentiality breach",
        ],
        "must_avoid": [
            "Ambiguous choice of law",
            "Foreign seat with no India enforcement consideration for an India-based party",
        ],
        "good_language_examples": [
            "This Agreement shall be governed by the laws of India. Any dispute shall be referred to arbitration under the Arbitration and Conciliation Act, 1996, with the seat at [Mumbai] and conducted in English.",
        ],
        "statutory_hooks": [
            "Arbitration and Conciliation Act, 1996",
            "Code of Civil Procedure, 1908",
        ],
    },
    {
        "category": "data_protection",
        "title": "Data Protection (DPDP Act 2023)",
        "must_have": [
            "Identification of Data Fiduciary and Data Processor roles per DPDP Act 2023",
            "Purpose limitation, lawful basis (consent or legitimate use)",
            "Data breach notification timelines (72 hours to Data Protection Board / affected principals)",
            "Cross-border transfer restrictions (subject to government notified countries)",
            "Sub-processor obligations (flow-down terms)",
            "Data deletion on termination / request",
        ],
        "must_avoid": [
            "Generic GDPR-only language without DPDP mapping for an Indian counterparty",
            "Silent on breach notification timelines",
        ],
        "good_language_examples": [
            "Processor shall notify Controller of any Personal Data Breach without undue delay and in any event within 48 hours of discovery, in compliance with the DPDP Act, 2023.",
        ],
        "statutory_hooks": [
            "Digital Personal Data Protection Act, 2023",
            "IT (Reasonable Security Practices) Rules, 2011",
        ],
    },
    {
        "category": "ip_assignment",
        "title": "Intellectual Property Assignment",
        "must_have": [
            "Clear assignment of IP in deliverables / work product",
            "Carve-out for pre-existing IP and background IP",
            "Licence-back of background IP needed to use deliverables",
            "Moral-rights waiver where applicable (Copyright Act §57)",
            "Open-source / third-party material disclosure obligations",
        ],
        "must_avoid": [
            "Ambiguity on whether 'work product' includes derivative works",
            "Failure to address moral rights — waivers not implied under Indian law",
        ],
        "good_language_examples": [
            "Supplier hereby assigns to Customer all right, title, and interest, including all Intellectual Property Rights, in the Deliverables. Supplier waives all moral rights in respect of the Deliverables to the maximum extent permitted by law.",
        ],
        "statutory_hooks": [
            "Copyright Act, 1957 (especially §17, §19, §57)",
            "Patents Act, 1970",
        ],
    },
]
