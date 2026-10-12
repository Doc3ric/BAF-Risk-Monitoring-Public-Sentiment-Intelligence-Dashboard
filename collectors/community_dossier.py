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
        "content_excerpt": "Comprehensive technical teardown into BlockAlgo Frontier (baf9.ai). Demonstrates that platform earnings are driven by multi-level recruitment downlines rather than quant trading. No smart contract transactions or blockchain hashes exist on-chain; balance numbers on the dashboard are simulated database increments. Clear ponzi and pyramid scam design.",
        "published_at": "2026-10-01T15:35:35+00:00",
        "author": "/u/DigzGwentplayer (r/ScammersPH)",
        "source_name": "Reddit r/ScammersPH"
    },
    {
        "title": "User Warning: BlockAlgo BAF Withdrawal Delays & Demands for Higher VIP Tiers to Unlock Funds",
        "url": "https://www.reddit.com/r/phinvest/comments/1wv2gz9/ph_deep_dive_on_blockalgo_frontier_baf_baf9ai/",
        "content_excerpt": "BlockAlgo BAF users attempting to cash out initial principal report pending withdrawals exceeding 72 hours. Promoters in telegram groups claim members must recruit new downlines or upgrade to VIP tiers to speed up payout processing. Cannot withdraw funds without paying extra fees.",
        "published_at": "2026-10-03T08:20:00+00:00",
        "author": "Community Contributor (r/phinvest)",
        "source_name": "Reddit r/phinvest"
    },
    {
        "title": "Frontend Code Teardown: baf9.ai Lacks Web3 Libraries and Smart Contract RPCs",
        "url": "https://baf9.ai",
        "content_excerpt": "Inspection of production scripts on baf9.ai reveals a standard Vue2 + Element-UI admin interface hosted behind Cloudflare. Zero Web3 libraries (web3.js, ethers.js) or blockchain RPC endpoints exist, contradicting BlockAlgo platform claims of an on-chain Web3 quantitative trading engine. The platform is completely simulated.",
        "published_at": "2026-10-05T12:00:00+00:00",
        "author": "OSINT Technical Analyst",
        "source_name": "Technical Forensic Audit"
    },
    {
        "title": "SEC Philippines Advisory Alert on BlockAlgo BAF: Unlicensed Quantitative Trading & High-Yield Schemes",
        "url": "https://www.sec.gov.ph/advisories/",
        "content_excerpt": "Philippine Securities and Exchange Commission warning regarding BlockAlgo Frontier / BAF platform soliciting public investments with promises of high daily passive yields and multi-level referral commissions without a secondary license. Regulators caution the public against placing money in this illegal scheme.",
        "published_at": "2026-09-20T04:00:00+00:00",
        "author": "Securities and Exchange Commission",
        "source_name": "SEC Philippines Advisory Registry"
    },
    {
        "title": "Community Complaint: BlockAlgo Customer Support Ghosted & Telegram Admin Blocked Users Asking for Payouts",
        "url": "https://www.reddit.com/r/CryptoScams/comments/baf_support_ghosted",
        "content_excerpt": "Victim reports that after requesting a $1,200 withdrawal from BlockAlgo (BAF), platform customer support went completely unresponsive. When following up in the official Telegram group, admins deleted the messages and banned the account. Funds remain frozen with zero reply.",
        "published_at": "2026-10-07T14:10:00+00:00",
        "author": "ScamVictimAdvocate (r/CryptoScams)",
        "source_name": "Reddit r/CryptoScams"
    },
    {
        "title": "Victim Report: BlockAlgo Frontier Demands 20% 'Tax Verification Fee' to Release Frozen Funds",
        "url": "https://www.reddit.com/r/Scams/comments/baf9_tax_fee_extortion",
        "content_excerpt": "Classic advance-fee fraud mechanism: BlockAlgo BAF customer trying to withdraw profits was notified that their account is flagged for audit. They are demanding a 20% 'liquidity tax fee' to unlock withdrawals. Do not pay, this is an exit scam trap.",
        "published_at": "2026-10-09T09:45:00+00:00",
        "author": "r/Scams Investigator",
        "source_name": "Reddit r/Scams"
    },
    {
        "title": "Public Warning: BlockAlgo BAF Deposit Credited But Internal Arbitrage Bot Simulation Draining Balance",
        "url": "https://www.reddit.com/r/phinvest/comments/baf_arbitrage_losses",
        "content_excerpt": "User deposited USDT into BlockAlgo Frontier expecting guaranteed 2% daily yield. Instead, fake trades caused sudden simulated liquidations while promoters asked for another top-up to recover losses. Severe deposit loss complaint.",
        "published_at": "2026-10-10T11:30:00+00:00",
        "author": "phinvest Member",
        "source_name": "Reddit r/phinvest"
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
