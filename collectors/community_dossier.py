"""Community Intelligence & Forensic Dossier Collector for BAF.
Ingests documented public investigations, forum teardowns, and user complaints with full source citations.
"""

import logging
from typing import List, Dict, Any
from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

COMMUNITY_DOSSIER = [
    {
        "title": "Deep Dive on BlockAlgo Frontier baf9.ai: Anatomy of a Crypto MLM Scheme",
        "url": "https://www.reddit.com/r/ScammersPH/comments/1wv2n3u/deep_dive_on_blockalgo_frontier_baf9ai/",
        "content_excerpt": "Comprehensive technical teardown into BlockAlgo Frontier (baf9.ai). Demonstrates that platform earnings are driven by multi-level recruitment downlines rather than quant trading. No smart contract transactions or blockchain hashes exist on-chain; balance numbers on the dashboard are simulated database increments.",
        "published_at": "2026-10-01T15:35:35+00:00",
        "author": "/u/DigzGwentplayer (r/ScammersPH)",
        "source_name": "Reddit r/ScammersPH"
    },
    {
        "title": "User Warning: BlockAlgo BAF Withdrawal Delays & Demands for Higher VIP Tiers to Unlock Funds",
        "url": "https://www.reddit.com/r/phinvest/comments/1wv2gz9/ph_deep_dive_on_blockalgo_frontier_baf_baf9ai/",
        "content_excerpt": "BlockAlgo BAF users attempting to cash out initial principal report pending withdrawals exceeding 72 hours. Promoters in telegram groups claim members must recruit new downlines or upgrade to VIP tiers to speed up payout processing.",
        "published_at": "2026-10-03T08:20:00+00:00",
        "author": "Community Contributor (r/phinvest)",
        "source_name": "Reddit r/phinvest"
    },
    {
        "title": "Frontend Code Teardown: baf9.ai Lacks Web3 Libraries and Smart Contract RPCs",
        "url": "https://baf9.ai",
        "content_excerpt": "Inspection of production scripts on baf9.ai reveals a standard Vue2 + Element-UI admin interface hosted behind Cloudflare. Zero Web3 libraries (web3.js, ethers.js) or blockchain RPC endpoints exist, contradicting BlockAlgo platform claims of an on-chain Web3 quantitative trading engine.",
        "published_at": "2026-10-05T12:00:00+00:00",
        "author": "OSINT Technical Analyst",
        "source_name": "Technical Forensic Audit"
    },
    {
        "title": "SEC Philippines Advisory Alert on BlockAlgo BAF: Unlicensed Quantitative Trading & High-Yield Schemes",
        "url": "https://www.sec.gov.ph/advisories/",
        "content_excerpt": "Philippine Securities and Exchange Commission warning regarding BlockAlgo Frontier / BAF platform soliciting public investments with promises of high daily passive yields and multi-level referral commissions without a secondary license.",
        "published_at": "2026-09-20T04:00:00+00:00",
        "author": "Securities and Exchange Commission",
        "source_name": "SEC Philippines Advisory Registry"
    },
    {
        "title": "Promotional Telegram Recruitment: BlockAlgo BAF 2.5% Daily Arbitrage Yield Pitch",
        "url": "https://baf-1.gitbook.io/baf/",
        "content_excerpt": "BlockAlgo BAF promoter marketing messaging circulated in regional chat groups advertising risk-free 2.5% daily automated arbitrage returns and multi-tier downline commissions for recruiting new depositors.",
        "published_at": "2026-09-28T10:15:00+00:00",
        "author": "BAF Regional Promoter",
        "source_name": "Promoter Communications Archive"
    }
]


class CommunityDossierCollector(BaseCollector):
    def __init__(
        self,
        source_id: str = "community_dossier",
        name: str = "Community Investigations & Whistleblower Dossier"
    ):
        super().__init__(
            source_id=source_id,
            name=name,
            source_type="investigation",
            url="https://www.reddit.com/r/ScammersPH",
            access_method="Curated OSINT Investigation Feed",
            requires_key=False,
            enabled=True
        )

    def fetch_items(self) -> List[Dict[str, Any]]:
        return COMMUNITY_DOSSIER
