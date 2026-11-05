# Brief for a fresh session: redraft the abstract

Written 4 November 2026 at the end of a long session. Paste the prompt at the bottom into a new Claude Code session opened in `/Volumes/PortableSSD/Github/canada-emissions-disaggregated`, with effort set high. Everything the session needs is listed here.

## What to do

Redraft the abstract of `01.manuscript/Manuscript.qmd`, the paragraph under `# Abstract {.unnumbered}`, and nothing else in the file. The abstract must read as the work of a leading author in the field of national greenhouse gas inventories and forest carbon accounting, using the terminology, perspective and statistical terms of the papers listed below, which are the literature on disaggregating natural disturbances in Canada's and other countries' national emissions reporting.

## The literature to read first, in full

Canada, the inventory and its model:

- /Volumes/PortableSSD/Github/library-science/library/staging/Kurz et al 2018 Quantifying-the-impacts-of-human-activities-on-reported-greenhouse-gas-emissions-and-removals-in-canada.pdf
- /Volumes/PortableSSD/Github/canada-emissions-disaggregated/04.references/literature/Kurz et al 2024 Revised historic harvest data improve estimates of the impacts of human activities on reported greenhouse gas emissions and removals in Canada's managed forest.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Bysouth et al 2024 High emissions or carbon neutral - Inclusion of anthropogenic forest sinks leads to underreporting of forestry emissions.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Thompson et al 2026 Incorporating observed fire severity in refined emissions estimates for boreal and temperate forest fires in the carbon budget model CBM-CFS3 v1.2.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Smyth et al 2026 Forest wildfire emissions using the Canadian Fire Effects Model within the Generic Carbon Budget Model.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Bernier et al 2010 Reconstructing and modelling 71 years of forest growth in a Canadian boreal landscape.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Kooten etl al 2019 Carbon Uptake and Forest Management under Uncertainty- Why Natural Disturbance Matters.pdf

Natural disturbance in national accounting elsewhere:

- /Volumes/PortableSSD/Github/canada-emissions-disaggregated/04.references/literature/Bowman et al 2023 Wildfire national carbon accounting- how natural and anthropogenic landscape fires emissions are treated in the 2020 Australian government greenhouse gas accounts report to the UNFCCC.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Canadell et al 2007 Factoring out natural and indirect human effects on terrestrial carbon sources and sinks.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Fry 2011 If a Tree Falls in a Kyoto Forest and Nobody is There to Hear it, will it be Accounted for.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Pilli et al 2016 Modelling forest carbon stock changes as affected by harvest and natural disturbances - Comparison with countries' estimates for forest management.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Pilli et al 2021 Combined effects of natural disturbances and management on forest carbon sequestration- the case of Vaia storm in Italy.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Pilli et al 2022 Correction - Combined effects of natural disturbances and management on forest carbon sequestration - the case of Vaia storm in Italy.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Dias-Yanez 2016 Assessment of the Main Natural Disturbances on Norwegian Forest Based on 20 Years of National Inventory.pdf
- /Volumes/PortableSSD/Github/library-science/library/staging/Ritter et al 2025 Alarming decline in the carbon sink of European forests driven by disturbances.pdf

The guidance under test:

- /Volumes/PortableSSD/Github/library-methodologies/IPCC/IPCC-2019-V4-Ch2-Generic-Methods.pdf, section 2.6, the natural disturbance approach of the 2019 Refinement, with Boxes 2.2i to 2.2k.
- /Volumes/PortableSSD/Github/library-methodologies/IPCC/IPCC-2019-V1-Ch3-Uncertainties.pdf, Approaches 1 and 2.
- The 2013 Kyoto Protocol Supplement, section 2.3.9, listed in `05.tasks/ipcc-scan/`.

Read the abstracts and introductions of all of them with `pdftotext`, and quote nothing without checking the page.

## The manuscript's own context

Read `CLAUDE.md` in the repository, then `05.tasks/2026-11-04-ipcc-debates.md`, then the rendered `01.manuscript/Manuscript.docx` through `pandoc -t plain`, so the abstract states what the paper finds and nothing else. The paper applies the ART TREES crediting standard to Canada's 2026 inventory for the crediting years 2017 to 2024 under three accounts, measures the uncertainty deduction by Monte Carlo, and reproduces FAOSTAT's Tier 1 fire emissions for Canada from FAO's stated method.

## Rules the abstract must meet

1. One paragraph, at most 250 words, counted with each inline number as one word. The journal is Climatic Change.
2. Past tense throughout. No sentence over 30 words. No colon, no dash of any kind, no first person, no abbreviation except ART TREES, which is written "the ART TREES standard" and never expanded or explained.
3. Seven moves that may share sentences, in this order: the message a reader can repeat, set in its context; the gap; the design, "This study" plus verb with data, year and place; the methods named exactly; results with direction; the comparison as the finding; one closing recommendation.
4. The terminology is that of the papers above: national greenhouse gas inventory, managed forest, emissions and removals, natural disturbances, anthropogenic, the managed land proxy, factoring out, natural disturbance provision, background level and margin, net source and net sink, reference level and crediting level, emission reductions, reversals, buffer, Monte Carlo, 90 per cent confidence interval, uncertainty adjustment factor, Tier 1, activity data and emission factors, verification against an independent estimate.
5. Every number stays as the inline R expression already in the source, so that the render fills it. The expressions and the sentences that carry them are in the current abstract below. Do not type a number by hand.
6. Seamus rejected these today and they must not return: "credit" or "credits" as a noun standing alone ("What credit?"); "Canada reported its managed forest" with no reader told to whom or when; "as cited in the 2019 Refinement"; "large and variable"; "which changed by hundreds of millions of tonnes from year to year"; three opening sentences that repeat each other; any expansion of ART TREES; a subtitle.
7. Change only the abstract. Then render in the background with `quarto render /Volumes/PortableSSD/Github/canada-emissions-disaggregated/01.manuscript/Manuscript.qmd --to docx -M echo:false`, read the count line the render prints (the Climatic Change count must stay at or under 10,000 and the abstract under 250), and render the anonymised copy the same way with `--output Manuscript-anonymised.docx`, move it into `01.manuscript/` and run `python3 01.manuscript/_tools/anonymise-docx.py` on it. Show Seamus the rendered abstract in chat before anything else.

## The current abstract in the source, inline expressions included

Whether Canada's managed forest showed emission reductions under a crediting standard depended on one accounting choice, the disaggregation of natural disturbances from the reported total. Canada's inventory, submitted to the United Nations Framework Convention on Climate Change, reported the lands dominated by wildfire and insects apart from the remaining managed forest, as the guidelines allowed. What that choice did to the emission reductions a government could sell had not been measured. This study applied the ART TREES standard to Canada's 2026 inventory for 2017 to 2024. The reported account was compared with the same account with natural disturbances included, and with a threshold account excluding only fire years above a 13 year baseline. With natural disturbances disaggregated, the managed forest showed emission reductions in `r sum(split_pos)` of `r nrow(credits)` years, `r round(sum(credits[["Disaggregated reductions (Mt)"]][split_pos]), 1)` million tonnes of carbon dioxide equivalent. With them included, emissions in `r credits$Year[worst]` alone exceeded the crediting level by `r format(abs(credits[["Undisaggregated reductions (Mt)"]][worst]), big.mark = ",")` million tonnes. The threshold account gave `r round(sum(credits[["Threshold rule reductions (Mt)"]][rule_pos]), 1)` million tonnes, `r round(sum(credits[["Threshold rule reductions (Mt)"]][rule_pos]) / sum(credits[["Disaggregated reductions (Mt)"]][split_pos]), 1)` times the reported account, because ordinary fire years raised its crediting level. The uncertainty deduction on the reported account ran from `r format(min(uncertainty[["Disaggregated deduction (%)"]], na.rm = TRUE), big.mark = ",")` to `r format(max(uncertainty[["Disaggregated deduction (%)"]], na.rm = TRUE), big.mark = ",")` per cent. The Food and Agriculture Organization's fire emissions for Canada were reproduced from its method within `r round(100 * max(abs(repro_year$ratio - 1)))` per cent. A standard that accepted the disaggregation needed a stated record length and regrowth period. It also needed to exclude only the emissions above a background level and deduct uncertainty from gross emissions and removals.

## Prompt to paste

> Read `/Volumes/PortableSSD/Github/canada-emissions-disaggregated/05.tasks/2026-11-04-abstract-brief.md` and do what it says. Read every paper it lists in full first, then redraft the abstract of `01.manuscript/Manuscript.qmd` as a leading author in national greenhouse gas inventory and forest carbon accounting would write it, in the terminology, perspective and statistical terms of those papers, under every rule the brief sets. Keep every inline R expression. Change nothing but the abstract. Render in the background, report the count, and show me the rendered abstract in chat.
