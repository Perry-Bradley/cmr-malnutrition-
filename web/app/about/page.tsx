import { Card } from "@/components/Card";
import { DataBanner } from "@/components/DataBanner";

export const metadata = { title: "About — Cameroon Malnutrition Atlas" };

const SOURCES = [
  { name: "Cameroon Subnational DHS (5 rounds)",
    url:  "https://data.humdata.org/dataset/dhs-subnational-data-for-cameroon",
    why:  "Target variable (anthropometry) plus most features. 1991, 1998, 2004, 2011, 2018 rounds." },
  { name: "WHO Health Indicators (CMR)",
    url:  "https://data.humdata.org/dataset/who-data-for-cmr",
    why:  "National-level malaria, TB, NCD, WASH, health-systems indicators." },
  { name: "Cameroon Health Facilities (OSM)",
    url:  "https://data.humdata.org/dataset/hotosm_cmr_health_facilities",
    why:  "Downloaded but empty; we use the DHS health-facility-delivery share as the access proxy instead." },
  { name: "Cameroon Population Density",
    url:  "https://data.humdata.org/dataset/highresolutionpopulationdensitymaps-cmr",
    why:  "Downloaded; not used in this round of the pipeline." },
  { name: "geoBoundaries CMR ADM1",
    url:  "https://www.geoboundaries.org/api/current/gbOpen/CMR/ADM1/",
    why:  "Source of the GeoJSON used in the choropleth map." },
];

const FEATURES = [
  ["stunting_rate",                "Children under 5 stunted",                  "Anthropometry"],
  ["wasting_pct",                  "Children under 5 wasted",                   "Anthropometry"],
  ["underweight_pct",              "Children under 5 underweight",              "Anthropometry"],
  ["child_anemia_pct",             "Children with any anaemia",                 "Anemia"],
  ["women_secondary_plus_pct",     "Women with secondary+ education",           "Literacy"],
  ["women_literate_pct",           "Women who are literate",                    "Literacy"],
  ["improved_water_pct",           "Population using improved water source",    "Water"],
  ["improved_sanitation_pct",      "Population with improved sanitation",       "Toilet_Facilities"],
  ["antenatal_4plus_pct",          "Antenatal visits 4+",                       "MDGs"],
  ["antenatal_skilled_pct",        "Antenatal from skilled provider",           "Access_to_Health_Care"],
  ["skilled_birth_attendance_pct", "Skilled birth attendance",                  "Access_to_Health_Care"],
  ["health_facility_delivery_pct", "Health facility delivery (% of births)",    "Access_to_Health_Care"],
  ["health_insurance_any_pct",     "Any health insurance (100 - no insurance)", "Health_Insurance"],
  ["malaria_prevalence_pct",       "Malaria prevalence (RDT)",                  "Malaria_Parasitemia"],
  ["fertility_rate",               "Total fertility rate 15-49",                "DHS_Mobile"],
];

export default function AboutPage() {
  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">About this project</h1>
        <p className="mt-1 max-w-3xl text-zinc-600">
          A CEC 420 Data Mining course project at the University of Buea. The
          aim is to identify the strongest real drivers of child stunting in
          Cameroon and produce a ranked list of high-risk regions that a
          public-health programme could act on. Built end-to-end in Python
          (CRISP-DM pipeline) with this Next.js webapp as the front-end —
          including live client-side prediction.
        </p>
      </header>

      <DataBanner />

      <Card title="Project information">
        <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-[180px_1fr]">
          <dt className="text-zinc-500">Course</dt>          <dd className="text-zinc-800">CEC 420 — Data Mining</dd>
          <dt className="text-zinc-500">Institution</dt>     <dd className="text-zinc-800">University of Buea, College of Technology</dd>
          <dt className="text-zinc-500">Department</dt>      <dd className="text-zinc-800">Computer Engineering — Software Engineering</dd>
          <dt className="text-zinc-500">Author</dt>          <dd className="text-zinc-800">SEPO PERRY-BRADLEY DINGA</dd>
          <dt className="text-zinc-500">Matricule</dt>       <dd className="text-zinc-800">CT23A145</dd>
          <dt className="text-zinc-500">Academic year</dt>   <dd className="text-zinc-800">2025 / 2026</dd>
        </dl>
      </Card>

      <Card title="Methodology (CRISP-DM)">
        <ol className="list-decimal space-y-2 pl-5 text-sm text-zinc-700">
          <li><strong>Business Understanding</strong> — frame the problem as a targeting decision for a fixed nutrition budget.</li>
          <li><strong>Data Understanding</strong> — inventory the DHS+MICS CSVs for Cameroon; pick the indicator that best matches each feature.</li>
          <li><strong>Data Preparation</strong> — load each long-format CSV, filter to Region rows, pick the longest recall window where present, normalise region names (handle 1991/1998 mega-regions by broadcasting to their constituent modern regions, normalise French/English variants and mojibake), pivot, then outer-join into one wide table.</li>
          <li><strong>Modelling</strong> — four parallel mining techniques on the same real table:
            <ul className="mt-1 list-disc space-y-1 pl-5">
              <li><a className="underline decoration-zinc-300 hover:decoration-zinc-700" href="/regression">Regression</a> — 10 models compete on 5-fold CV.</li>
              <li><a className="underline decoration-zinc-300 hover:decoration-zinc-700" href="/classification">Classification</a> — predict the WHO band (low / medium / high / critical).</li>
              <li><a className="underline decoration-zinc-300 hover:decoration-zinc-700" href="/clustering">Clustering</a> — K-Means on standardised drivers; k chosen by silhouette.</li>
              <li><a className="underline decoration-zinc-300 hover:decoration-zinc-700" href="/forecasts">Forecasting</a> — per-region linear trend → 2026, 2028.</li>
            </ul>
          </li>
          <li><strong>Evaluation</strong> — 5-fold CV for regression + classification; <a className="underline decoration-zinc-300 hover:decoration-zinc-700" href="/hypotheses">hypothesis tests H1-H6</a> on the real series.</li>
          <li><strong>Deployment</strong> — serialised best model, ranked CSV, and a deployable linear/logistic/k-means bundle (`predictor.json`) that powers the live <a className="underline decoration-zinc-300 hover:decoration-zinc-700" href="/predict">/predict</a> page directly in the browser.</li>
        </ol>
      </Card>

      <Card title="Why 1991-2018 and not 2024?">
        <p className="text-sm text-zinc-700">
          Sub-national stunting data for Cameroon is published by household
          surveys (DHS, MICS), not by annual modelled estimates. The five
          rounds <strong>1991, 1998, 2004, 2011, 2018</strong> are the only public
          sub-national series for Cameroon. The next DHS-VI round was
          anticipated 2024 but had not been released at the time of this
          analysis. National-level WHO/UNICEF estimates exist through 2024
          but those are single national numbers, not 10 region rows — so
          they don&apos;t fit the per-region modelling framing.
          1991/1998 only published five mega-regions
          (e.g. &ldquo;Adamaoua/Nord/Extrême-Nord&rdquo;); we broadcast each mega
          value to its constituent modern regions to preserve the time series.
        </p>
      </Card>

      <Card title="Feature map (DHS indicator → analysis column)">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-zinc-500">
              <tr><th className="px-2 py-1.5">Column</th><th className="px-2 py-1.5">DHS Indicator</th><th className="px-2 py-1.5">Source CSV</th></tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {FEATURES.map(([col, ind, csv]) => (
                <tr key={col}>
                  <td className="px-2 py-1.5 font-mono text-xs text-zinc-700">{col}</td>
                  <td className="px-2 py-1.5 text-zinc-800">{ind}</td>
                  <td className="px-2 py-1.5 text-zinc-500">{csv}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Data sources">
        <ul className="grid gap-3 sm:grid-cols-2">
          {SOURCES.map((s) => (
            <li key={s.url} className="rounded-md border border-zinc-200 bg-zinc-50/50 p-3">
              <a className="font-medium text-zinc-900 hover:underline" href={s.url} target="_blank" rel="noopener noreferrer">
                {s.name}
              </a>
              <p className="mt-0.5 text-xs text-zinc-600">{s.why}</p>
            </li>
          ))}
        </ul>
      </Card>

      <Card title="Stack">
        <ul className="grid grid-cols-2 gap-2 text-sm text-zinc-700 sm:grid-cols-3">
          <li>Python 3.11 · pandas · numpy</li>
          <li>scikit-learn · XGBoost · LightGBM</li>
          <li>scipy · statsmodels · SHAP</li>
          <li>Jupyter for the analysis notebook</li>
          <li>Next.js 16 · React 19 · TypeScript</li>
          <li>Tailwind 4 · Recharts · react-simple-maps</li>
        </ul>
      </Card>
    </div>
  );
}
