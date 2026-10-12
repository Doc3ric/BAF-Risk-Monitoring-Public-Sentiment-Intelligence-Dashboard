from collectors.base import BaseCollector
from collectors.official_baf import OfficialBAFCollector
from collectors.gdelt import GDELTCollector
from collectors.rss import RSSNewsCollector
from collectors.reddit import RedditCollector
from collectors.manual_import import ManualImportCollector
from collectors.community_dossier import CommunityDossierCollector

__all__ = [
    "BaseCollector",
    "OfficialBAFCollector",
    "GDELTCollector",
    "RSSNewsCollector",
    "RedditCollector",
    "ManualImportCollector",
    "CommunityDossierCollector"
]
