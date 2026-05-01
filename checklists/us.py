"""
US jurisdiction legal checklist (Delaware/NY default — most common for US tech contracts).
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


US_CHECKLIST: list[ChecklistItem] = [
    {
        "category": "indemnity",
        "title": "Indemnification",
        "must_have": [
            "Mutual indemnity for third-party claims (IP infringement, bodily injury, property damage)",
            "Indemnity cap — typically 1x to 2x annual fees, with carve-outs",
            "Carve-outs from cap: gross negligence, wilful misconduct, IP indemnity, confidentiality, fraud",
            "Conspicuous (ALL CAPS or BOLD) drafting where required by UCC §2-316 for warranty disclaimers tied to indemnities",
            "Notice and defense procedure (sole control of defense for indemnitor with carve-outs)",
        ],
        "must_avoid": [
            "Uncapped one-way indemnity",
            "Indemnification for first-party damages (overlap with limitation of liability)",
        ],
        "good_language_examples": [
            "Each Party shall defend, indemnify, and hold harmless the other from third-party claims arising out of...",
        ],
        "statutory_hooks": [
            "UCC Article 2 (sale of goods)",
            "Restatement (Second) of Contracts §195 (limitation of liability)",
        ],
    },
    {
        "category": "liability",
        "title": "Limitation of Liability",
        "must_have": [
            "Mutual cap on direct damages",
            "Exclusion of indirect, consequential, special, punitive damages — must be CONSPICUOUS (UCC §2-316, §2-719)",
            "Carve-outs: confidentiality breach, IP infringement, indemnification, gross negligence, fraud",
            "Acknowledgment of essential purpose (anti-failure-of-essential-purpose language)",
        ],
        "must_avoid": [
            "Liability cap that purports to exclude liability for fraud (unenforceable in most US jurisdictions)",
            "Non-conspicuous warranty disclaimers tied to limitation language",
        ],
        "good_language_examples": [
            "IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, CONSEQUENTIAL, SPECIAL, OR PUNITIVE DAMAGES...",
        ],
        "statutory_hooks": [
            "UCC §2-719 (limitation of remedies)",
            "Delaware case law on enforceability of liability caps",
        ],
    },
    {
        "category": "termination",
        "title": "Termination",
        "must_have": [
            "Termination for convenience with notice period (typically 30-60 days)",
            "Termination for material breach with cure period (typically 30 days)",
            "Termination on bankruptcy (subject to §365 of Bankruptcy Code; see Sunbeam doctrine)",
            "Survival of obligations — confidentiality, IP, indemnity, accrued payment, limitation of liability",
            "Effects of termination — data return, transition assistance, final invoicing",
        ],
        "must_avoid": [
            "Perpetual auto-renewal without express opt-out",
            "Penalty clauses (must be liquidated damages reasonably proportionate)",
        ],
        "good_language_examples": [
            "Either Party may terminate this Agreement for material breach by the other Party that remains uncured 30 days after written notice.",
        ],
        "statutory_hooks": [
            "11 U.S.C. §365 (executory contracts in bankruptcy)",
        ],
    },
    {
        "category": "confidentiality",
        "title": "Confidentiality",
        "must_have": [
            "Defined Confidential Information (marking + oral disclosure rules)",
            "Standard exceptions: public domain, prior knowledge, independently developed, third-party receipt, legal compulsion",
            "Term: 3-5 years for general CI; perpetual for trade secrets (per DTSA / state UTSA)",
            "Standard of care: same as own CI, no less than reasonable care",
            "Compelled disclosure procedure (notice and cooperation)",
            "Return / destruction on termination with certification on request",
        ],
        "must_avoid": [
            "Perpetual term for non-trade-secret CI (potentially unenforceable as restraint of trade in California)",
            "No carve-out for residuals if appropriate to the deal",
        ],
        "good_language_examples": [
            "The obligations in this Section shall survive for five (5) years following termination, except with respect to trade secrets, for which the obligations shall survive for so long as such information remains a trade secret under applicable law.",
        ],
        "statutory_hooks": [
            "Defend Trade Secrets Act of 2016 (18 U.S.C. §1836)",
            "Uniform Trade Secrets Act (most states)",
        ],
    },
    {
        "category": "governing_law",
        "title": "Governing Law & Dispute Resolution",
        "must_have": [
            "Choice of law (Delaware and New York are most common for tech)",
            "Forum selection clause",
            "Arbitration vs litigation choice (FAA pre-emption applies for arbitration)",
            "Carve-out for injunctive relief in court for IP / confidentiality",
            "Jury trial waiver (where state-enforceable)",
        ],
        "must_avoid": [
            "California-specific issues if California law applies (no non-competes; restrictive covenants narrowly construed)",
        ],
        "good_language_examples": [
            "This Agreement shall be governed by the laws of the State of Delaware, without regard to its conflict-of-laws principles.",
        ],
        "statutory_hooks": [
            "Federal Arbitration Act (9 U.S.C. §§1-16)",
        ],
    },
    {
        "category": "data_protection",
        "title": "Data Protection (CCPA/CPRA, HIPAA where applicable)",
        "must_have": [
            "Identification of Service Provider / Business roles (CCPA/CPRA)",
            "Purpose limitation and use restrictions",
            "Data breach notification — state-by-state (e.g., CA: in the most expedient time possible)",
            "Sub-processor flow-down obligations",
            "Sale-of-data prohibitions (CCPA/CPRA)",
            "BAA (Business Associate Agreement) provisions where HIPAA applies",
        ],
        "must_avoid": [
            "GDPR-only language ignoring US state laws",
            "Silent on data subject rights / consumer rights",
        ],
        "good_language_examples": [
            "Service Provider shall not sell, retain, use, or disclose Personal Information for any purpose other than the specific purpose of performing the Services...",
        ],
        "statutory_hooks": [
            "California Consumer Privacy Act / California Privacy Rights Act",
            "HIPAA (Health Insurance Portability and Accountability Act)",
            "State breach notification statutes",
        ],
    },
    {
        "category": "ip_assignment",
        "title": "Intellectual Property Assignment",
        "must_have": [
            "Work-made-for-hire language (where applicable; Copyright Act §101)",
            "Present assignment of IP rights (' hereby assigns ', not 'will assign' — Stanford v. Roche)",
            "Pre-existing IP carve-out and licence-back",
            "Moral rights waiver to extent permissible",
            "Patent/invention assignment language for employees / contractors",
            "Open-source disclosure",
        ],
        "must_avoid": [
            "Future-tense assignments only ('will assign' — fails under Filmtec / Stanford v. Roche)",
            "Ambiguity on derivative works",
        ],
        "good_language_examples": [
            "Supplier hereby irrevocably assigns to Customer all right, title, and interest in and to the Deliverables, including all Intellectual Property Rights therein.",
        ],
        "statutory_hooks": [
            "17 U.S.C. §101 (work made for hire)",
            "35 U.S.C. §261 (assignment of patents)",
            "Stanford v. Roche, 563 U.S. 776 (2011)",
        ],
    },
]
