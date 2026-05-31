// hooks/useAgent.js
import { useState } from "react";

const API = import.meta.env.VITE_API_URL;

export function useAgent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeResume = async (resumeData) => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/agent/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(resumeData)
      });
      const data = await res.json();
      return data.data;
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const scoreATS = async (resume, jobDesc) => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/agent/ats-score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume, job_description: jobDesc })
      });
      const data = await res.json();
      return data.data;
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const fullPipeline = async (resume, jobDesc) => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/agent/full-pipeline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume, job_description: jobDesc })
      });
      const data = await res.json();
      return data.data;
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return { analyzeResume, scoreATS, fullPipeline, loading, error };
}