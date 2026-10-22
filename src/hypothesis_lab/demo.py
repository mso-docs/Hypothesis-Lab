"""Verified linked literature and synthetic observations, explicitly separated."""

from hypothesis_lab.models import Observation, Publication

HYPOTHESIS = (
    "Increasing temperatures are associated with more frequent extreme-heat events."
)
OBSERVATIONS = [
    Observation(experiment_id=f"synthetic-batch-{i + 1}", successes=k, trials=25)
    for i, k in enumerate([3, 4, 6, 7])
]
# Metadata snapshot retrieved from OpenAlex on 2026-10-22. No API request is
# needed to open the starter. Missing abstracts remain missing.
SOURCE_SNAPSHOT_DATE = "2026-10-22"
PUBLICATIONS = [
    Publication.model_validate(item)
    for item in [
        {
            "abstract": None,
            "authors": ["Erich Markus Fischer", "Sebastian Sippel", "Reto Knutti"],
            "doi": "https://doi.org/10.1038/s41558-021-01092-9",
            "id": "https://openalex.org/W3183552297",
            "provider": "OpenAlex",
            "title": "Increasing probability of record-shattering climate extremes",
            "url": "https://doi.org/10.1038/s41558-021-01092-9",
            "year": 2021,
        },
        {
            "abstract": "Climatic warming of about 0.5 ° C in the global mean since the 1970s has strongly "
            "increased the occurrence-probability of heat extremes on monthly to seasonal time "
            "scales. For the 21st century, climate models predict more substantial warming. Here "
            "we show that the multi-model mean of the CMIP5 (Coupled Model Intercomparison "
            "Project) climate models accurately reproduces the evolution over time and spatial "
            "patterns of the historically observed increase in monthly heat extremes. For the "
            "near-term (i.e., by 2040), the models predict a robust, several-fold increase in "
            "the frequency of such heat extremes, irrespective of the emission scenario. "
            "However, mitigation can strongly reduce the number of heat extremes by the second "
            "half of the 21st century. Unmitigated climate change causes most (>50%) continental "
            "regions to move to a new climatic regime with the coldest summer months by the end "
            "of the century substantially hotter than the hottest experienced today. We show "
            "that the land fraction experiencing extreme heat as a function of global mean "
            "temperature follows a simple cumulative distribution function, which depends only "
            "on natural variability and the level of spatial heterogeneity in the warming.",
            "authors": ["Dim Coumou", "Alexander Robinson"],
            "doi": "https://doi.org/10.1088/1748-9326/8/3/034018",
            "id": "https://openalex.org/W2101948993",
            "provider": "OpenAlex",
            "title": "Historic and future increase in the global land area affected by monthly heat extremes",
            "url": "https://doi.org/10.1088/1748-9326/8/3/034018",
            "year": 2013,
        },
        {
            "abstract": "Abstract. On 19 May 2016 the afternoon temperature reached 51.0 ºC in Phalodi in "
            "the northwest of India, a new record for the highest observed maximum temperature "
            "in India. The previous year, a widely-reported very lethal heat wave occurred in "
            "the southeast, in Andhra Pradesh and Telangana, killing thousands of people. In "
            "both cases it was widely assumed that the probability and severity of heat waves in "
            "India are increasing due to global warming, as they do in other parts of the world. "
            "However, we do not find positive trends in the highest maximum temperature of the "
            "year in most of India since the 1970s (except spurious trends due to missing data). "
            "Decadal variability cannot explain this, but both increased air pollution with "
            "aerosols blocking sunlight and increased irrigation leading to evaporative cooling "
            "have counteracted the effect of greenhouse gases up to now. Current climate models "
            "do not represent these processes well and hence cannot be used to attribute heat "
            "waves in this area. The health effects of heat are often described better by a "
            "combination of temperature and humidity, such as a heat index or wet bulb "
            "temperature. Due to the increase in humidity from irrigation and higher SSTs these "
            "indices have increased over the last decades even when extreme temperatures have "
            "not. The extreme air pollution also exacerbates the health impacts of heat. From a "
            "health impact point of view, the severity of heat waves has increased in India. For "
            "the next decades we expect the trend due to global warming to continue, but the "
            "cooling effect of aerosols to diminish as air quality controls are implemented. The "
            "expansion of irrigation will likely continue, though at a slower pace, mitigating "
            "this trend somewhat. Humidity will probably continue to rise. The combination will "
            "give a strong rise of the temperature of heat waves. The high humidity will make "
            "health effects worse, whereas decreased air pollution would decrease the impacts.",
            "authors": [
                "Geert Jan van Oldenborgh",
                "Sjoukje Yvette Philip",
                "Sarah Kew",
            ],
            "doi": "https://doi.org/10.5194/nhess-18-365-2018",
            "id": "https://openalex.org/W2597851810",
            "provider": "OpenAlex",
            "title": "Extreme heat in India and anthropogenic climate change",
            "url": "https://doi.org/10.5194/nhess-18-365-2018",
            "year": 2018,
        },
    ]
]

NOTES = """# Extreme heat · research notebook

## Research question
How should we evaluate the claim that warming is associated with more frequent extreme-heat events?

## Start here
1. Open hypothesis.md to read the research question and its scope.
2. Open literature (Literature) to inspect three real papers and follow their DOI links.
   Compare the global findings with the India study: region, metric, and confounders matter.
3. Open evidence.json (Evidence review) to inspect the verbatim abstract excerpts,
   assign classifications, and mark excerpts reviewed after checking their sources.
4. Open analysis.py (Bayesian analysis) and change the prior to inspect its effect
   on the posterior. The observation counts are synthetic, independent of the papers.
5. Use source-map to explore source relationships, then report.md to export your findings.
6. Save a named copy of your investigation, or choose New investigation to start your own.

## Demonstration data
The 100 eligible observations and 20 events are synthetic teaching data, not measurements
from the linked papers. Literature is qualitative context and never updates the model automatically.

## Method limitations
A Beta–Binomial model estimates a single event probability assuming independent trials
and a consistent threshold. It does not establish a trend or causation. Regional dependence,
changing baselines, humidity, and sampling design require a richer analysis.

## Source provenance
The bundled publication metadata was retrieved from OpenAlex on 22 October 2026.
A missing abstract is shown as unavailable. Review full papers before drawing conclusions.
"""
