"""Data sources and acquisition adapters for UK Planning & Housing Data."""

import json
import logging
import os
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

PLANNING_DATA_GOV_UK_BASE = "https://www.planning.data.gov.uk"
USER_AGENT = "okf-planning/0.2.0 (+https://github.com/chris-page-gov/okf-planning)"


class AcquisitionError(RuntimeError):
    """Raised when a live snapshot cannot be acquired safely."""

# Curated planning policy & guidance datasets to augment planning.data.gov.uk
POLICY_AND_GUIDANCE_AUGMENTATIONS: list[dict[str, Any]] = [
    {
        "dataset": "nppf-framework-policy",
        "name": "National Planning Policy Framework (NPPF)",
        "plural": "National Planning Policy Framework sections",
        "collection": "planning-policy",
        "typology": "policy",
        "description": "The National Planning Policy Framework sets out the Government's planning policies for England and how these are expected to be applied, including housing targets, sustainable development, Green Belt protection, design codes, and biodiversity net gain.",
        "text": "Core national policy framework governing local plan development, housing delivery test calculations, presumption in favour of sustainable development (Paragraph 11), and statutory consultee considerations.",
        "themes": ["development", "housing", "environment", "heritage"],
        "phase": "live",
        "licence": "ogl3",
        "licence-text": "Licensed under the Open Government Licence v.3.0",
        "attribution": "crown-copyright",
        "attribution-text": "© Crown copyright Ministry of Housing, Communities & Local Government",
        "entity-count": 17,
        "source_url": "https://www.gov.uk/government/publications/national-planning-policy-framework--2",
        "documentation_url": "https://www.gov.uk/guidance/national-planning-policy-framework",
        "wikidata": "Q6974911",
    },
    {
        "dataset": "planning-practice-guidance",
        "name": "Planning Practice Guidance (PPG)",
        "plural": "Planning Practice Guidance suites",
        "collection": "planning-policy",
        "typology": "policy",
        "description": "Gov.uk web-based category guidance accompanying the NPPF, covering Use Classes, Permitted Development Rights, Section 106 agreements, CIL, Viability, EIA, SHLAA, and Brownfield Land Registers.",
        "text": "Detailed operational planning guidance suite issued by MHCLG to assist local planning authorities, developers, and citizens in interpreting planning legislation and policy.",
        "themes": ["development", "housing", "specification", "monitoring"],
        "phase": "live",
        "licence": "ogl3",
        "licence-text": "Licensed under the Open Government Licence v.3.0",
        "attribution": "crown-copyright",
        "attribution-text": "© Crown copyright Ministry of Housing, Communities & Local Government",
        "entity-count": 48,
        "source_url": "https://www.gov.uk/government/collections/planning-practice-guidance",
        "documentation_url": "https://www.gov.uk/guidance/use-of-planning-conditions",
        "wikidata": "",
    },
    {
        "dataset": "town-and-country-planning-act-1990",
        "name": "Town and Country Planning Act 1990",
        "plural": "Town and Country Planning Act 1990 sections",
        "collection": "legislation",
        "typology": "legal-instrument",
        "description": "Primary Act of Parliament regulating the development of land in England and Wales, defining planning permission, planning obligations (Section 106), enforcement powers, and purchase notices.",
        "text": "The foundation of modern UK land use planning law, establishing control over development, statutory definitions of 'development', and authority for Local Planning Authorities.",
        "themes": ["administrative", "development", "specification"],
        "phase": "live",
        "licence": "ogl3",
        "licence-text": "Licensed under the Open Government Licence v.3.0",
        "attribution": "crown-copyright",
        "attribution-text": "© Crown copyright The National Archives",
        "entity-count": 336,
        "source_url": "https://www.legislation.gov.uk/ukpga/1990/8/contents",
        "documentation_url": "https://www.legislation.gov.uk/ukpga/1990/8",
        "wikidata": "Q7830089",
    },
    {
        "dataset": "levelling-up-and-regeneration-act-2023",
        "name": "Levelling-up and Regeneration Act 2023 (LURA)",
        "plural": "Levelling-up and Regeneration Act 2023 sections",
        "collection": "legislation",
        "typology": "legal-instrument",
        "description": "Statutory Act establishing National Development Management Policies (NDMPs), statutory local plan timetables, mandatory design codes, Infrastructure Levy, and environmental outcome reports.",
        "text": "Major legislative reform introducing statutory status for National Development Management Policies, street votes, and streamlined plan-making processes.",
        "themes": ["administrative", "development", "housing", "environment"],
        "phase": "live",
        "licence": "ogl3",
        "licence-text": "Licensed under the Open Government Licence v.3.0",
        "attribution": "crown-copyright",
        "attribution-text": "© Crown copyright The National Archives",
        "entity-count": 252,
        "source_url": "https://www.legislation.gov.uk/ukpga/2023/55/contents",
        "documentation_url": "https://www.legislation.gov.uk/ukpga/2023/55",
        "wikidata": "Q123284000",
    },
    {
        "dataset": "use-classes-order-1987",
        "name": "Town and Country Planning (Use Classes) Order 1987 (as amended)",
        "plural": "Use Classes Order classifications",
        "collection": "legislation",
        "typology": "legal-instrument",
        "description": "Statutory Instrument categorising the use of land and buildings (Class E Commercial, Class C3 Dwellinghouses, Class C4 HMOs, Class B2/B8 Industrial, Sui Generis).",
        "text": "Defines building use classes and changes of use that do not constitute development under planning law, significantly revised in 2020 to introduce Class E.",
        "themes": ["development", "housing", "specification"],
        "phase": "live",
        "licence": "ogl3",
        "licence-text": "Licensed under the Open Government Licence v.3.0",
        "attribution": "crown-copyright",
        "attribution-text": "© Crown copyright The National Archives",
        "entity-count": 18,
        "source_url": "https://www.legislation.gov.uk/uksi/1987/764/contents",
        "documentation_url": "https://www.gov.uk/guidance/change-of-use",
        "wikidata": "",
    },
    {
        "dataset": "historic-england-nhle-heritage",
        "name": "National Heritage List for England (NHLE)",
        "plural": "National Heritage List entries",
        "collection": "historic-england",
        "typology": "geography",
        "description": "Official database of statutory protected historic buildings, scheduled monuments, registered parks and gardens, battlefields, and protected wreck sites in England published by Historic England.",
        "text": "Defines spatial boundaries, grade designations (Grade I, Grade II*, Grade II), and legal protection entries cross-referenced with planning application constraints.",
        "themes": ["heritage", "environment"],
        "phase": "live",
        "licence": "ogl3",
        "licence-text": "Contains Historic England data © Historic England 2026",
        "attribution": "historic-england",
        "attribution-text": "© Historic England 2026. Contains Ordnance Survey data © Crown copyright and database right 2026",
        "entity-count": 405120,
        "source_url": "https://historicengland.org.uk/listing/the-list/",
        "documentation_url": "https://historicengland.org.uk/services-skills/dataset-downloads/",
        "wikidata": "Q6973052",
    },
    {
        "dataset": "environment-agency-flood-risk-zones",
        "name": "Environment Agency Flood Risk Zones 2 & 3",
        "plural": "Flood Risk Zone spatial polygons",
        "collection": "flood-risk-zone",
        "typology": "geography",
        "description": "Statutory spatial boundaries for river and sea flood risk zones used by local planning authorities to apply the Sequential Test and Exception Test for planning applications.",
        "text": "Flood Zone 2 represents 1 in 1000 year chance of flooding; Flood Zone 3 represents 1 in 100 year chance of river flooding or 1 in 200 year sea flooding.",
        "themes": ["environment", "monitoring"],
        "phase": "live",
        "licence": "ogl3",
        "licence-text": "Environment Agency Open Data licence",
        "attribution": "environment-agency",
        "attribution-text": "© Environment Agency copyright and/or database right 2026",
        "entity-count": 89450,
        "source_url": "https://environment.data.gov.uk/dataset/flood-map-for-planning-rivers-and-sea-flood-zone-2",
        "documentation_url": "https://www.gov.uk/guidance/flood-risk-and-coastal-change",
        "wikidata": "",
    },
    {
        "dataset": "natural-england-protected-sites-and-bng",
        "name": "Natural England Statutory Protected Sites & BNG Register",
        "plural": "Natural England statutory site designations",
        "collection": "natural-england",
        "typology": "geography",
        "description": "Spatial designations of Sites of Special Scientific Interest (SSSI), Special Areas of Conservation (SAC), Special Protection Areas (SPA), Ramsar sites, and Biodiversity Net Gain (BNG) register allocations.",
        "text": "Essential statutory environmental constraints for Environmental Outcome Reports, Habitats Regulations Assessments, and 10% BNG mandatory planning compliance.",
        "themes": ["environment", "monitoring"],
        "phase": "live",
        "licence": "ogl3",
        "licence-text": "Natural England Open Data licence",
        "attribution": "natural-england",
        "attribution-text": "© Natural England copyright 2026",
        "entity-count": 14230,
        "source_url": "https://naturalengland-defra.opendata.arcgis.com/",
        "documentation_url": "https://www.gov.uk/guidance/understanding-biodiversity-net-gain",
        "wikidata": "",
    },
    {
        "dataset": "planning-inspectorate-appeals-data",
        "name": "Planning Inspectorate Appeals & NSIP Register",
        "plural": "Planning Inspectorate appeal cases",
        "collection": "planning-inspectorate",
        "typology": "document",
        "description": "National register of Section 78 planning appeals, enforcement appeals, local plan examination reports, and Nationally Significant Infrastructure Projects (NSIPs) handled by PINS.",
        "text": "Decisions, inspector reports, and appeal determinations establishing planning precedent and local plan soundness findings across England.",
        "themes": ["development", "administrative", "monitoring"],
        "phase": "live",
        "licence": "ogl3",
        "licence-text": "Licensed under the Open Government Licence v.3.0",
        "attribution": "crown-copyright",
        "attribution-text": "© Crown copyright The Planning Inspectorate",
        "entity-count": 28400,
        "source_url": "https://www.gov.uk/government/organisations/planning-inspectorate",
        "documentation_url": "https://acp.planninginspectorate.gov.uk/",
        "wikidata": "Q7757116",
    },
    {
        "dataset": "hm-land-registry-inspire-index-polygons",
        "name": "HM Land Registry INSPIRE Index Polygons",
        "plural": "HM Land Registry INSPIRE property boundary polygons",
        "collection": "land-registry",
        "typology": "geography",
        "description": "Cadastral parcel spatial boundaries corresponding to registered land titles in England and Wales under the EU INSPIRE Directive dataset.",
        "text": "Spatial boundaries linking land ownership titles to planning application red line boundaries and UPRNs.",
        "themes": ["development", "housing", "administrative"],
        "phase": "live",
        "licence": "ogl3",
        "licence-text": "HM Land Registry INSPIRE Licence",
        "attribution": "hm-land-registry",
        "attribution-text": "© HM Land Registry 2026",
        "entity-count": 28500000,
        "source_url": "https://use-land-property-data.service.gov.uk/datasets/inspire",
        "documentation_url": "https://www.gov.uk/guidance/inspire-index-polygons-spatial-data",
        "wikidata": "Q5635035",
    },
]


AUGMENTATION_AUTHORITIES: dict[str, dict[str, str]] = {
    "nppf-framework-policy": {
        "source_adapter": "gov-uk-mhclg",
        "source_publisher": "https://www.gov.uk/government/organisations/ministry-of-housing-communities-and-local-government",
        "publisher_id": "ministry-of-housing-communities-and-local-government",
        "publisher_name": "Ministry of Housing, Communities & Local Government",
    },
    "planning-practice-guidance": {
        "source_adapter": "gov-uk-mhclg",
        "source_publisher": "https://www.gov.uk/government/organisations/ministry-of-housing-communities-and-local-government",
        "publisher_id": "ministry-of-housing-communities-and-local-government",
        "publisher_name": "Ministry of Housing, Communities & Local Government",
    },
    "town-and-country-planning-act-1990": {
        "source_adapter": "legislation-gov-uk",
        "source_publisher": "https://www.legislation.gov.uk/",
        "publisher_id": "the-national-archives",
        "publisher_name": "The National Archives",
    },
    "levelling-up-and-regeneration-act-2023": {
        "source_adapter": "legislation-gov-uk",
        "source_publisher": "https://www.legislation.gov.uk/",
        "publisher_id": "the-national-archives",
        "publisher_name": "The National Archives",
    },
    "use-classes-order-1987": {
        "source_adapter": "legislation-gov-uk",
        "source_publisher": "https://www.legislation.gov.uk/",
        "publisher_id": "the-national-archives",
        "publisher_name": "The National Archives",
    },
    "historic-england-nhle-heritage": {
        "source_adapter": "historic-england",
        "source_publisher": "https://historicengland.org.uk/",
        "publisher_id": "historic-england",
        "publisher_name": "Historic England",
        "licence": "source-specific",
    },
    "environment-agency-flood-risk-zones": {
        "source_adapter": "environment-agency",
        "source_publisher": "https://www.gov.uk/government/organisations/environment-agency",
        "publisher_id": "environment-agency",
        "publisher_name": "Environment Agency",
        "licence": "source-specific",
    },
    "natural-england-protected-sites-and-bng": {
        "source_adapter": "natural-england",
        "source_publisher": "https://www.gov.uk/government/organisations/natural-england",
        "publisher_id": "natural-england",
        "publisher_name": "Natural England",
        "licence": "source-specific",
    },
    "planning-inspectorate-appeals-data": {
        "source_adapter": "planning-inspectorate",
        "source_publisher": "https://www.gov.uk/government/organisations/planning-inspectorate",
        "publisher_id": "planning-inspectorate",
        "publisher_name": "Planning Inspectorate",
    },
    "hm-land-registry-inspire-index-polygons": {
        "source_adapter": "hm-land-registry",
        "source_publisher": "https://www.gov.uk/government/organisations/land-registry",
        "publisher_id": "hm-land-registry",
        "publisher_name": "HM Land Registry",
        "licence": "source-specific",
    },
}


def fetch_json(url: str, timeout: int = 15) -> dict[str, Any] | list[Any]:
    """Fetch JSON from a URL with standard user agent header."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_live_planning_datasets(cache_dir: str | None = None) -> dict[str, Any]:
    """Fetch all dataset definitions, typologies, and collections from planning.data.gov.uk.
    
    Uses cached snapshot file if available.
    """
    if cache_dir and os.path.exists(os.path.join(cache_dir, "dataset.json")):
        logger.info("Loading cached planning datasets from %s", cache_dir)
        with open(os.path.join(cache_dir, "dataset.json"), encoding="utf-8") as f:
            return json.load(f)

    logger.info("Fetching live planning datasets from %s/dataset.json", PLANNING_DATA_GOV_UK_BASE)
    try:
        data = fetch_json(f"{PLANNING_DATA_GOV_UK_BASE}/dataset.json")
        if isinstance(data, dict):
            return data
    except Exception as exc:
        raise AcquisitionError(
            "Could not acquire planning.data.gov.uk dataset metadata; "
            "the existing snapshot was not changed"
        ) from exc

    raise AcquisitionError("planning.data.gov.uk returned an invalid dataset payload")


def load_live_planning_organisations(cache_dir: str | None = None) -> dict[str, Any]:
    """Fetch organisation records from planning.data.gov.uk."""
    if cache_dir and os.path.exists(os.path.join(cache_dir, "organisation.json")):
        logger.info("Loading cached organisation data from %s", cache_dir)
        with open(os.path.join(cache_dir, "organisation.json"), encoding="utf-8") as f:
            return json.load(f)

    logger.info("Fetching live organisations from %s/organisation.json", PLANNING_DATA_GOV_UK_BASE)
    try:
        data = fetch_json(f"{PLANNING_DATA_GOV_UK_BASE}/organisation.json")
        if isinstance(data, dict):
            return data
    except Exception as exc:
        raise AcquisitionError(
            "Could not acquire planning.data.gov.uk organisation metadata; "
            "the existing snapshot was not changed"
        ) from exc

    raise AcquisitionError("planning.data.gov.uk returned an invalid organisation payload")


def get_all_augmented_datasets(cache_dir: str | None = None) -> list[dict[str, Any]]:
    """Combine Planning Data records with curated policy and guidance records."""
    live_raw = load_live_planning_datasets(cache_dir)
    raw_datasets = live_raw.get("datasets", [])

    all_ds: list[dict[str, Any]] = []

    # Map raw planning.data.gov.uk datasets
    for ds in raw_datasets:
        item = dict(ds)
        item["source_adapter"] = "planning-data-gov-uk"
        item["source_publisher"] = "https://www.planning.data.gov.uk/"
        item["publisher_id"] = "planning-data-england"
        item["publisher_name"] = "Planning Data England / MHCLG"
        all_ds.append(item)

    # Add policy & legal instrument augmentations
    for aug in POLICY_AND_GUIDANCE_AUGMENTATIONS:
        aug_copy = dict(aug)
        aug_copy.update(AUGMENTATION_AUTHORITIES[aug_copy["dataset"]])
        aug_copy["confidence"] = "curated-unverified"
        all_ds.append(aug_copy)

    return all_ds
