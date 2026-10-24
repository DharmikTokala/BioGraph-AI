let cy = null;


// ========================================================
// STATUS
// ========================================================

function setStatus(
  message,
  loading = false
) {

  const text =
    document.getElementById(
      "statusText"
    );

  const dot =
    document.getElementById(
      "statusDot"
    );

  text.textContent =
    message;


  if (loading) {

    dot.classList.add(
      "loading"
    );

  }

  else {

    dot.classList.remove(
      "loading"
    );

  }

}


// ========================================================
// LOADING OVERLAY
// ========================================================

function showGraphLoading(
  show
) {

  const loading =
    document.getElementById(
      "graphLoading"
    );


  if (show) {

    loading.classList.remove(
      "hidden"
    );

  }

  else {

    loading.classList.add(
      "hidden"
    );

  }

}


// ========================================================
// RESET DETAILS
// ========================================================

function clearDetails() {

  document.getElementById(
    "nodeTitle"
  ).textContent =
    "Select a node";


  document.getElementById(
    "nodeType"
  ).textContent =
    "—";


  document.getElementById(
    "nodeDescription"
  ).innerHTML =
    "";


  document.getElementById(
    "sourceLink"
  ).classList.add(
    "hidden"
  );


  document.getElementById(
    "paperSection"
  ).classList.add(
    "hidden"
  );

}


// ========================================================
// BUILD GRAPH
// ========================================================

async function buildGraph() {

  const disease =
    document
      .getElementById(
        "diseaseInput"
      )
      .value
      .trim();


  if (!disease) {

    alert(
      "Enter a disease to explore."
    );

    return;

  }


  const button =
    document.getElementById(
      "searchBtn"
    );


  button.disabled =
    true;


  button.querySelector(
    "span"
  ).textContent =
    "Building graph...";


  clearDetails();


  showGraphLoading(
    true
  );


  setStatus(
    "Retrieving biomedical evidence...",
    true
  );


  try {

    const response =
      await fetch(

        `/api/graph?disease=${
          encodeURIComponent(
            disease
          )
        }`

      );


    const graph =
      await response.json();


    console.log(
      "BIOGRAPH DATA:",
      graph
    );


    if (graph.error) {

      alert(
        graph.error
      );


      setStatus(
        "Unable to load disease"
      );


      return;

    }


    // ----------------------------------------------------
    // SUMMARY
    // ----------------------------------------------------

    document.getElementById(
      "graphName"
    ).textContent =
      graph.display_name;


    document.getElementById(
      "targetCount"
    ).textContent =
      graph.stats?.targets
      || 0;


    document.getElementById(
      "drugCount"
    ).textContent =
      graph.stats?.drugs
      || 0;


    document.getElementById(
      "candidateCount"
    ).textContent =
      graph.stats?.clinical_candidates
      || 0;


    // ----------------------------------------------------
    // ELEMENTS
    // ----------------------------------------------------

    const elements = [

      ...graph.nodes.map(

        node => ({

          data: {
            ...node
          }

        })

      ),


      ...graph.edges.map(

        (edge, index) => ({

          data: {

            id:
              `edge_${index}`,

            source:
              edge.source,

            target:
              edge.target,

            label:
              edge.label

          }

        })

      )

    ];


    if (cy) {

      cy.destroy();

      cy = null;

    }


    // ----------------------------------------------------
    // CREATE CYTOSCAPE
    // ----------------------------------------------------

    cy = cytoscape({

      container:
        document.getElementById(
          "cy"
        ),

      elements,

      wheelSensitivity:
        0.22,

      minZoom:
        0.2,

      maxZoom:
        2.6,


      layout: {

        name:
          "cose",

        animate:
          false,

        padding:
          48,

        nodeRepulsion:
          15000,

        idealEdgeLength:
          155,

        edgeElasticity:
          100,

        gravity:
          0.16

      },


      style: [

        // ================================================
        // NORMAL NODE
        // ================================================

        {

          selector:
            "node",

          style: {

            "label":
              "data(label)",

            "font-size":
              13,

            "font-weight":
              600,

            "color":
              "#eef3ff",

            "text-valign":
              "bottom",

            "text-margin-y":
              11,

            "text-wrap":
              "wrap",

            "text-max-width":
              120,

            "width":
              58,

            "height":
              58,

            "background-color":
              "#7183ff",

            "border-width":
              2,

            "border-color":
              "#aab6ff",

            "overlay-opacity":
              0

          }

        },


        // ================================================
        // SELECTED
        // ================================================

        {

          selector:
            "node:selected",

          style: {

            "border-width":
              5,

            "border-color":
              "#ffffff",

            "overlay-opacity":
              0

          }

        },


        // ================================================
        // DISEASE
        // ================================================

        {

          selector:
            'node[type="disease"]',

          style: {

            "background-color":
              "#ef5f84",

            "width":
              86,

            "height":
              86,

            "border-color":
              "#ffb2c4",

            "font-size":
              14

          }

        },


        // ================================================
        // PROTEIN
        // ================================================

        {

          selector:
            'node[type="protein"]',

          style: {

            "background-color":
              "#f4b548",

            "border-color":
              "#ffe19a",

            "shape":
              "ellipse"

          }

        },


        // ================================================
        // DRUG
        // ================================================

        {

          selector:
            'node[type="drug"]',

          style: {

            "background-color":
              "#34c8a6",

            "border-color":
              "#9ff3df",

            "shape":
              "round-rectangle",

            "width":
              100,

            "height":
              52,

            "text-max-width":
              130

          }

        },


        // ================================================
        // EDGE
        // ================================================

        {

          selector:
            "edge",

          style: {

            "width":
              1.7,

            "curve-style":
              "bezier",

            "line-color":
              "#3c485d",

            "target-arrow-color":
              "#3c485d",

            "target-arrow-shape":
              "triangle",

            "arrow-scale":
              0.75,

            "label":
              "data(label)",

            "font-size":
              7,

            "color":
              "#67748a",

            "text-rotation":
              "autorotate",

            "text-background-color":
              "#080d14",

            "text-background-opacity":
              0.9,

            "text-background-padding":
              3

          }

        }

      ]

    });


    // ----------------------------------------------------
    // NODE CLICK
    // ----------------------------------------------------

    cy.on(
      "tap",
      "node",
      async function(event) {

        const node =
          event.target;


        const data =
          node.data();


        cy.nodes()
          .unselect();


        node.select();


        showNodeDetails(
          data
        );


        await loadPapers(
          data
        );


        if (
          data.type === "drug"
        ) {

          await loadEvidenceAnalysis(
            data
          );

        }

      }
    );


    // ----------------------------------------------------
    // FIT
    // ----------------------------------------------------

    setTimeout(
      () => {

        cy.fit(
          cy.elements(),
          55
        );

      },
      120
    );


    setStatus(

      `${graph.stats?.targets || 0} targets · `
      +
      `${graph.stats?.drugs || 0} matched drugs · `
      +
      `click a node to inspect evidence`

    );

  }

  catch (error) {

    console.error(
      error
    );


    alert(
      "BioGraph could not build this graph. "
      + error.message
    );


    setStatus(
      "Graph failed to load"
    );

  }

  finally {

    button.disabled =
      false;


    button.querySelector(
      "span"
    ).textContent =
      "Build knowledge graph";


    showGraphLoading(
      false
    );

  }

}


// ========================================================
// BASIC NODE DETAILS
// ========================================================

function showNodeDetails(
  data
) {

  const title =
    document.getElementById(
      "nodeTitle"
    );


  const type =
    document.getElementById(
      "nodeType"
    );


  const description =
    document.getElementById(
      "nodeDescription"
    );


  title.textContent =
    data.label
    || "Unknown";


  type.textContent =
    readableType(
      data.type
    );


  description.innerHTML =
    "";


  if (data.type === "disease") {

    addInfoMessage(

      description,

      "Disease node",

      "This is the disease used as the starting point for the knowledge graph."

    );

  }


  if (data.type === "protein") {

    addInfoMessage(

      description,

      "Biological target",

      "This gene or protein has biomedical evidence associating it with the selected disease."

    );

  }


  if (data.type === "drug") {

    addInfoMessage(

      description,

      "Drug / clinical candidate",

      "This compound appears in clinical information for the selected disease and is connected through a biological target."

    );

  }


  addDetail(

    description,
    "Full name",
    data.full_name

  );


  addDetail(

    description,
    "Biological type",
    data.biotype

  );


  if (
    data.score !== undefined
    &&
    data.score !== null
  ) {

    addDetail(

      description,
      "Disease association score",
      `${data.score} / 1`

    );

  }


  if (
    data.clinical_stage !== undefined
    &&
    data.clinical_stage !== null
  ) {

    addDetail(

      description,
      "Maximum clinical stage",
      formatClinicalStage(
        data.clinical_stage
      )

    );

  }


  if (
    data.clinical_reports !== undefined
    &&
    data.clinical_reports !== null
  ) {

    addDetail(

      description,
      "Clinical reports",
      data.clinical_reports

    );

  }


  addDetail(

    description,
    "Description",
    data.description

  );


  addDetail(

    description,
    "Why BioGraph connected it",
    data.why

  );


  const link =
    document.getElementById(
      "sourceLink"
    );


  if (data.source_url) {

    link.href =
      data.source_url;


    link.classList.remove(
      "hidden"
    );

  }

  else {

    link.classList.add(
      "hidden"
    );

  }

}


// ========================================================
// READABLE TYPE
// ========================================================

function readableType(
  type
) {

  if (
    type === "protein"
  ) {

    return "GENE / PROTEIN";

  }


  if (
    type === "drug"
  ) {

    return "DRUG / CLINICAL CANDIDATE";

  }


  if (
    type === "disease"
  ) {

    return "DISEASE";

  }


  return (
    type
    || "UNKNOWN"
  ).toUpperCase();

}


// ========================================================
// CLINICAL STAGE
// ========================================================

function formatClinicalStage(
  stage
) {

  if (!stage) {

    return "Not available";

  }


  const text =
    String(stage)
      .replaceAll("_", " ")
      .toUpperCase();


  if (
    text === "APPROVAL"
  ) {

    return "Approved";

  }


  return text
    .toLowerCase()
    .replace(
      /\b\w/g,
      char =>
        char.toUpperCase()
    );

}


// ========================================================
// INFO MESSAGE
// ========================================================

function addInfoMessage(
  container,
  heading,
  text
) {

  const block =
    document.createElement(
      "div"
    );


  block.className =
    "detail-block";


  const strong =
    document.createElement(
      "strong"
    );


  strong.textContent =
    heading;


  const paragraph =
    document.createElement(
      "p"
    );


  paragraph.textContent =
    text;


  block.appendChild(
    strong
  );


  block.appendChild(
    paragraph
  );


  container.appendChild(
    block
  );

}


// ========================================================
// DETAIL
// ========================================================

function addDetail(
  container,
  label,
  value
) {

  if (
    value === undefined
    ||
    value === null
    ||
    value === ""
  ) {

    return;

  }


  const block =
    document.createElement(
      "div"
    );


  block.className =
    "detail-block";


  const heading =
    document.createElement(
      "strong"
    );


  heading.textContent =
    label;


  const text =
    document.createElement(
      "p"
    );


  text.textContent =
    value;


  block.appendChild(
    heading
  );


  block.appendChild(
    text
  );


  container.appendChild(
    block
  );

}


// ========================================================
// EVIDENCE ANALYSIS
// ========================================================

async function loadEvidenceAnalysis(
  data
) {

  const description =
    document.getElementById(
      "nodeDescription"
    );


  const analysis =
    document.createElement(
      "div"
    );


  analysis.className =
    "evidence-score-display";


  analysis.innerHTML =
    `
      <strong>BioGraph evidence analysis</strong>

      <p style="
        margin:8px 0 0;
        color:#8795aa;
        font-size:0.78rem;
      ">
        Analyzing disease, target, clinical
        and literature evidence...
      </p>
    `;


  description.prepend(
    analysis
  );


  try {

    const params =
      new URLSearchParams({

        drug_id:
          data.entity_id
          || "",

        disease_id:
          data.disease_id
          || "",

        drug_name:
          data.full_name
          || "",

        disease_name:
          data.disease_name
          || "",

        target_symbol:
          data.target_symbol
          || "",

        clinical_stage:
          data.clinical_stage
          || "",

        clinical_reports:
          data.clinical_reports
          || 0,

        association_score:
          data.association_score
          || 0

      });


    const response =
      await fetch(

        `/api/evidence-analysis?${params.toString()}`

      );


    const result =
      await response.json();


    if (result.error) {

      analysis.innerHTML =
        `
          <strong>
            Evidence analysis unavailable
          </strong>

          <p style="
            color:#8795aa;
            font-size:0.78rem;
          ">
            ${result.error}
          </p>
        `;

      return;

    }


    analysis.innerHTML =
      "";


    // ----------------------------------------------------
    // SCORE HEADER
    // ----------------------------------------------------

    const top =
      document.createElement(
        "div"
      );


    top.className =
      "score-top-row";


    const left =
      document.createElement(
        "div"
      );


    const title =
      document.createElement(
        "strong"
      );


    title.textContent =
      "Evidence score";


    const score =
      document.createElement(
        "div"
      );


    score.innerHTML =
      `
        <span class="big-score">
          ${result.score}
        </span>

        <span class="score-out-of">
          / 100
        </span>
      `;


    const strength =
      document.createElement(
        "span"
      );


    strength.className =
      "strength-label";


    strength.textContent =
      `${result.strength} evidence`;


    left.appendChild(
      title
    );


    left.appendChild(
      score
    );


    left.appendChild(
      strength
    );


    top.appendChild(
      left
    );


    analysis.appendChild(
      top
    );


    // ----------------------------------------------------
    // EXPLANATION
    // ----------------------------------------------------

    const explanationTitle =
      document.createElement(
        "strong"
      );


    explanationTitle.style.marginTop =
      "17px";


    explanationTitle.style.display =
      "block";


    explanationTitle.textContent =
      "What this means";


    analysis.appendChild(
      explanationTitle
    );


    const explanation =
      document.createElement(
        "p"
      );


    explanation.style.color =
      "#98a6bb";


    explanation.style.lineHeight =
      "1.6";


    explanation.style.fontSize =
      "0.8rem";


    explanation.textContent =
      result.explanation;


    analysis.appendChild(
      explanation
    );


    // ----------------------------------------------------
    // COUNTS
    // ----------------------------------------------------

    addEvidenceMetric(

      analysis,

      "Drug–disease publication mentions",

      result.relation_publication_count

    );


    addEvidenceMetric(

      analysis,

      "Abstracts examined",

      result.abstracts_analyzed

    );


    addEvidenceMetric(

      analysis,

      "Supportive language signals",

      result.supportive_count

    );


    addEvidenceMetric(

      analysis,

      "Uncertain / negative signals",

      result.negative_count

    );


    // ----------------------------------------------------
    // PAPERS
    // ----------------------------------------------------

    if (
      result.supportive
      &&
      result.supportive.length
    ) {

      addSignalSection(

        analysis,

        "Supporting literature signals",

        result.supportive

      );

    }


    if (
      result.uncertain_negative
      &&
      result.uncertain_negative.length
    ) {

      addSignalSection(

        analysis,

        "Possible uncertain / negative signals",

        result.uncertain_negative

      );

    }


    // ----------------------------------------------------
    // NOTE
    // ----------------------------------------------------

    const note =
      document.createElement(
        "p"
      );


    note.style.marginTop =
      "17px";


    note.style.fontSize =
      "0.68rem";


    note.style.lineHeight =
      "1.5";


    note.style.color =
      "#69778c";


    note.textContent =
      result.method_note;


    analysis.appendChild(
      note
    );

  }

  catch (error) {

    console.error(
      error
    );


    analysis.innerHTML =
      `
        <strong>
          Evidence analysis unavailable
        </strong>

        <p style="
          color:#8795aa;
          font-size:0.78rem;
        ">
          The evidence service could not complete
          this request.
        </p>
      `;

  }

}


// ========================================================
// EVIDENCE METRIC
// ========================================================

function addEvidenceMetric(
  container,
  label,
  value
) {

  const row =
    document.createElement(
      "div"
    );


  row.style.display =
    "flex";


  row.style.justifyContent =
    "space-between";


  row.style.gap =
    "18px";


  row.style.marginTop =
    "8px";


  row.style.fontSize =
    "0.75rem";


  const left =
    document.createElement(
      "span"
    );


  left.style.color =
    "#7f8ca0";


  left.textContent =
    label;


  const right =
    document.createElement(
      "strong"
    );


  right.textContent =
    value ?? 0;


  row.appendChild(
    left
  );


  row.appendChild(
    right
  );


  container.appendChild(
    row
  );

}


// ========================================================
// SIGNAL PAPERS
// ========================================================

function addSignalSection(
  container,
  headingText,
  papers
) {

  const heading =
    document.createElement(
      "strong"
    );


  heading.style.display =
    "block";


  heading.style.marginTop =
    "18px";


  heading.style.marginBottom =
    "8px";


  heading.textContent =
    headingText;


  container.appendChild(
    heading
  );


  papers.forEach(
    paper => {

      const wrapper =
        document.createElement(
          "div"
        );


      wrapper.style.marginBottom =
        "8px";


      const link =
        document.createElement(
          "a"
        );


      link.href =
        paper.url;


      link.target =
        "_blank";


      link.rel =
        "noopener noreferrer";


      link.style.display =
        "block";


      link.style.color =
        "#aebcff";


      link.style.fontSize =
        "0.76rem";


      link.style.lineHeight =
        "1.45";


      link.style.textDecoration =
        "none";


      link.textContent =
        paper.title
        ||
        `PubMed ${paper.pmid}`;


      wrapper.appendChild(
        link
      );


      if (
        paper.matched_terms
        &&
        paper.matched_terms.length
      ) {

        const detected =
          document.createElement(
            "span"
          );


        detected.style.display =
          "block";


        detected.style.marginTop =
          "2px";


        detected.style.color =
          "#65738a";


        detected.style.fontSize =
          "0.65rem";


        detected.textContent =
          "Detected signal: "
          +
          paper.matched_terms.join(
            ", "
          );


        wrapper.appendChild(
          detected
        );

      }


      container.appendChild(
        wrapper
      );

    }
  );

}


// ========================================================
// GENERAL PAPERS
// ========================================================

async function loadPapers(
  data
) {

  const section =
    document.getElementById(
      "paperSection"
    );


  const list =
    document.getElementById(
      "papers"
    );


  const count =
    document.getElementById(
      "paperCount"
    );


  if (
    !data.entity_id
    ||
    !data.type
  ) {

    section.classList.add(
      "hidden"
    );

    return;

  }


  section.classList.remove(
    "hidden"
  );


  list.innerHTML =
    `
      <div class="paper-loading">
        Loading scientific literature...
      </div>
    `;


  count.textContent =
    "";


  try {

    const response =
      await fetch(

        `/api/papers?entity_type=${
          encodeURIComponent(
            data.type
          )
        }&entity_id=${
          encodeURIComponent(
            data.entity_id
          )
        }`

      );


    const result =
      await response.json();


    if (
      result.error
      ||
      !result.papers
      ||
      result.papers.length === 0
    ) {

      list.innerHTML =
        `
          <div class="paper-empty">
            No publication results were returned
            for this entity.
          </div>
        `;

      return;

    }


    count.textContent =
      `${result.count} mentions`;


    list.innerHTML =
      "";


    result.papers.forEach(
      paper => {

        const card =
          document.createElement(
            "a"
          );


        card.className =
          "paper-card";


        card.href =
          paper.url;


        card.target =
          "_blank";


        card.rel =
          "noopener noreferrer";


        const name =
          document.createElement(
            "strong"
          );


        name.textContent =
          `PubMed ${paper.pmid}`;


        const date =
          document.createElement(
            "span"
          );


        date.textContent =
          paper.date
          ? `Publication date: ${paper.date}`
          : "Publication date unavailable";


        card.appendChild(
          name
        );


        card.appendChild(
          date
        );


        list.appendChild(
          card
        );

      }
    );

  }

  catch (error) {

    console.error(
      error
    );


    list.innerHTML =
      `
        <div class="paper-empty">
          Scientific literature could not
          be loaded.
        </div>
      `;

  }

}


// ========================================================
// EVENTS
// ========================================================

document
  .getElementById(
    "searchBtn"
  )
  .addEventListener(
    "click",
    buildGraph
  );


document
  .getElementById(
    "diseaseInput"
  )
  .addEventListener(
    "keydown",
    event => {

      if (
        event.key === "Enter"
      ) {

        buildGraph();

      }

    }
  );


document
  .getElementById(
    "fitBtn"
  )
  .addEventListener(
    "click",
    () => {

      if (cy) {

        cy.fit(
          cy.elements(),
          55
        );

      }

    }
  );


// ========================================================
// EXAMPLE BUTTONS
// ========================================================

document
  .querySelectorAll(
    ".example-chip"
  )
  .forEach(
    button => {

      button.addEventListener(
        "click",
        () => {

          document.getElementById(
            "diseaseInput"
          ).value =
            button.dataset.disease;


          buildGraph();

        }
      );

    }
  );


// ========================================================
// START
// ========================================================

buildGraph();