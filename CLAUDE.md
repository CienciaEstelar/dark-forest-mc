# Dark Forest Monte Carlo — CLAUDE.md

## Qué es este proyecto

Simulación Monte Carlo del ciclo completo **detección → destrucción → silencio** de la hipótesis del Bosque Oscuro (solución a la Paradoja de Fermi). Target de publicación: International Journal of Astrobiology.

## Estructura del proyecto

```
bosque_oscuro/
├── sim/           # Motor de simulación
│   ├── sociologia.py    # Tipos de civilización y decisión de ataque
│   ├── dinamica.py      # Paso 5: dinámica Bosque Oscuro (event-driven + cKDTree)
│   ├── tecnologia.py    # Radio de detección (sigmoide) y prob. detección
│   ├── espacio.py       # Generación de posiciones galácticas (bulbo+disco+GHZ)
│   ├── tiempos.py       # Duraciones lognormal y análisis de coexistencia
│   ├── sensibilidad.py  # Sobol SALib sobre parámetros Drake
│   ├── validacion.py    # Integridad del DataFrame y benchmarks Drake
│   └── pipeline.py      # Orquestación completa del pipeline de simulación
├── analysis/      # Post-procesamiento
│   ├── destruccion.py   # Estadísticas de destrucción post-Paso5
│   ├── ghz.py           # Análisis de la Zona Galáctica Habitable
│   ├── vecino.py        # KDTree 3D: distancia al vecino más cercano
│   ├── robustez.py      # Multi-seed: CV de métricas clave
│   └── narrativa_llm.py # Narrativa Gemini/OpenAI (NO incluir en paper)
├── common/
│   ├── config.py        # Parametros dataclass — todos los parámetros aquí
│   ├── io_utils.py      # Logger, ensure_structure, save_*
│   └── tipos.py         # Type aliases
├── cli/
│   ├── sim_main.py      # Entrada CLI para la simulación
│   └── analyze_main.py  # Entrada CLI para el análisis
└── run_pipeline.py      # Orquestador: sim + análisis + LLM opcional
```

## Cómo ejecutar

Desde el directorio PADRE (`~/Escritorio/`):

```bash
python -m bosque_oscuro.run_pipeline \
    --outdir ./output_sim \
    --seed 42 \
    --analysis-outdir ./output_analisis \
    --no-sensitivity
```

Para escenario optimista (pesado):
```bash
python -m bosque_oscuro.run_pipeline \
    --outdir ./output_sim \
    --seed 42 \
    --full-optimistic \
    --analysis-outdir ./output_analisis
```

## Parámetros clave (common/config.py)

| Parámetro | Valor actual | Nota |
|-----------|-------------|------|
| `ghz_inner_radius` | 10,000 ly | Lineweaver 2004 (solo para análisis GHZ) |
| `ghz_outer_radius` | 30,000 ly | Lineweaver 2004 (solo para análisis GHZ) |
| `ghz_peak_radius` | 25,000 ly | Pico de habitabilidad (Lineweaver 2004) |
| `ghz_sigma` | 8,000 ly | Ancho gaussiano del perfil GHZ |
| `probabilidad_ghz` | 0.8 | Obsoleto — reemplazado por perfil continuo |
| `vida_media_extendida` | 1.43×10⁸ yr | Corregido (era 2×10⁵, producía 0% destrucciones) |
| `radio_max_realista` | 1,000 ly | Arbitrario, citar literatura |
| `umbral_amenaza` | 0.7 | Sin justificación teórica |
| `vida_media_civilizacion` | 10,000 yr | L de Drake (lognormal media) |
| `sensibilidad["N"]` | 512 | Sobol N=512 (5,120 evaluaciones) |

## Literatura clave a citar

- Liu Cixin (2008) — "El problema de los tres cuerpos" (Bosque Oscuro)
- Forgan (2009) — Monte Carlo galáctico base (IJA)
- De Vladar (2013) — Game theory para civilizaciones
- Došović et al. (2019) — Autómata celular 1D
- Carroll-Nellenback et al. (2019) — Movimiento estelar
- Lineweaver et al. (2004) — GHZ boundaries
- Drake (1961) — Ecuación Drake original

## Estado del proyecto (2026-05-10)

### Fixes históricos (mayo 6-8)
- [x] FIX 1-4 + MEJORA 1-5 + FIX A-C + OPT 1-2 + MANT 1-3
- [x] PAPER 1-2 + FIX-PAPER F1, F3, F4, 2.4, 2.5
- [x] Escenario optimista multi-seed (10 seeds, cap=10,000)
- [x] control_multiseed.py creado (infraestructura, no ejecutado)

### Roadmap de corrección 2026-05-10 (3 fases, ~15 fixes)

**FASE 1 — FATALES:**
- [x] **FIX 1.1: Sobol N=512 re-ejecutado** — 6,144 evaluaciones, 5 parámetros, output guardado en `sobol_bosque_oscuro_N512.json`. S1 ∈ [-0.06, 0.06], ST ∈ [0.90, 1.01], CV=67.4%
- [x] **FIX 1.2: control_multiseed ejecutado** — Δr = +0.007 ± 0.066 (0.1σ). DF no distinguible de geometría ZGH en régimen pesimista
- [x] **FIX 1.3: decision_ataque corregido** — `min(1.0, ...)` añadido en sociologia.py:91
- [x] **FIX 1.4: d₀=100 al justificado** — citas Loeb 2007 + Forgan & Nichol 2011 en §2.3
- [x] **FIX 1.5: análisis sobre activas (n=385)** — analyze_main.py corregido, resumen_analisis.json regenerado. KS p=4.89×10⁻¹⁰ (antes 10⁻⁴² con n=440)

**FASE 2 — MAYORES:**
- [x] **FIX 2.1: L vs L_ext documentado** — §2.4 reescrito con dos escalas temporales
- [x] **FIX 2.2: Nota altura disco** — añadida en §5 (escala 300 al vs ~1000 al real)
- [x] **FIX 2.3: Seeds sincronizadas** — control_multiseed.py usa mismas 10 seeds que multiseed.py
- [x] **FIX 2.4: Factory function** — `sim/factory.py:crear_catalogo()` creada. 6 archivos refactorizados. ~160 líneas duplicadas eliminadas. Tests: 5/5.
- [x] **FIX 2.5: Versión inglesa marcada obsoleta** — advertencia en dark_forest_paper.tex
- [x] **FIX 2.6: Sobol 5 params en Tabla 2** — d₀_atenuacion incluido. Valores reales N=512.
- [x] **FIX 2.7: KS test corregido** — `alternative='greater'` en vecino.py

**FASE 3 — EDITORIAL:**
- [x] **3.1: Lenguaje suavizado** — Abstract y Conclusiones con tono condicional
- [x] **3.2: Framing como modelo de juguete** — párrafo añadido en §1
- [x] **3.3: Δr al frente** — §3.2.1 reescrito con resultados reales
- [x] **3.4: 3 figuras añadidas** — GHZ profile + destrucciones + vecino más cercano
- [x] **English abstract** — requerido por IJA
- [x] **Columna Δr en Tabla 1** — +0.007 ± 0.066 (0.1σ)
- [x] **Blindaje MNRAS** — mínimo efecto detectable Δr_min≈0.20, derivación explícita de L_ext, mismatch d₀/R_mem documentado
- [x] **Vectorización paso5** — `prob_deteccion_batch` + loop interno numpy. Speedup 3-5×. Tests 5/5.
- [x] **Control optimista** — 3 semillas, Δr_opt = −0.538 ± 0.020 (**27σ**). El DF IMPORTA en régimen denso.
- [x] **Sobol N=4096** — 49,152 eval, ST todos <1.0, S1_conf ±0.04. Convergencia alcanzada.
- [x] **Título reescrito** — "La Geometría Galáctica Domina sobre la Dinámica de Destrucción"
- [x] **Paper blindado** — 8pp, 3 figs. 3 revisiones superadas. Score final: **88/100** (Aceptar con correcciones mínimas)
- [x] **Robustizado** — 50 semillas pesimista (CV=10.1%), t-Student Δr_opt (IC 95% t₂), vectorización §2.6, robustez memoria verificada
- [x] **Consistencia editorial** — N=4,096 unificado (10 ocurrencias), r=1.43 unificado, sin frases duplicadas
- [x] **5 revisiones superadas** — 58→80→88→86→89→90→**96/100 (ACEPTAR SIN CAMBIOS)**
- [x] **Premortem aplicado** — título "Del Silencio a la Concentración", predicción observable SKA/WISE en §5, Dockerfile
- [ ] Comparación cuantitativa con Forgan 2009 (futuro)
- [ ] Versión en inglés del paper (futuro)

### Archivos creados/modificados (15 archivos)
- `sim/factory.py` — NUEVO
- `sim/sociologia.py` — FIX 1.3
- `sim/pipeline.py` — refactorizado (factory)
- `sim/sensibilidad.py` — refactorizado (factory)
- `analysis/vecino.py` — FIX 2.7
- `cli/analyze_main.py` — FIX 1.5
- `control_multiseed.py` — FIX 2.3 + refactor
- `multiseed.py` — refactorizado (factory)
- `multiseed_optimista.py` — refactorizado (factory)
- `tests/test_regression.py` — refactorizado (factory)
- `dark_forest_paper.tex` — marcado obsoleto
- `dark_forest_paper_es.tex` — 8 secciones actualizadas + 3 figuras + English abstract
- `ROADMAP_CORRECCION.md` — NUEVO (registro completo)
- `output_sim/sensibilidad/sobol_bosque_oscuro_N512.json` — NUEVO (N=512, 5 params, 6,144 eval)
- `output_sim/sensibilidad/sobol_bosque_oscuro_N4096.json` — NUEVO (N=4096, 49,152 eval, ST<1)
- `output_control/control_multiseed_results.json` — NUEVO (Δr pesimista)
- `output_control/control_optimista_3seeds.json` — NUEVO (Δr optimista, 27σ)

### Verificación
- Tests regresión: 5/5 ✅ (fixtures actualizados post-vectorización)
- PDF compilado: 0 errores, 1.7 MB, 7 páginas, 3 figuras, solo abstract español

---

## Estado para submission IJA

**Fecha: 10 mayo 2026**
**Estado: BLINDADO — 3 revisiones superadas, Δr_opt = −0.54 (27σ), Sobol convergido**

### Resultados definitivos

**Pesimista (N=440, 10 seeds DF + 10 seeds control, vectorizado):**
- Destruidas: 69.6 ± 5.4 (15.8% ± 1.2%)
- Dist. vecino (activas): 1837 ± 52 al
- Ratio obs/Poisson: 1.42 ± 0.04
- KS p-valor: 4.89×10⁻¹⁰ (seed 42, n=385 activas)
- **Δr_pes = +0.007 ± 0.066 (0.1σ)** — DF indistinguible de geometría ZGH
- Mínimo efecto detectable: Δr_min ≈ 0.20 a 3σ

**Optimista (N=10,000 cap, 10 seeds DF + 3 seeds control):**
- Destruidas: 8,583 ± 22 (85.8% ± 0.2%)
- Dist. vecino (activas): 478 ± 17 al
- Ratio obs/Poisson: 0.578 ± 0.020
- KS p-valor: < 2.2×10⁻³⁰⁸ (underflow float64)
- **Δr_opt = −0.538 ± 0.020 (27σ)** — DF MASIVO, concentra supervivientes
- r_obs/P control (sin DF): 1.117 ± 0.001 → el DF reduce el cociente en 0.54 unidades

**Sobol (N=4096, 49,152 eval, 5 params):**
- S1 ∈ [−0.016, 0.067] con ±0.04 CI
- ST ∈ [0.912, 0.980] — **todos < 1.0, convergencia alcanzada**
- f_agresivo muestra el mayor S1 = 0.067 (1.5σ de cero)
- CV = 68%. Sin parámetro dominante. Interacciones de alto orden controlan el modelo.

### Transición de régimen confirmada
| Régimen | Δr | Significancia | Interpretación |
|---------|-----|---------------|----------------|
| Baja densidad (N=440) | ≈ 0 | 0.1σ | DF irrelevante, ZGH domina |
| Alta densidad (N=10,000) | −0.54 | **27σ** | DF DOMINA, concentración masiva |

### Pendiente técnico
- [x] Vectorización paso5 — `prob_deteccion_batch` + loop interno numpy. Speedup 3-5×
- [x] Control optimista ejecutado (3 seeds, viable gracias a vectorización)
- [x] Sobol N=4096 convergido
- [ ] Comparación cuantitativa con Forgan 2009 (futuro)
- [ ] Versión en inglés del paper (futuro)
- [ ] Barrido Nc ∈ [10⁴, 10⁵, 10⁶] para verificar convergencia del cociente (futuro)

### Bibliografía verificada
- radio_max_realista = 1000 ly → Troitskij 1989, Loeb & Zaldarriaga 2007
- d₀ = 100 al → Loeb & Zaldarriaga 2007; Forgan & Nichol 2011
- vida_media_extendida = 1.43e8 → Sandberg et al. 2018 (parámetro de viabilidad, calibrado)
- umbral_amenaza = 0.7 → parámetro libre, Sobol S1=−0.016±0.042
- ne = 0.22 → Fressin et al. 2013, ApJ 766, 81
- Adams & Mann 2023 y Kučera & Špiljak 2024 → ALUCINACIONES, NO CITAR
