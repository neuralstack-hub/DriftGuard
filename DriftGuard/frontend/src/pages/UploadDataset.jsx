import React, { useState } from "react";
import { api } from "../api/client";

export default function UploadDataset({ onRefresh, onNavigate }) {
  const [file, setFile] = useState(null);
  const [inspection, setInspection] = useState(null);
  const [datasetName, setDatasetName] = useState("");
  const [targetColumn, setTargetColumn] = useState("");
  const [selectedFeatures, setSelectedFeatures] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleFileChange = async (e) => {
    const picked = e.target.files?.[0];
    if (!picked) return;
    setFile(picked);
    setDatasetName(picked.name.replace(/\.csv$/i, ""));
    setMessage("");
    setError("");
    setBusy(true);
    try {
      const info = await api.inspectDataset(picked);
      setInspection(info);
      const numericCols = info.columns.filter((c) => c.dtype === "numeric").map((c) => c.name);
      const defaultTarget = numericCols[numericCols.length - 1] || info.columns[info.columns.length - 1]?.name || "";
      setTargetColumn(defaultTarget);
      setSelectedFeatures(
        info.columns.map((c) => c.name).filter((name) => name !== defaultTarget)
      );
    } catch (err) {
      setError(err.message);
      setInspection(null);
    } finally {
      setBusy(false);
    }
  };

  const toggleFeature = (colName) => {
    setSelectedFeatures((prev) =>
      prev.includes(colName) ? prev.filter((c) => c !== colName) : [...prev, colName]
    );
  };

  const handleTargetChange = (newTarget) => {
    setTargetColumn(newTarget);
    setSelectedFeatures((prev) => prev.filter((c) => c !== newTarget));
  };

  const handleTrain = async (e) => {
    e.preventDefault();
    if (!file || !targetColumn || selectedFeatures.length === 0) {
      setError("Please select a CSV file, a numeric target column, and at least one feature.");
      return;
    }
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const res = await api.uploadAndTrainDataset({
        file,
        datasetName: datasetName || file.name,
        targetColumn,
        selectedFeatures,
      });
      setMessage(
        `Trained ${res.model.version} on "${res.schema.dataset_name}" (${res.splits.total_clean_rows} rows) — RMSE: ${res.model.metrics.rmse}, R²: ${res.model.metrics.r2}`
      );
      await onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Upload Custom Dataset</h2>
        <p className="text-sm text-slate-500">
          Onboard any labelled CSV dataset, choose your target &amp; feature columns, and train a monitored RandomForestRegressor
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-5">
        <div>
          <label className="block text-sm font-semibold text-slate-800 mb-2">
            1. Select Labelled CSV File
          </label>
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
          />
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-sm text-rose-700">
            {error}
          </div>
        )}

        {message && (
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-sm text-emerald-800 flex items-center justify-between gap-4">
            <span>{message}</span>
            <button
              onClick={() => onNavigate("overview")}
              className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium"
            >
              View Overview
            </button>
          </div>
        )}

        {inspection && (
          <form onSubmit={handleTrain} className="space-y-5 pt-3 border-t border-slate-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="text-slate-700 font-medium">Dataset Name</span>
                <input
                  type="text"
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  required
                  className="px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900"
                />
              </label>

              <label className="flex flex-col gap-1.5 text-sm">
                <span className="text-slate-700 font-medium">
                  Target Column (Numeric value to predict)
                </span>
                <select
                  value={targetColumn}
                  onChange={(e) => handleTargetChange(e.target.value)}
                  className="px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900"
                >
                  {inspection.columns
                    .filter((c) => c.dtype === "numeric")
                    .map((c) => (
                      <option key={c.name} value={c.name}>
                        {c.name} (numeric, {c.missing_count} missing)
                      </option>
                    ))}
                </select>
              </label>
            </div>

            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">
                2. Select Input Features ({selectedFeatures.length} selected · {inspection.row_count} total rows)
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5 max-h-60 overflow-y-auto p-3 rounded-lg bg-slate-50 border border-slate-200">
                {inspection.columns
                  .filter((c) => c.name !== targetColumn)
                  .map((col) => (
                    <label
                      key={col.name}
                      className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedFeatures.includes(col.name)}
                        onChange={() => toggleFeature(col.name)}
                        className="rounded accent-blue-600"
                      />
                      <span className="truncate">
                        {col.name}{" "}
                        <span className="text-slate-400">({col.dtype === "numeric" ? "num" : "cat"})</span>
                      </span>
                    </label>
                  ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={busy}
              className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-sm font-semibold text-white shadow-sm transition"
            >
              {busy ? "Preprocessing & Training..." : "Upload & Train Model"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
