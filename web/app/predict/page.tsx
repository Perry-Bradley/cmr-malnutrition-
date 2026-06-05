import Predictor from "@/components/Predictor";
import { getPredictor, getSubregional } from "@/lib/data";

export const metadata = { title: "Predict — Cameroon Malnutrition Atlas" };

export default async function PredictPage() {
  const [payload, subregions] = await Promise.all([getPredictor(), getSubregional()]);
  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          What-if predictor
        </h1>
        <p className="mt-1 max-w-3xl text-zinc-600">
          A live, browser-side prediction: enter the driver values for any
          hypothetical Cameroonian region and see the predicted child stunting
          rate, the WHO risk band probabilities, and the most similar real
          region-years from the DHS dataset. Inference runs entirely in your
          browser — no requests, no backend.
        </p>
      </header>
      <Predictor payload={payload} subregions={subregions} />
    </div>
  );
}
