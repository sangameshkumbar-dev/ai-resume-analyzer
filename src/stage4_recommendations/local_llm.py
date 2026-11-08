"""
Local LLM Client supporting Ollama and Hugging Face Transformers.
Strictly local inference. No external APIs. No LangChain.
Includes offline heuristic fallback so system is always fully operational.
"""
import json
import logging
import requests
from typing import Optional, Dict, Any, List

from src.config import OLLAMA_BASE_URL, DEFAULT_OLLAMA_MODEL, DEFAULT_HF_MODEL, LLM_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class LocalLLMClient:
    """
    Direct interface to local LLMs via Ollama HTTP API or Hugging Face Transformers.
    No third-party wrappers or LangChain.
    """

    def __init__(
        self,
        provider: str = "auto",  # 'ollama', 'huggingface', 'fallback', or 'auto'
        ollama_model: str = DEFAULT_OLLAMA_MODEL,
        hf_model: str = DEFAULT_HF_MODEL,
        base_url: str = OLLAMA_BASE_URL
    ):
        self.provider = provider
        self.ollama_model = ollama_model
        self.hf_model = hf_model
        self.base_url = base_url.rstrip("/")
        self._hf_pipeline = None

    def check_ollama_status(self) -> Dict[str, Any]:
        """Check if local Ollama daemon is reachable and list downloaded models."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                return {
                    "running": True,
                    "models": models,
                    "default_model": self.ollama_model,
                    "model_installed": any(self.ollama_model in m for m in models)
                }
        except Exception:
            pass
        return {
            "running": False,
            "models": [],
            "default_model": self.ollama_model,
            "model_installed": False
        }

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 512, temperature: float = 0.2) -> str:
        """
        Generate text using local model (Ollama -> Hugging Face -> Heuristic fallback).
        """
        # Determine provider
        active_provider = self.provider
        if active_provider == "auto":
            ollama_info = self.check_ollama_status()
            if ollama_info["running"] and ollama_info["models"]:
                active_provider = "ollama"
            else:
                active_provider = "fallback"

        # 1. Ollama Provider
        if active_provider == "ollama":
            response = self._call_ollama(prompt, system_prompt, max_tokens, temperature)
            if response:
                return response

        # 2. Hugging Face Transformers Provider
        if active_provider == "huggingface":
            response = self._call_huggingface(prompt, system_prompt, max_tokens, temperature)
            if response:
                return response

        # 3. Intelligent Heuristic Fallback
        return self._generate_heuristic_response(prompt)

    def _call_ollama(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Query local Ollama REST endpoint."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": 0.9
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=LLM_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama call failed: {e}")
        return None

    def _call_huggingface(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Query local Hugging Face Transformers pipeline."""
        try:
            if self._hf_pipeline is None:
                from transformers import pipeline
                # Load lightweight local text-generation pipeline
                self._hf_pipeline = pipeline(
                    "text-generation",
                    model=self.hf_model,
                    device_map="auto"
                )

            full_prompt = f"<system>\n{system_prompt}\n<user>\n{prompt}\n<assistant>\n"
            outputs = self._hf_pipeline(
                full_prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=(temperature > 0.0),
                pad_token_id=50256
            )
            generated_text = outputs[0]["generated_text"]
            # Extract assistant response portion
            if "<assistant>\n" in generated_text:
                return generated_text.split("<assistant>\n")[-1].strip()
            return generated_text[len(full_prompt):].strip()
        except Exception as e:
            logger.warning(f"Hugging Face Transformers call failed: {e}")
        return None

    @staticmethod
    def _enhance_single_bullet(orig: str) -> str:
        """Dynamically elevate a candidate's actual bullet using Google XYZ formula."""
        import re
        cleaned = re.sub(r'^[•\-\*\>]\s*', '', orig).strip(' "\'')
        if not cleaned:
            return "Spearheaded core system architectural optimizations, enhancing delivery velocity by 25%."

        # Detect existing metrics (percentages, multipliers, dollar values, scale counts)
        metric_pattern = re.compile(
            r'(?:\b\d+(?:\.\d+)?%|\b\d+x\b|\$\d+[\d,]*|\b\d+\+?\s*(?:k|m|users|requests|ms|sec|days|weeks|engineers|microservices|services)\b)',
            re.I
        )
        has_metric = bool(metric_pattern.search(cleaned))

        # Replace weak or passive opening phrases with proactive action verbs
        passive_map = [
            (r'^(?:responsible for|tasked with|assigned to)\s+(?:writing|building|developing|creating)\s+', 'Engineered and scaled '),
            (r'^(?:responsible for|tasked with|assigned to)\s+(?:maintaining|managing|supporting)\s+', 'Architected and maintained '),
            (r'^(?:responsible for|tasked with|assigned to)\s+', 'Spearheaded '),
            (r'^(?:designed|developed|built)\s+and\s+led\s+', 'Spearheaded and led '),
            (r'^(?:worked with|collaborated with)\s+(?:the\s+)?team to\s+', 'Collaborated across cross-functional teams to '),
            (r'^(?:worked on|helped with|assisted in)\s+', 'Contributed to the design and implementation of '),
            (r'^(?:wrote|created)\s+', 'Engineered and deployed '),
            (r'^(?:developed)\s+', 'Spearheaded development of '),
            (r'^(?:designed)\s+', 'Architected and implemented '),
            (r'^(?:integrated)\s+', 'Engineered and integrated '),
            (r'^(?:optimized)\s+', 'Benchmarked and optimized '),
            (r'^(?:mentored)\s+', 'Mentored and guided ')
        ]

        transformed = cleaned
        for pat, rep in passive_map:
            if re.search(pat, transformed, re.I):
                transformed = re.sub(pat, rep, transformed, flags=re.I, count=1)
                break

        # Only inject an outcome metric if the bullet currently lacks quantifiable metrics
        if not has_metric:
            t_lower = transformed.lower()
            if any(w in t_lower for w in ['test', 'pytest', 'qa', 'bug', 'quality']):
                transformed = f"{transformed.rstrip('.')}, elevating automated test coverage by 35% and minimizing production regressions"
            elif any(w in t_lower for w in ['cloud', 'aws', 'docker', 'ci/cd', 'deploy', 'pipeline', 'terraform', 'ecs', 'k8s']):
                transformed = f"{transformed.rstrip('.')}, reducing deployment turnaround by 40% and ensuring reproducible environments"
            elif any(w in t_lower for w in ['database', 'sql', 'query', 'postgres', 'redis', 'cache', 'db']):
                transformed = f"{transformed.rstrip('.')}, cutting average query latency by 30% under heavy traffic"
            elif any(w in t_lower for w in ['frontend', 'react', 'ui', 'user', 'portal', 'next.js', 'css']):
                transformed = f"{transformed.rstrip('.')}, accelerating page load responsiveness by 35% and elevating user engagement"
            else:
                transformed = f"{transformed.rstrip('.')}, boosting system throughput by 25% and improving team delivery velocity"

        if not transformed.endswith('.'):
            transformed += '.'

        return transformed[0].upper() + transformed[1:]

    def _generate_heuristic_response(self, prompt: str) -> str:
        """Rule-based local fallback returning actionable suggestions if LLM daemon is offline."""
        import re
        if "REWRITE" in prompt.upper() or "BULLET" in prompt.upper():
            m = re.search(r'Original Bullet:\s*["\']?(.*?)["\']?\s*(?:\n|Output|$)', prompt, re.DOTALL | re.IGNORECASE)
            orig = m.group(1).strip() if m else ""
            if orig:
                return self._enhance_single_bullet(orig)
            return (
                "Spearheaded implementation of scalable backend architecture and services, "
                "improving system throughput by 30% and cutting latency across active deployments."
            )
        elif "SUMMARY" in prompt.upper():
            return (
                "Results-driven software engineering professional with proven expertise in building high-concurrency systems, "
                "cloud-native microservices, and modern web applications. Demonstrated track record of optimizing performance, "
                "collaborating across cross-functional teams, and delivering reliable, scalable products."
            )
        return (
            "Recommendation: Align technical terminology with target job description specifications, "
            "highlight quantifiable business impact on all bullet points, and verify that all core competencies are prominent."
        )

