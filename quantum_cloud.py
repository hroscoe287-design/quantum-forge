from __future__ import annotations

import os
import time
from typing import Any

def config() -> dict[str, Any]:
    return {
        "enabled": os.getenv("QUANTUM_HARDWARE_ENABLED", "false").lower() in {"1","true","yes","on"},
        "provider": os.getenv("QUANTUM_PROVIDER", "ibm").lower(),
        "backend": os.getenv("IBM_QUANTUM_BACKEND", "ibm_brisbane"),
        "instance": os.getenv("IBM_QUANTUM_INSTANCE", "").strip(),
        "shots": max(1, int(os.getenv("QUANTUM_SHOTS", "128"))),
    }

def status() -> dict[str, Any]:
    cfg = config()
    if cfg["provider"] != "ibm":
        return {"configured": False, "connected": False, "provider": cfg["provider"],
                "message": "Provider adapter is not enabled yet."}
    token = os.getenv("IBM_QUANTUM_TOKEN", "").strip()
    configured = bool(token and cfg["enabled"])
    if not token:
        return {"configured": False, "connected": False, "provider": "ibm",
                "backend": cfg["backend"], "message": "IBM_QUANTUM_TOKEN is not configured."}
    if not cfg["enabled"]:
        return {"configured": True, "connected": False, "provider": "ibm",
                "backend": cfg["backend"], "message": "Credentials found; hardware execution is disabled."}
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        kwargs = {"channel": "ibm_quantum_platform", "token": token}
        if cfg["instance"]:
            kwargs["instance"] = cfg["instance"]
        service = QiskitRuntimeService(**kwargs)
        backend = service.backend(cfg["backend"])
        return {"configured": configured, "connected": True, "provider": "ibm",
                "backend": backend.name, "message": "IBM Quantum backend is reachable."}
    except Exception as exc:
        return {"configured": configured, "connected": False, "provider": "ibm",
                "backend": cfg["backend"], "message": f"Quantum connection error: {type(exc).__name__}: {exc}"}

def submit_probe(label: str) -> dict[str, Any]:
    cfg = config()
    if not cfg["enabled"]:
        return {"submitted": False, "reason": "Hardware execution is disabled."}
    if cfg["provider"] != "ibm":
        return {"submitted": False, "reason": f"Unsupported provider: {cfg['provider']}"}
    token = os.getenv("IBM_QUANTUM_TOKEN", "").strip()
    if not token:
        return {"submitted": False, "reason": "IBM_QUANTUM_TOKEN is missing."}
    try:
        from qiskit import QuantumCircuit
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
        kwargs = {"channel": "ibm_quantum_platform", "token": token}
        if cfg["instance"]:
            kwargs["instance"] = cfg["instance"]
        service = QiskitRuntimeService(**kwargs)
        backend = service.backend(cfg["backend"])
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure_all()
        sampler = Sampler(mode=backend)
        job = sampler.run([circuit], shots=cfg["shots"])
        return {
            "submitted": True,
            "provider": "ibm",
            "backend": backend.name,
            "job_id": str(job.job_id()),
            "label": label[:160],
            "shots": cfg["shots"],
            "submitted_at": time.time(),
            "note": "Bell-state probe submitted to real quantum hardware; result may remain queued."
        }
    except Exception as exc:
        return {"submitted": False, "reason": f"{type(exc).__name__}: {exc}"}

def job_status(job_id: str) -> dict[str, Any]:
    token = os.getenv("IBM_QUANTUM_TOKEN", "").strip()
    if not token:
        return {"ok": False, "message": "IBM_QUANTUM_TOKEN is missing."}
    cfg = config()
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        kwargs = {"channel": "ibm_quantum_platform", "token": token}
        if cfg["instance"]:
            kwargs["instance"] = cfg["instance"]
        service = QiskitRuntimeService(**kwargs)
        job = service.job(job_id)
        out = {"ok": True, "job_id": job_id, "status": str(job.status())}
        if str(job.status()).upper() in {"DONE", "ERROR", "CANCELLED"}:
            try:
                result = job.result()
                out["result_available"] = True
                out["result_summary"] = str(result)[:4000]
            except Exception as exc:
                out["result_available"] = False
                out["result_error"] = str(exc)[:500]
        return out
    except Exception as exc:
        return {"ok": False, "job_id": job_id, "message": f"{type(exc).__name__}: {exc}"}
