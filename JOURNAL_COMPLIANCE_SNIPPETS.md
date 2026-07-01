# Journal compliance snippets

Use these drafts when updating the revised manuscript and point-by-point response.
Replace bracketed placeholders after Zenodo DOI assignment (see [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)).

---

## 1. Code Availability (separate section after Data availability)

```text
The code used for data preprocessing, model training, internal validation, temporal validation, model evaluation, inference, SHAP-based model interpretation, and figure generation has been deposited in Zenodo and is available at https://doi.org/10.5281/zenodo.21107169. The active development repository is available at https://github.com/linzixuan45/hypokalemia-icu-mortality. The repository includes the analysis scripts, optional SQL extraction scripts, inference code, final research model objects, variable dictionary, README, and MODEL_CARD. Raw patient-level data are not redistributed because access to MIMIC and the local validation cohorts is restricted.
```

Optional calculator sentence (Methods or Code availability):

```text
An HTTPS research demonstration calculator for the 8-feature model is available at https://k.mixaihub.top (not for clinical use).
```

---

## 2. Ethics / guidelines statement (Methods)

Add after the existing institutional approval statement:

```text
The study was approved by the relevant institutional review board, and all methods were performed in accordance with the relevant guidelines and regulations. Use of MIMIC-III and MIMIC-IV data followed PhysioNet credentialed access and data-use requirements.
```

---

## 3. Point-by-point response — Code deposit (editor requirement)

**Editor comment:** Custom/bespoke computational code must be deposited in a DOI-assigning repository and linked from Methods or Code Availability.

**Response:**

```text
We thank the editor for this reminder. We have deposited the underlying analysis code in Zenodo (https://doi.org/10.5281/zenodo.21107169) and maintain the active development repository at https://github.com/linzixuan45/hypokalemia-icu-mortality. The deposit includes analysis scripts, optional SQL extraction scripts, inference code, final research model objects, variable dictionary, README, and MODEL_CARD. We have also deployed an HTTPS research demonstration calculator at https://k.mixaihub.top (not for clinical use). The revised manuscript now includes a separate Code availability section with these links. Raw patient-level data were not redistributed because MIMIC and local validation cohorts are access-restricted.
```

---

## 4. Point-by-point response — Guidelines and regulations (editor requirement)

**Editor comment:** Confirm that all methods were performed in accordance with relevant guidelines and regulations.

**Response:**

```text
We have added an explicit statement to the Methods section confirming that all methods were performed in accordance with the relevant guidelines and regulations, in addition to the existing institutional approval disclosure.
```

---

## 5. Placeholder tracking

| Item | Status | Value |
|------|--------|-------|
| Research demo URL | Done | https://k.mixaihub.top |
| GitHub URL | Done | https://github.com/linzixuan45/hypokalemia-icu-mortality |
| Zenodo concept DOI | Done | 10.5281/zenodo.21107168 |
| Zenodo version DOI | Done | 10.5281/zenodo.21107169 |
| Release tag | Done | `v2.0.0` |
| Submission ID | Known | `91406a0b-fc8b-4fcf-95bc-820b99f21793` |
