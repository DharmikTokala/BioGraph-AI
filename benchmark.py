import csv
import math
import os
from statistics import mean

from app.main import (
    search_disease,
    run_graphql,
    get_drug_disease_publications,
    fetch_pubmed_details,
    classify_paper_signal,
)


# =========================================================
# BIOGRAPH AI — FINAL BENCHMARK
# =========================================================
#
# This script REUSES benchmark_v81_results.csv.
#
# It DOES NOT rerun all 100 pairs.
#
# It only replaces controls that have:
#   - clinical evidence
#   - clinical reports
#   - biological target overlap
#
# =========================================================


OLD_RESULTS_FILE = "benchmark_v81_results.csv"
FINAL_RESULTS_FILE = "benchmark_final_results.csv"


# =========================================================
# REPLACEMENT DISEASE POOL
# =========================================================

CONTROL_DISEASE_POOL = [

    "multiple sclerosis",
    "amyotrophic lateral sclerosis",
    "ulcerative colitis",
    "endometriosis",
    "osteoporosis",
    "glaucoma",
    "cataract",
    "chronic kidney disease",

    "pancreatic cancer",
    "prostate cancer",
    "hepatocellular carcinoma",
    "glioblastoma",

    "tuberculosis",
    "influenza",

    "systemic lupus erythematosus",
    "celiac disease",
    "osteoarthritis",

    "autism spectrum disorder",
    "Huntington disease",

    "multiple myeloma",
    "acute myeloid leukemia",

    "endometrial cancer",
    "bladder cancer",

    "chronic obstructive pulmonary disease",

    "myasthenia gravis",
    "sarcoidosis",

    "polycystic ovary syndrome",

    "kidney stone disease",

    "narcolepsy",
    "restless legs syndrome",

]


# =========================================================
# CACHES
# =========================================================

drug_cache = {}
disease_cache = {}

drug_targets_cache = {}
disease_targets_cache = {}

clinical_cache = {}
literature_cache = {}


# =========================================================
# HELPERS
# =========================================================

def safe_int(value):

    try:

        if value in (
            None,
            ""
        ):
            return 0

        return int(
            float(value)
        )

    except Exception:

        return 0


def safe_float(value):

    try:

        if value in (
            None,
            ""
        ):
            return 0.0

        return float(value)

    except Exception:

        return 0.0


# =========================================================
# LOAD OLD RESULTS
# =========================================================

def load_old_results():

    if not os.path.exists(
        OLD_RESULTS_FILE
    ):

        raise Exception(
            f"{OLD_RESULTS_FILE} was not found.\n"
            "Make sure it is in the main biograph_v1 folder."
        )

    rows = []

    with open(
        OLD_RESULTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            row["label"] = safe_int(
                row.get("label")
            )

            row[
                "prediction_score"
            ] = safe_int(
                row.get(
                    "prediction_score"
                )
            )

            row[
                "full_score"
            ] = safe_int(
                row.get(
                    "full_score"
                )
            )

            row[
                "target_overlap_count"
            ] = safe_int(
                row.get(
                    "target_overlap_count"
                )
            )

            row[
                "max_target_association"
            ] = safe_float(
                row.get(
                    "max_target_association"
                )
            )

            row[
                "publication_count"
            ] = safe_int(
                row.get(
                    "publication_count"
                )
            )

            row[
                "abstracts_analyzed"
            ] = safe_int(
                row.get(
                    "abstracts_analyzed"
                )
            )

            row[
                "supportive_count"
            ] = safe_int(
                row.get(
                    "supportive_count"
                )
            )

            row[
                "negative_count"
            ] = safe_int(
                row.get(
                    "negative_count"
                )
            )

            row[
                "unclear_count"
            ] = safe_int(
                row.get(
                    "unclear_count"
                )
            )

            row[
                "clinical_reports"
            ] = safe_int(
                row.get(
                    "clinical_reports"
                )
            )

            rows.append(row)

    return rows


# =========================================================
# SEARCH DRUG
# =========================================================

def search_drug(name):

    if name in drug_cache:

        return drug_cache[name]

    query = """
    query SearchDrug($queryString: String!) {

      search(
        queryString: $queryString,
        entityNames: ["drug"],
        page: {
          index: 0,
          size: 5
        }
      ) {

        hits {
          id
          name
        }

      }

    }
    """

    data = run_graphql(
        query,
        {
            "queryString":
                name
        }
    )

    hits = (
        data
        .get("data", {})
        .get("search", {})
        .get("hits", [])
    )

    result = (
        hits[0]
        if hits
        else None
    )

    drug_cache[name] = result

    return result


# =========================================================
# SEARCH DISEASE
# =========================================================

def cached_search_disease(
    name
):

    if name in disease_cache:

        return disease_cache[
            name
        ]

    result = search_disease(
        name
    )

    disease_cache[
        name
    ] = result

    return result


# =========================================================
# DRUG TARGETS
# =========================================================

def get_drug_targets(
    drug_id
):

    if drug_id in drug_targets_cache:

        return drug_targets_cache[
            drug_id
        ]

    query = """
    query DrugTargets($drugId: String!) {

      drug(chemblId: $drugId) {

        mechanismsOfAction {

          rows {

            targets {
              id
              approvedSymbol
            }

          }

        }

      }

    }
    """

    data = run_graphql(
        query,
        {
            "drugId":
                drug_id
        }
    )

    drug = (
        data
        .get("data", {})
        .get("drug")
    )

    targets = {}

    if drug:

        rows = (
            drug
            .get(
                "mechanismsOfAction",
                {}
            )
            .get("rows", [])
        )

        for row in rows:

            for target in (
                row.get("targets")
                or []
            ):

                target_id = (
                    target.get("id")
                )

                if not target_id:
                    continue

                targets[
                    target_id
                ] = (
                    target.get(
                        "approvedSymbol"
                    )
                    or target_id
                )

    drug_targets_cache[
        drug_id
    ] = targets

    return targets


# =========================================================
# DISEASE TARGETS
# =========================================================

def get_disease_targets(
    disease_id
):

    if disease_id in disease_targets_cache:

        return disease_targets_cache[
            disease_id
        ]

    query = """
    query DiseaseTargets($diseaseId: String!) {

      disease(efoId: $diseaseId) {

        associatedTargets(
          page: {
            index: 0,
            size: 200
          }
        ) {

          rows {

            score

            target {
              id
              approvedSymbol
            }

          }

        }

      }

    }
    """

    data = run_graphql(
        query,
        {
            "diseaseId":
                disease_id
        }
    )

    disease = (
        data
        .get("data", {})
        .get("disease")
    )

    targets = {}

    if disease:

        rows = (
            disease
            .get(
                "associatedTargets",
                {}
            )
            .get("rows", [])
        )

        for row in rows:

            target = row.get(
                "target"
            )

            if not target:
                continue

            target_id = (
                target.get("id")
            )

            if not target_id:
                continue

            targets[
                target_id
            ] = {

                "symbol":
                    target.get(
                        "approvedSymbol"
                    )
                    or target_id,

                "score":
                    row.get("score")
                    or 0

            }

    disease_targets_cache[
        disease_id
    ] = targets

    return targets


# =========================================================
# TARGET OVERLAP
# =========================================================

def calculate_target_overlap(
    drug_id,
    disease_id
):

    drug_targets = (
        get_drug_targets(
            drug_id
        )
    )

    disease_targets = (
        get_disease_targets(
            disease_id
        )
    )

    overlaps = []

    for (
        target_id,
        symbol
    ) in drug_targets.items():

        if (
            target_id
            not in
            disease_targets
        ):

            continue

        overlaps.append({

            "id":
                target_id,

            "symbol":
                symbol,

            "association_score":
                disease_targets[
                    target_id
                ]["score"]

        })

    overlaps.sort(

        key=lambda item:
            item[
                "association_score"
            ],

        reverse=True

    )

    if overlaps:

        maximum = overlaps[0][
            "association_score"
        ]

    else:

        maximum = 0

    return {

        "count":
            len(overlaps),

        "max_score":
            maximum,

        "targets":
            overlaps

    }


# =========================================================
# CLINICAL DATA
# =========================================================

def get_pair_clinical_data(
    disease_id,
    drug_id
):

    key = (
        disease_id,
        drug_id
    )

    if key in clinical_cache:

        return clinical_cache[
            key
        ]

    query = """
    query PairClinicalData($diseaseId: String!) {

      disease(efoId: $diseaseId) {

        drugAndClinicalCandidates {

          rows {

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
            "diseaseId":
                disease_id
        }
    )

    disease = (
        data
        .get("data", {})
        .get("disease")
    )

    result = {

        "clinical_stage":
            "",

        "clinical_reports":
            0

    }

    if disease:

        rows = (
            disease
            .get(
                "drugAndClinicalCandidates",
                {}
            )
            .get("rows", [])
        )

        for row in rows:

            drug = row.get(
                "drug"
            )

            if not drug:
                continue

            if (
                drug.get("id")
                ==
                drug_id
            ):

                result = {

                    "clinical_stage":
                        row.get(
                            "maxClinicalStage"
                        )
                        or "",

                    "clinical_reports":
                        len(
                            row.get(
                                "clinicalReports"
                            )
                            or []
                        )

                }

                break

    clinical_cache[
        key
    ] = result

    return result


# =========================================================
# SCORE FUNCTIONS
# =========================================================

def stage_points(stage):

    if not stage:
        return 0

    text = str(
        stage
    ).upper()

    if "APPROVAL" in text:
        return 20

    if "4" in text:
        return 20

    if "3" in text:
        return 17

    if "2" in text:
        return 12

    if "1" in text:
        return 6

    return 3


def report_points(count):

    if count >= 50:
        return 15

    if count >= 20:
        return 12

    if count >= 10:
        return 9

    if count >= 5:
        return 6

    if count >= 1:
        return 3

    return 0


def literature_points(count):

    if count <= 0:
        return 0

    result = round(
        math.log10(
            count + 1
        )
        * 2
    )

    return min(
        10,
        result
    )


def biological_points(
    count,
    max_score
):

    if count <= 0:
        return 0

    primary = (
        max_score
        * 45
    )

    extra = min(
        15,
        max(
            0,
            count - 1
        )
        * 3
    )

    return min(
        60,
        round(
            primary
            +
            extra
        )
    )


def abstract_points(
    supportive,
    negative
):

    positive = min(
        20,
        supportive
        * 4
    )

    penalty = min(
        20,
        negative
        * 5
    )

    return (
        positive
        -
        penalty
    )


def prediction_score(
    publications,
    overlap_count,
    max_target_score,
    supportive,
    negative
):

    score = 0

    score += literature_points(
        publications
    )

    score += biological_points(
        overlap_count,
        max_target_score
    )

    score += abstract_points(
        supportive,
        negative
    )

    return max(
        0,
        min(
            100,
            round(score)
        )
    )


def full_score(
    prediction,
    stage,
    reports
):

    score = prediction

    score += stage_points(
        stage
    )

    score += report_points(
        reports
    )

    return max(
        0,
        min(
            100,
            round(score)
        )
    )


def score_strength(score):

    if score >= 75:
        return "Strong"

    if score >= 50:
        return "Moderate"

    if score >= 25:
        return "Limited"

    return "Weak"


# =========================================================
# IS OLD CONTROL VALID?
# =========================================================

def old_control_is_valid(
    row
):

    clinical_stage = (
        row.get(
            "clinical_stage"
        )
        or ""
    ).strip()

    clinical_reports = (
        safe_int(
            row.get(
                "clinical_reports"
            )
        )
    )

    overlap_count = (
        safe_int(
            row.get(
                "target_overlap_count"
            )
        )
    )

    if clinical_stage:
        return False

    if clinical_reports > 0:
        return False

    if overlap_count > 0:
        return False

    return True


# =========================================================
# SCREEN NEW CONTROL
# =========================================================

def candidate_is_valid(
    drug_name,
    known_disease,
    candidate_disease
):

    if (
        candidate_disease
        ==
        known_disease
    ):
        return False

    drug = search_drug(
        drug_name
    )

    disease = (
        cached_search_disease(
            candidate_disease
        )
    )

    if not drug or not disease:

        return False

    clinical = (
        get_pair_clinical_data(

            disease["id"],
            drug["id"]

        )
    )

    if clinical[
        "clinical_stage"
    ]:

        return False

    if (
        clinical[
            "clinical_reports"
        ] > 0
    ):

        return False

    overlap = (
        calculate_target_overlap(

            drug["id"],
            disease["id"]

        )
    )

    if (
        overlap["count"] > 0
    ):

        return False

    return True


# =========================================================
# ANALYZE ONLY A NEW REPLACEMENT CONTROL
# =========================================================

def analyze_new_control(
    drug_name,
    disease_name
):

    print(
        f"Analyzing new control: "
        f"{drug_name} -> "
        f"{disease_name}"
    )

    drug = search_drug(
        drug_name
    )

    disease = (
        cached_search_disease(
            disease_name
        )
    )

    drug_id = drug["id"]
    disease_id = disease["id"]

    overlap = (
        calculate_target_overlap(
            drug_id,
            disease_id
        )
    )

    clinical = (
        get_pair_clinical_data(
            disease_id,
            drug_id
        )
    )

    literature = (
        get_drug_disease_publications(
            drug_id,
            disease_id
        )
    )

    publication_count = (
        literature.get(
            "count",
            0
        )
        or 0
    )

    paper_rows = (
        literature.get(
            "papers",
            []
        )
        or []
    )

    pmids = [

        paper["pmid"]

        for paper in paper_rows

        if paper.get("pmid")

    ]

    details = (
        fetch_pubmed_details(
            pmids
        )
    )

    supportive = 0
    negative = 0
    unclear = 0

    for paper in details:

        classification = (
            classify_paper_signal(

                paper.get(
                    "title",
                    ""
                ),

                paper.get(
                    "abstract",
                    ""
                )

            )[
                "classification"
            ]
        )

        if (
            classification
            ==
            "supportive"
        ):

            supportive += 1

        elif (
            classification
            ==
            "uncertain_negative"
        ):

            negative += 1

        else:

            unclear += 1


    pred_score = prediction_score(

        publications=
            publication_count,

        overlap_count=
            overlap["count"],

        max_target_score=
            overlap["max_score"],

        supportive=
            supportive,

        negative=
            negative

    )


    final_score = full_score(

        prediction=
            pred_score,

        stage=
            clinical[
                "clinical_stage"
            ],

        reports=
            clinical[
                "clinical_reports"
            ]

    )


    targets = "; ".join(

        item["symbol"]

        for item in overlap[
            "targets"
        ][:5]

    )


    return {

        "drug":
            drug_name,

        "disease":
            disease_name,

        "label":
            0,

        "group":
            "screened_control",

        "prediction_score":
            pred_score,

        "prediction_strength":
            score_strength(
                pred_score
            ),

        "full_score":
            final_score,

        "full_strength":
            score_strength(
                final_score
            ),

        "target_overlap_count":
            overlap["count"],

        "max_target_association":
            round(
                overlap[
                    "max_score"
                ],
                4
            ),

        "overlapping_targets":
            targets,

        "publication_count":
            publication_count,

        "abstracts_analyzed":
            len(details),

        "supportive_count":
            supportive,

        "negative_count":
            negative,

        "unclear_count":
            unclear,

        "clinical_stage":
            clinical[
                "clinical_stage"
            ],

        "clinical_reports":
            clinical[
                "clinical_reports"
            ],

        "drug_id":
            drug_id,

        "disease_id":
            disease_id

    }


# =========================================================
# BUILD FINAL DATASET
# =========================================================

def build_final_dataset(
    old_rows
):

    known_rows = [

        row

        for row in old_rows

        if row[
            "label"
        ] == 1

    ]

    old_controls = [

        row

        for row in old_rows

        if row[
            "label"
        ] == 0

    ]


    known_disease_by_drug = {

        row["drug"]:
            row["disease"]

        for row in known_rows

    }


    good_controls = []
    bad_controls = []


    for row in old_controls:

        if old_control_is_valid(
            row
        ):

            row[
                "group"
            ] = "screened_existing_control"

            good_controls.append(
                row
            )

        else:

            bad_controls.append(
                row
            )


    print()
    print(
        "=========================================="
    )

    print(
        "OLD RESULTS CHECK"
    )

    print(
        "=========================================="
    )

    print(
        "Known pairs reused:",
        len(known_rows)
    )

    print(
        "Existing controls reused:",
        len(good_controls)
    )

    print(
        "Controls needing replacement:",
        len(bad_controls)
    )


    replacements = []

    used = {

        (
            row["drug"],
            row["disease"]
        )

        for row in good_controls

    }


    for index, old_control in enumerate(
        bad_controls,
        start=1
    ):

        drug = (
            old_control["drug"]
        )

        known_disease = (
            known_disease_by_drug[
                drug
            ]
        )


        print()
        print(
            f"Finding replacement "
            f"{index}/{len(bad_controls)} "
            f"for {drug}"
        )


        replacement_disease = None


        for candidate in (
            CONTROL_DISEASE_POOL
        ):

            key = (
                drug,
                candidate
            )

            if key in used:
                continue


            try:

                if candidate_is_valid(

                    drug,
                    known_disease,
                    candidate

                ):

                    replacement_disease = (
                        candidate
                    )

                    break

            except Exception as error:

                print(
                    "Skipped:",
                    candidate,
                    error
                )


        if not replacement_disease:

            print(
                "WARNING: "
                "No replacement found for",
                drug
            )

            continue


        print(
            "Replacement:",
            drug,
            "->",
            replacement_disease
        )


        result = (
            analyze_new_control(

                drug,
                replacement_disease

            )
        )


        replacements.append(
            result
        )


        used.add(
            (
                drug,
                replacement_disease
            )
        )


    final_rows = (

        known_rows
        +
        good_controls
        +
        replacements

    )


    return final_rows


# =========================================================
# ROC AUC
# =========================================================

def calculate_auc(
    rows,
    score_name
):

    positives = [

        row

        for row in rows

        if row[
            "label"
        ] == 1

    ]

    negatives = [

        row

        for row in rows

        if row[
            "label"
        ] == 0

    ]

    wins = 0
    comparisons = 0


    for positive in positives:

        for negative in negatives:

            p = safe_float(
                positive[
                    score_name
                ]
            )

            n = safe_float(
                negative[
                    score_name
                ]
            )

            comparisons += 1

            if p > n:

                wins += 1

            elif p == n:

                wins += 0.5


    if comparisons == 0:
        return 0

    return (
        wins
        /
        comparisons
    )


# =========================================================
# METRICS
# =========================================================

def calculate_metrics(
    rows,
    score_name,
    threshold
):

    tp = 0
    tn = 0
    fp = 0
    fn = 0


    for row in rows:

        score = safe_float(
            row[
                score_name
            ]
        )

        prediction = (

            1

            if score >= threshold

            else 0

        )

        actual = (
            row["label"]
        )


        if prediction == 1 and actual == 1:

            tp += 1

        elif prediction == 0 and actual == 0:

            tn += 1

        elif prediction == 1 and actual == 0:

            fp += 1

        else:

            fn += 1


    total = (
        tp
        +
        tn
        +
        fp
        +
        fn
    )


    accuracy = (

        (tp + tn)
        /
        total

        if total

        else 0

    )


    precision = (

        tp
        /
        (tp + fp)

        if (
            tp + fp
        )

        else 0

    )


    recall = (

        tp
        /
        (tp + fn)

        if (
            tp + fn
        )

        else 0

    )


    f1 = (

        2
        *
        precision
        *
        recall
        /
        (
            precision
            +
            recall
        )

        if (
            precision
            +
            recall
        )

        else 0

    )


    return {

        "accuracy":
            accuracy,

        "precision":
            precision,

        "recall":
            recall,

        "f1":
            f1,

        "tp":
            tp,

        "tn":
            tn,

        "fp":
            fp,

        "fn":
            fn

    }


# =========================================================
# BEST THRESHOLD
# =========================================================

def find_best_threshold(
    rows,
    score_name
):

    best_threshold = 0
    best_f1 = -1


    for threshold in range(
        0,
        101
    ):

        metrics = (
            calculate_metrics(
                rows,
                score_name,
                threshold
            )
        )


        if (
            metrics["f1"]
            >
            best_f1
        ):

            best_f1 = (
                metrics["f1"]
            )

            best_threshold = (
                threshold
            )


    return best_threshold


# =========================================================
# PRINT REPORT
# =========================================================

def report(
    title,
    rows,
    score_name
):

    positive_scores = [

        safe_float(
            row[
                score_name
            ]
        )

        for row in rows

        if row[
            "label"
        ] == 1

    ]


    control_scores = [

        safe_float(
            row[
                score_name
            ]
        )

        for row in rows

        if row[
            "label"
        ] == 0

    ]


    threshold = (
        find_best_threshold(
            rows,
            score_name
        )
    )


    metrics = (
        calculate_metrics(
            rows,
            score_name,
            threshold
        )
    )


    auc = (
        calculate_auc(
            rows,
            score_name
        )
    )


    print()
    print(
        "=========================================="
    )

    print(title)

    print(
        "=========================================="
    )


    print(
        "Known-pair average:",
        round(
            mean(
                positive_scores
            ),
            2
        )
    )


    print(
        "Control average:",
        round(
            mean(
                control_scores
            ),
            2
        )
    )


    print(
        "Best threshold:",
        threshold
    )


    print(
        "Accuracy:",
        round(
            metrics[
                "accuracy"
            ],
            3
        )
    )


    print(
        "Precision:",
        round(
            metrics[
                "precision"
            ],
            3
        )
    )


    print(
        "Recall:",
        round(
            metrics[
                "recall"
            ],
            3
        )
    )


    print(
        "F1:",
        round(
            metrics[
                "f1"
            ],
            3
        )
    )


    print(
        "ROC-AUC:",
        round(
            auc,
            3
        )
    )


    print(
        "TP:",
        metrics["tp"],
        "TN:",
        metrics["tn"],
        "FP:",
        metrics["fp"],
        "FN:",
        metrics["fn"]
    )


# =========================================================
# SAVE FINAL CSV
# =========================================================

def save_final_results(
    rows
):

    fields = [

        "drug",
        "disease",
        "label",
        "group",

        "prediction_score",
        "prediction_strength",

        "full_score",
        "full_strength",

        "target_overlap_count",
        "max_target_association",
        "overlapping_targets",

        "publication_count",
        "abstracts_analyzed",

        "supportive_count",
        "negative_count",
        "unclear_count",

        "clinical_stage",
        "clinical_reports",

        "drug_id",
        "disease_id"

    ]


    with open(
        FINAL_RESULTS_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()


        for row in rows:

            writer.writerow({

                field:
                    row.get(
                        field,
                        ""
                    )

                for field
                in fields

            })


    print()
    print(
        "Saved:",
        FINAL_RESULTS_FILE
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print(
        "##########################################"
    )

    print(
        "       BIOGRAPH AI FINAL BENCHMARK"
    )

    print(
        "##########################################"
    )


    old_rows = (
        load_old_results()
    )


    final_rows = (
        build_final_dataset(
            old_rows
        )
    )


    print()
    print(
        "Final dataset size:",
        len(final_rows)
    )


    known_count = sum(

        1

        for row in final_rows

        if row[
            "label"
        ] == 1

    )


    control_count = sum(

        1

        for row in final_rows

        if row[
            "label"
        ] == 0

    )


    print(
        "Known pairs:",
        known_count
    )


    print(
        "Screened controls:",
        control_count
    )


    print()
    print(
        "##########################################"
    )

    print(
        "              FINAL RESULTS"
    )

    print(
        "##########################################"
    )


    report(

        "MODEL A — FULL EVIDENCE MODEL",

        final_rows,

        "full_score"

    )


    report(

        "MODEL B — PREDICTION MODEL",

        final_rows,

        "prediction_score"

    )


    save_final_results(
        final_rows
    )


    print()
    print(
        "##########################################"
    )

    print(
        "              FINISHED"
    )

    print(
        "##########################################"
    )


    print()
    print(
        "This benchmark reused the original V8.1 "
        "results and only reran replacement controls."
    )


    print(
        "Controls should be described as screened "
        "mismatched controls, not proven negatives."
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()