from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import requests
import xml.etree.ElementTree as ET


app = FastAPI(title="BioGraph AI")

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


OPEN_TARGETS_URL = (
    "https://api.platform.opentargets.org/api/v4/graphql"
)

PUBMED_EFETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
)


# =========================================================
# OPEN TARGETS GRAPHQL
# =========================================================

def run_graphql(query, variables):

    response = requests.post(
        OPEN_TARGETS_URL,
        json={
            "query": query,
            "variables": variables
        },
        timeout=30
    )

    try:
        data = response.json()

    except Exception:
        raise Exception(
            f"Open Targets returned HTTP "
            f"{response.status_code}"
        )

    if data.get("errors"):

        messages = [
            error.get(
                "message",
                "Unknown GraphQL error"
            )
            for error in data["errors"]
        ]

        raise Exception(
            " | ".join(messages)
        )

    if response.status_code != 200:

        raise Exception(
            f"Open Targets returned HTTP "
            f"{response.status_code}"
        )

    return data


# =========================================================
# SEARCH DISEASE
# =========================================================

def search_disease(name):

    query = """
    query SearchDisease($queryString: String!) {

      search(
        queryString: $queryString,
        entityNames: ["disease"],
        page: {
          index: 0,
          size: 5
        }
      ) {

        hits {
          id
          name
          description
        }

      }

    }
    """

    data = run_graphql(
        query,
        {
            "queryString": name
        }
    )

    hits = (
        data
        .get("data", {})
        .get("search", {})
        .get("hits", [])
    )

    if not hits:
        return None

    return hits[0]


# =========================================================
# DISEASE DATA
# =========================================================

def get_disease_data(disease_id):

    query = """
    query DiseaseData($diseaseId: String!) {

      disease(efoId: $diseaseId) {

        id
        name
        description

        associatedTargets(
          page: {
            index: 0,
            size: 10
          }
        ) {

          rows {

            score

            target {
              id
              approvedSymbol
              approvedName
              biotype
              functionDescriptions
            }

          }

        }

        drugAndClinicalCandidates {

          count

          rows {

            id
            maxClinicalStage

            drug {
              id
              name
            }

            clinicalReports {
              id
            }

          }

        }

      }

    }
    """

    return run_graphql(
        query,
        {
            "diseaseId": disease_id
        }
    )


# =========================================================
# TARGET DRUGS
# =========================================================

def get_target_drugs(target_id):

    query = """
    query TargetDrugs($targetId: String!) {

      target(ensemblId: $targetId) {

        id
        approvedSymbol

        drugAndClinicalCandidates {

          count

          rows {

            id
            maxClinicalStage

            drug {
              id
              name
            }

            clinicalReports {
              id
            }

          }

        }

      }

    }
    """

    data = run_graphql(
        query,
        {
            "targetId": target_id
        }
    )

    return (
        data
        .get("data", {})
        .get("target")
    )


# =========================================================
# GENERAL PUBLICATIONS
# =========================================================

def get_publications(entity_type, entity_id):

    if entity_type == "protein":

        query = """
        query Publications($id: String!) {

          target(ensemblId: $id) {

            literatureOcurrences {

              count
              filteredCount

              rows {
                pmid
                pmcid
                publicationDate
              }

            }

          }

        }
        """

        root_name = "target"

    elif entity_type == "drug":

        query = """
        query Publications($id: String!) {

          drug(chemblId: $id) {

            literatureOcurrences {

              count
              filteredCount

              rows {
                pmid
                pmcid
                publicationDate
              }

            }

          }

        }
        """

        root_name = "drug"

    elif entity_type == "disease":

        query = """
        query Publications($id: String!) {

          disease(efoId: $id) {

            literatureOcurrences {

              count
              filteredCount

              rows {
                pmid
                pmcid
                publicationDate
              }

            }

          }

        }
        """

        root_name = "disease"

    else:

        return {
            "count": 0,
            "papers": []
        }

    data = run_graphql(
        query,
        {
            "id": entity_id
        }
    )

    entity = (
        data
        .get("data", {})
        .get(root_name)
    )

    if not entity:

        return {
            "count": 0,
            "papers": []
        }

    literature = (
        entity.get(
            "literatureOcurrences"
        )
        or {}
    )

    rows = (
        literature.get("rows")
        or []
    )

    papers = []

    for paper in rows[:8]:

        pmid = paper.get("pmid")

        if not pmid:
            continue

        papers.append({

            "pmid":
                str(pmid),

            "pmcid":
                paper.get("pmcid"),

            "date":
                paper.get(
                    "publicationDate"
                ),

            "url":
                f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        })

    count = (
        literature.get("filteredCount")
        or
        literature.get("count")
        or
        len(papers)
    )

    return {
        "count": count,
        "papers": papers
    }


# =========================================================
# DRUG + DISEASE PUBLICATIONS
# =========================================================

def get_drug_disease_publications(
    drug_id,
    disease_id
):

    query = """
    query DrugDiseaseLiterature(
      $drugId: String!,
      $ids: [String!]
    ) {

      drug(chemblId: $drugId) {

        literatureOcurrences(
          additionalIds: $ids
        ) {

          count
          filteredCount

          rows {
            pmid
            pmcid
            publicationDate
          }

        }

      }

    }
    """

    data = run_graphql(
        query,
        {
            "drugId": drug_id,
            "ids": [disease_id]
        }
    )

    drug = (
        data
        .get("data", {})
        .get("drug")
    )

    if not drug:

        return {
            "count": 0,
            "papers": []
        }

    literature = (
        drug.get(
            "literatureOcurrences"
        )
        or {}
    )

    rows = (
        literature.get("rows")
        or []
    )

    papers = []

    for row in rows[:10]:

        pmid = row.get("pmid")

        if not pmid:
            continue

        papers.append({

            "pmid":
                str(pmid),

            "date":
                row.get(
                    "publicationDate"
                ),

            "url":
                f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        })

    count = (
        literature.get(
            "filteredCount"
        )
        or 0
    )

    return {
        "count": count,
        "papers": papers
    }


# =========================================================
# FETCH PUBMED ABSTRACTS
# =========================================================

def fetch_pubmed_details(pmids):

    if not pmids:
        return []

    pmids = [
        str(pmid)
        for pmid in pmids[:10]
    ]

    try:

        response = requests.get(
            PUBMED_EFETCH_URL,
            params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml"
            },
            headers={
                "User-Agent":
                    "BioGraphAI-ResearchProject/1.0"
            },
            timeout=20
        )

        response.raise_for_status()

        root = ET.fromstring(
            response.content
        )

    except Exception:

        return []

    papers = []

    for article in root.findall(
        ".//PubmedArticle"
    ):

        pmid_element = article.find(
            ".//PMID"
        )

        pmid = (
            pmid_element.text
            if pmid_element is not None
            else ""
        )

        title_element = article.find(
            ".//ArticleTitle"
        )

        title = ""

        if title_element is not None:

            title = "".join(
                title_element.itertext()
            ).strip()

        abstract_parts = []

        for abstract_element in article.findall(
            ".//Abstract/AbstractText"
        ):

            part = "".join(
                abstract_element.itertext()
            ).strip()

            if part:
                abstract_parts.append(part)

        abstract = " ".join(
            abstract_parts
        )

        papers.append({

            "pmid":
                pmid,

            "title":
                title,

            "abstract":
                abstract,

            "url":
                f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        })

    return papers


# =========================================================
# PAPER SIGNAL CLASSIFICATION
# =========================================================

SUPPORT_TERMS = [

    "effective",
    "efficacy",
    "improved",
    "improvement",
    "benefit",
    "beneficial",
    "response",
    "reduced",
    "reduction",
    "inhibited",
    "inhibition",
    "promising",
    "therapeutic benefit",
    "significant improvement",
    "survival benefit",
    "positive response"

]


NEGATIVE_TERMS = [

    "no significant benefit",
    "no significant improvement",
    "did not improve",
    "did not reduce",
    "failed to improve",
    "failed to show",
    "ineffective",
    "no difference",
    "not effective",
    "lack of efficacy",
    "no benefit",
    "worsened",
    "worsening",
    "negative result"

]


def classify_paper_signal(
    title,
    abstract
):

    text = (
        f"{title} {abstract}"
    ).lower()

    negative_hits = [
        term
        for term in NEGATIVE_TERMS
        if term in text
    ]

    support_hits = [
        term
        for term in SUPPORT_TERMS
        if term in text
    ]

    # Negative language gets priority because
    # "no significant improvement" also
    # contains the word "improvement".

    if negative_hits:

        return {
            "classification":
                "uncertain_negative",

            "matched_terms":
                negative_hits[:3]
        }

    if support_hits:

        return {
            "classification":
                "supportive",

            "matched_terms":
                support_hits[:3]
        }

    return {
        "classification":
            "unclear",

        "matched_terms":
            []
    }


# =========================================================
# CLINICAL STAGE SCORE
# =========================================================

def clinical_stage_points(stage):

    if stage is None:
        return 0

    text = str(stage).upper()

    if "4" in text:
        return 30

    if "3" in text:
        return 26

    if "2" in text:
        return 20

    if "1" in text:
        return 10

    return 5


# =========================================================
# EVIDENCE SCORE
# =========================================================

def calculate_evidence_score(
    clinical_stage,
    relation_publication_count,
    clinical_reports,
    association_score,
    supportive_count,
    negative_count
):

    score = 0
    reasons = []

    # -----------------------------------------------------
    # Clinical stage
    # -----------------------------------------------------

    stage_score = clinical_stage_points(
        clinical_stage
    )

    score += stage_score

    if stage_score:

        reasons.append(
            f"+{stage_score} clinical development"
        )

    # -----------------------------------------------------
    # Drug + disease literature
    # -----------------------------------------------------

    if relation_publication_count >= 30:
        literature_score = 25

    elif relation_publication_count >= 15:
        literature_score = 20

    elif relation_publication_count >= 7:
        literature_score = 15

    elif relation_publication_count >= 3:
        literature_score = 10

    elif relation_publication_count >= 1:
        literature_score = 5

    else:
        literature_score = 0

    score += literature_score

    if literature_score:

        reasons.append(
            f"+{literature_score} drug–disease literature"
        )

    # -----------------------------------------------------
    # Clinical reports
    # -----------------------------------------------------

    if clinical_reports >= 10:
        report_score = 20

    elif clinical_reports >= 5:
        report_score = 15

    elif clinical_reports >= 2:
        report_score = 10

    elif clinical_reports >= 1:
        report_score = 5

    else:
        report_score = 0

    score += report_score

    if report_score:

        reasons.append(
            f"+{report_score} clinical reports"
        )

    # -----------------------------------------------------
    # Target-disease association
    # -----------------------------------------------------

    association_score = (
        association_score
        if association_score is not None
        else 0
    )

    target_score = round(
        min(
            20,
            max(
                0,
                association_score * 20
            )
        )
    )

    score += target_score

    if target_score:

        reasons.append(
            f"+{target_score} target–disease association"
        )

    # -----------------------------------------------------
    # Abstract signals
    # -----------------------------------------------------

    supportive_bonus = min(
        10,
        supportive_count * 2
    )

    score += supportive_bonus

    if supportive_bonus:

        reasons.append(
            f"+{supportive_bonus} supportive abstract signals"
        )

    negative_penalty = min(
        20,
        negative_count * 5
    )

    score -= negative_penalty

    if negative_penalty:

        reasons.append(
            f"-{negative_penalty} uncertain/negative signals"
        )

    score = max(
        0,
        min(
            100,
            round(score)
        )
    )

    if score >= 75:

        strength = "Strong"

    elif score >= 50:

        strength = "Moderate"

    elif score >= 25:

        strength = "Limited"

    else:

        strength = "Weak"

    return {
        "score": score,
        "strength": strength,
        "reasons": reasons
    }


# =========================================================
# EXPLANATION ENGINE
# =========================================================

def build_evidence_explanation(
    drug_name,
    disease_name,
    target_symbol,
    score,
    strength,
    clinical_stage,
    relation_publication_count,
    supportive_count,
    negative_count,
    unclear_count
):

    parts = []

    parts.append(
        f"{drug_name} has a {strength.lower()} "
        f"evidence profile for its connection "
        f"with {disease_name} in this model "
        f"(score {score}/100)."
    )

    if target_symbol:

        parts.append(
            f"The graph links the drug through "
            f"the biological target "
            f"{target_symbol}."
        )

    if clinical_stage:

        parts.append(
            f"Open Targets reports a maximum "
            f"clinical stage of "
            f"{clinical_stage}."
        )

    if relation_publication_count > 0:

        parts.append(
            f"Open Targets identified "
            f"{relation_publication_count} "
            f"publication mentions containing "
            f"both the drug and disease entities."
        )

    else:

        parts.append(
            "No drug–disease co-mentioning "
            "publications were returned by the "
            "literature query."
        )

    if supportive_count > 0:

        parts.append(
            f"{supportive_count} of the analyzed "
            f"abstracts contained language that "
            f"the heuristic classified as "
            f"supportive."
        )

    if negative_count > 0:

        parts.append(
            f"{negative_count} abstracts contained "
            f"language suggesting an uncertain "
            f"or negative result."
        )

    if unclear_count > 0:

        parts.append(
            f"{unclear_count} abstracts were "
            f"left unclassified because the "
            f"text did not contain a clear signal."
        )

    parts.append(
        "These classifications are research "
        "signals, not conclusions: keyword "
        "matching cannot determine whether a "
        "drug is safe or effective."
    )

    return " ".join(parts)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return FileResponse(
        "app/static/index.html"
    )


# =========================================================
# GRAPH ENDPOINT
# =========================================================

@app.get("/api/graph")
def graph(
    disease: str = Query(
        default="Parkinson's disease"
    )
):

    try:

        search_result = search_disease(
            disease
        )

        if not search_result:

            return {
                "error":
                    "Disease could not be found.",
                "nodes": [],
                "edges": []
            }

        disease_id = (
            search_result["id"]
        )

        raw = get_disease_data(
            disease_id
        )

        disease_data = (
            raw
            .get("data", {})
            .get("disease")
        )

        if not disease_data:

            return {
                "error":
                    "No disease data returned.",
                "nodes": [],
                "edges": []
            }

        disease_name = (
            disease_data.get("name")
            or disease
        )

        nodes = []
        edges = []

        # -------------------------------------------------
        # Disease node
        # -------------------------------------------------

        nodes.append({

            "id":
                "disease",

            "entity_id":
                disease_id,

            "label":
                disease_name,

            "type":
                "disease",

            "full_name":
                disease_name,

            "description":
                disease_data.get(
                    "description"
                )
                or
                "No description available.",

            "why":
                "This is the disease "
                "selected for analysis.",

            "source_url":
                "https://platform.opentargets.org/"
                f"disease/{disease_id}"

        })

        # -------------------------------------------------
        # Disease drugs
        # -------------------------------------------------

        disease_drugs = {}

        clinical_rows = (
            disease_data
            .get(
                "drugAndClinicalCandidates",
                {}
            )
            .get("rows", [])
        )

        for row in clinical_rows:

            drug = row.get("drug")

            if not drug:
                continue

            drug_id = drug.get("id")

            if not drug_id:
                continue

            disease_drugs[drug_id] = {

                "name":
                    drug.get("name"),

                "stage":
                    row.get(
                        "maxClinicalStage"
                    ),

                "clinical_reports":
                    len(
                        row.get(
                            "clinicalReports"
                        )
                        or []
                    )

            }

        # -------------------------------------------------
        # Targets
        # -------------------------------------------------

        associations = (
            disease_data
            .get(
                "associatedTargets",
                {}
            )
            .get("rows", [])
        )

        target_ids = []
        target_scores = {}

        for association in associations:

            target = association.get(
                "target"
            )

            if not target:
                continue

            target_id = target.get("id")

            if not target_id:
                continue

            symbol = (
                target.get(
                    "approvedSymbol"
                )
                or target_id
            )

            full_name = (
                target.get(
                    "approvedName"
                )
                or symbol
            )

            score = (
                association.get("score")
                or 0
            )

            target_scores[
                target_id
            ] = score

            functions = (
                target.get(
                    "functionDescriptions"
                )
                or []
            )

            description = (
                functions[0]
                if functions
                else
                "No function description available."
            )

            nodes.append({

                "id":
                    target_id,

                "entity_id":
                    target_id,

                "label":
                    symbol,

                "type":
                    "protein",

                "full_name":
                    full_name,

                "biotype":
                    target.get(
                        "biotype"
                    )
                    or "Unknown",

                "description":
                    description,

                "score":
                    round(
                        score,
                        3
                    ),

                "why":
                    f"Open Targets reports "
                    f"evidence connecting "
                    f"{symbol} with "
                    f"{disease_name}.",

                "source_url":
                    "https://platform.opentargets.org/"
                    f"target/{target_id}"

            })

            edges.append({

                "source":
                    "disease",

                "target":
                    target_id,

                "label":
                    f"{round(score, 2)}"

            })

            target_ids.append(
                target_id
            )

        # -------------------------------------------------
        # Drugs
        # -------------------------------------------------

        created_drugs = set()

        for target_id in target_ids:

            target_data = get_target_drugs(
                target_id
            )

            if not target_data:
                continue

            target_symbol = (
                target_data.get(
                    "approvedSymbol"
                )
                or target_id
            )

            target_candidates = (
                target_data
                .get(
                    "drugAndClinicalCandidates",
                    {}
                )
                .get("rows", [])
            )

            added_for_target = 0

            for candidate in target_candidates:

                if added_for_target >= 3:
                    break

                drug = candidate.get(
                    "drug"
                )

                if not drug:
                    continue

                drug_id = drug.get("id")

                if not drug_id:
                    continue

                if drug_id not in disease_drugs:
                    continue

                disease_drug = (
                    disease_drugs[
                        drug_id
                    ]
                )

                drug_name = (
                    drug.get("name")
                    or
                    disease_drug.get("name")
                    or
                    drug_id
                )

                node_id = (
                    f"drug_{drug_id}"
                )

                if node_id not in created_drugs:

                    nodes.append({

                        "id":
                            node_id,

                        "entity_id":
                            drug_id,

                        "label":
                            drug_name,

                        "type":
                            "drug",

                        "full_name":
                            drug_name,

                        "disease_id":
                            disease_id,

                        "disease_name":
                            disease_name,

                        "target_id":
                            target_id,

                        "target_symbol":
                            target_symbol,

                        "association_score":
                            round(
                                target_scores.get(
                                    target_id,
                                    0
                                ),
                                3
                            ),

                        "biotype":
                            "Drug / clinical candidate",

                        "clinical_stage":
                            disease_drug.get(
                                "stage"
                            ),

                        "clinical_reports":
                            disease_drug.get(
                                "clinical_reports",
                                0
                            ),

                        "description":
                            "A drug or clinical "
                            "candidate reported in "
                            "Open Targets clinical data.",

                        "why":
                            f"{drug_name} appears in "
                            f"clinical information for "
                            f"{disease_name} and is "
                            f"connected with target "
                            f"{target_symbol}.",

                        "source_url":
                            "https://platform.opentargets.org/"
                            f"drug/{drug_id}"

                    })

                    created_drugs.add(
                        node_id
                    )

                edges.append({

                    "source":
                        target_id,

                    "target":
                        node_id,

                    "label":
                        "drug-target"

                })

                added_for_target += 1

        return {

            "display_name":
                disease_name,

            "disease_id":
                disease_id,

            "nodes":
                nodes,

            "edges":
                edges,

            "stats": {

                "targets":
                    len(target_ids),

                "drugs":
                    len(created_drugs),

                "clinical_candidates":
                    len(disease_drugs)

            }

        }

    except Exception as error:

        return {
            "error": str(error),
            "nodes": [],
            "edges": []
        }


# =========================================================
# PAPERS ENDPOINT
# =========================================================

@app.get("/api/papers")
def papers(
    entity_type: str,
    entity_id: str
):

    try:

        return get_publications(
            entity_type,
            entity_id
        )

    except Exception as error:

        return {
            "error":
                str(error),

            "count":
                0,

            "papers":
                []
        }


# =========================================================
# V7 EVIDENCE ANALYSIS
# =========================================================

@app.get("/api/evidence-analysis")
def evidence_analysis(
    drug_id: str,
    disease_id: str,
    drug_name: str = "",
    disease_name: str = "",
    target_symbol: str = "",
    clinical_stage: str = "",
    clinical_reports: int = 0,
    association_score: float = 0
):

    try:

        # -------------------------------------------------
        # Get papers containing drug + disease
        # -------------------------------------------------

        literature = (
            get_drug_disease_publications(
                drug_id,
                disease_id
            )
        )

        relation_count = (
            literature.get(
                "count",
                0
            )
        )

        paper_rows = (
            literature.get(
                "papers",
                []
            )
        )

        pmids = [
            paper["pmid"]
            for paper in paper_rows
            if paper.get("pmid")
        ]

        # -------------------------------------------------
        # Fetch titles + abstracts from PubMed
        # -------------------------------------------------

        details = (
            fetch_pubmed_details(
                pmids
            )
        )

        supportive = []
        uncertain_negative = []
        unclear = []

        # -------------------------------------------------
        # Classify papers
        # -------------------------------------------------

        for paper in details:

            signal = (
                classify_paper_signal(
                    paper.get(
                        "title",
                        ""
                    ),
                    paper.get(
                        "abstract",
                        ""
                    )
                )
            )

            item = {

                "pmid":
                    paper.get("pmid"),

                "title":
                    paper.get("title")
                    or
                    "Untitled publication",

                "url":
                    paper.get("url"),

                "matched_terms":
                    signal.get(
                        "matched_terms",
                        []
                    )

            }

            classification = (
                signal[
                    "classification"
                ]
            )

            if classification == "supportive":

                supportive.append(
                    item
                )

            elif classification == "uncertain_negative":

                uncertain_negative.append(
                    item
                )

            else:

                unclear.append(
                    item
                )

        # -------------------------------------------------
        # Score
        # -------------------------------------------------

        score_result = (
            calculate_evidence_score(

                clinical_stage=
                    clinical_stage,

                relation_publication_count=
                    relation_count,

                clinical_reports=
                    clinical_reports,

                association_score=
                    association_score,

                supportive_count=
                    len(supportive),

                negative_count=
                    len(
                        uncertain_negative
                    )

            )
        )

        # -------------------------------------------------
        # Explanation
        # -------------------------------------------------

        explanation = (
            build_evidence_explanation(

                drug_name=
                    drug_name
                    or drug_id,

                disease_name=
                    disease_name
                    or disease_id,

                target_symbol=
                    target_symbol,

                score=
                    score_result[
                        "score"
                    ],

                strength=
                    score_result[
                        "strength"
                    ],

                clinical_stage=
                    clinical_stage,

                relation_publication_count=
                    relation_count,

                supportive_count=
                    len(supportive),

                negative_count=
                    len(
                        uncertain_negative
                    ),

                unclear_count=
                    len(unclear)

            )
        )

        return {

            "score":
                score_result["score"],

            "strength":
                score_result["strength"],

            "reasons":
                score_result["reasons"],

            "explanation":
                explanation,

            "relation_publication_count":
                relation_count,

            "abstracts_analyzed":
                len(details),

            "supportive_count":
                len(supportive),

            "negative_count":
                len(
                    uncertain_negative
                ),

            "unclear_count":
                len(unclear),

            "supportive":
                supportive[:5],

            "uncertain_negative":
                uncertain_negative[:5],

            "unclear":
                unclear[:5],

            "method_note":
                "Support and uncertainty labels are "
                "generated with a transparent keyword "
                "heuristic over PubMed titles and "
                "abstracts. They are research signals, "
                "not medical conclusions."

        }

    except Exception as error:

        return {

            "error":
                str(error),

            "score":
                0,

            "strength":
                "Unknown",

            "supportive":
                [],

            "uncertain_negative":
                [],

            "unclear":
                []

        }