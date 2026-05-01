"""
EU jurisdiction legal checklist (GDPR-aware, with member-state nuance).
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


EU_CHECKLIST: list[ChecklistItem] = [
    {
        "category": "indemnity",
        "title": "Indemnification",
        "must_have": [
            "Mutual indemnity for third-party IP infringement claims",
            "Indemnity cap (national civil-code limits apply; e.g., German BGB §276 prohibits exclusion of liability for intent)",
            "Carve-outs from cap: gross negligence, intent, life/body/health, mandatory statutory liability",
            "Notice-and-defence procedure",
        ],
        "must_avoid": [
            "Unlimited indemnities running only against one party",
            "Exclusions of liability that violate national civil-code mandatory protections (BGB §276 in DE; etc.)",
        ],
        "good_language_examples": [
            "Subject to the limitations in Section [X], each Party shall indemnify the other against third-party claims arising out of...",
        ],
        "statutory_hooks": [
            "National civil codes (BGB Germany, Code Civil France)",
            "B2B unfair contract terms statutes (e.g., German AGB law)",
        ],
    },
    {
        "category": "liability",
        "title": "Limitation of Liability",
        "must_have": [
            "Mutual liability cap consistent with national rules",
            "Mandatory carve-outs: intent, gross negligence, personal injury, life-and-health, fraud (cannot be limited)",
            "Exclusion of indirect / consequential damages — must conform to local enforceability tests (e.g., German AGB review)",
            "Carve-outs for confidentiality, IP, data protection",
        ],
        "must_avoid": [
            "Boilerplate US-style 'IN NO EVENT' clauses without local-law review (often partially unenforceable in DE)",
            "Caps below 'foreseeable damage' threshold for ordinary negligence (DE BGB §276)",
        ],
        "good_language_examples": [
            "The aggregate liability of each Party under or in connection with this Agreement, except for liability arising from intent, gross negligence, or injury to life, body, or health, shall be limited to [amount].",
        ],
        "statutory_hooks": [
            "BGB §§276, 309 (Germany)",
            "Member-state implementation of Unfair Contract Terms Directive 93/13/EEC (B2C)",
        ],
    },
    {
        "category": "termination",
        "title": "Termination",
        "must_have": [
            "Termination for convenience with notice period",
            "Extraordinary termination for cause (Außerordentliche Kündigung in DE) — typically non-waivable",
            "Termination on insolvency proceedings (subject to local insolvency-law restrictions on ipso-facto clauses)",
            "Survival clause (confidentiality, IP, data protection, accrued payment, liability provisions)",
            "Data return / deletion on termination (aligned with GDPR Art. 28(3)(g))",
        ],
        "must_avoid": [
            "Penalty clauses without judicial-mitigation acknowledgement",
            "Waiver of statutorily mandatory termination rights",
        ],
        "good_language_examples": [
            "The right of either Party to terminate this Agreement for cause for good cause (wichtiger Grund) shall remain unaffected.",
        ],
        "statutory_hooks": [
            "BGB §314 (extraordinary termination)",
            "Member-state insolvency codes",
        ],
    },
    {
        "category": "confidentiality",
        "title": "Confidentiality",
        "must_have": [
            "Definition of Confidential Information aligned with EU Trade Secrets Directive (2016/943)",
            "Reasonable steps to maintain secrecy (qualifying for trade-secret protection)",
            "Standard exceptions (public domain, independently developed, third-party receipt, legal compulsion)",
            "Term — 3-5 years for general CI; for trade secrets, as long as the secret subsists",
            "Compelled disclosure procedure",
        ],
        "must_avoid": [
            "Insufficient secrecy measures language (could lose trade-secret protection)",
            "Confidentiality terms operating as non-competes without reasonableness review",
        ],
        "good_language_examples": [
            "The Receiving Party shall take reasonable steps under the circumstances to keep the Confidential Information secret, in line with Article 2(1)(c) of Directive (EU) 2016/943.",
        ],
        "statutory_hooks": [
            "EU Trade Secrets Directive 2016/943 (and national transpositions)",
        ],
    },
    {
        "category": "governing_law",
        "title": "Governing Law & Dispute Resolution",
        "must_have": [
            "Choice of law conforming to Rome I (Reg. 593/2008)",
            "Forum selection conforming to Brussels I Recast (Reg. 1215/2012)",
            "Arbitration alternative if cross-border (NY Convention 1958)",
            "Carve-out for interim relief",
            "Language of proceedings",
        ],
        "must_avoid": [
            "Choice of law that defeats mandatory consumer / employee protections",
            "Forum clauses violating exclusive jurisdiction rules",
        ],
        "good_language_examples": [
            "This Agreement shall be governed by the laws of [Member State], without regard to its conflict-of-laws rules. The courts of [City, Member State] shall have exclusive jurisdiction.",
        ],
        "statutory_hooks": [
            "Rome I Regulation (EC) No 593/2008",
            "Brussels I Recast Regulation (EU) No 1215/2012",
        ],
    },
    {
        "category": "data_protection",
        "title": "Data Protection (GDPR)",
        "must_have": [
            "Roles: Controller / Processor / Joint Controller (GDPR Art. 4, 26, 28)",
            "Mandatory DPA terms per GDPR Art. 28(3): subject matter, duration, nature, purpose, types of data, categories of subjects, obligations",
            "Sub-processor authorisation procedure (Art. 28(2))",
            "International transfer mechanism — SCCs (Decision 2021/914) or adequacy decision; supplementary measures post-Schrems II",
            "Breach notification: Processor to Controller without undue delay (Art. 33(2))",
            "DSR assistance (Art. 28(3)(e)), audit rights (Art. 28(3)(h))",
            "Erasure / return of personal data on termination (Art. 28(3)(g))",
            "Records of processing (Art. 30)",
        ],
        "must_avoid": [
            "Pre-2021 SCCs (replaced by 2021 SCCs)",
            "International transfer language without Schrems II / TIA reference",
            "Generic 'reasonable security measures' without Art. 32 specifics",
        ],
        "good_language_examples": [
            "The Processor shall process Personal Data only on the documented instructions of the Controller, in accordance with Article 28(3)(a) GDPR, including with regard to international transfers, which shall be subject to the Standard Contractual Clauses (Decision 2021/914) and any necessary supplementary measures.",
        ],
        "statutory_hooks": [
            "GDPR (Reg. (EU) 2016/679)",
            "ePrivacy Directive 2002/58/EC",
            "Schrems II (CJEU C-311/18)",
        ],
    },
    {
        "category": "ip_assignment",
        "title": "Intellectual Property Assignment",
        "must_have": [
            "Express assignment language compliant with national rules (some jurisdictions require specific written form)",
            "Moral rights — note that moral rights are inalienable in many EU jurisdictions (FR, DE); use waiver of exercise rather than assignment",
            "Pre-existing IP carve-out and licence-back",
            "Database rights (sui generis EU database right) where applicable",
            "Open-source compliance with GPL / AGPL / EUPL etc.",
        ],
        "must_avoid": [
            "Assignment of moral rights in jurisdictions where they are inalienable (e.g., France)",
            "Boilerplate US 'work-made-for-hire' language (concept does not map cleanly to EU)",
        ],
        "good_language_examples": [
            "To the extent permitted by applicable law, the Supplier hereby assigns to the Customer all transferable Intellectual Property Rights in the Deliverables. With respect to non-transferable rights (including moral rights), the Supplier hereby grants the Customer an exclusive, worldwide, perpetual, royalty-free licence and undertakes not to exercise such rights against the Customer.",
        ],
        "statutory_hooks": [
            "InfoSoc Directive 2001/29/EC",
            "EU Database Directive 96/9/EC",
            "National copyright laws (e.g., French CPI; German UrhG)",
        ],
    },
]
