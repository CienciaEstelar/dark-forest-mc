# Dark Forest Monte Carlo -- Simulacion del Bosque Oscuro

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![MNRAS](https://img.shields.io/badge/paper-MNRAS--ready-brightgreen)](https://mnras.oxfordjournals.org)
[![Zenodo](https://img.shields.io/badge/DOI-Zenodo--pending-orange)](https://zenodo.org)

**Español** (Chile 🇨🇱) abajo | **English** (UK 🇬🇧) below

---

## 🇨🇱 Espanol

Simulacion Monte Carlo del ciclo completo **deteccion -> destruccion -> silencio** de la hipotesis del Bosque Oscuro como solucion a la Paradoja de Fermi.

Target de publicacion: **International Journal of Astrobiology / MNRAS**.

### Caracteristicas principales

- **Motor N-body con cKDTree** para deteccion de vecinos y dinamica de destruccion
- **Sociologia de civilizaciones**: tipos agresivos, pasivos y ocultos con umbrales de amenaza
- **Zona Galactica Habitable (GHZ)**: perfil gaussiano continuo (Lineweaver et al. 2004) con corte entre 10-30 kly
- **Analisis de sensibilidad Sobol** (N=4096, 49,152 evaluaciones, 5 parametros Drake) -- convergencia alcanzada, ST < 1.0
- **Validacion multi-semilla**: 50 semillas en regimen pesimista, 3-10 en optimista, con CV de metricas clave
- **Vectorizacion x5**: `prob_deteccion_batch` + loop interno numpy en paso5
- **Paper cientifico completo** en espanol con `mn2e.cls` (formato MNRAS) -- 8pp, 3 figuras, English abstract
- **5 revisiones superadas** -- Score final: **96/100** (ACEPTAR SIN CAMBIOS)

### Estructura del proyecto

```
bosque_oscuro/
 sim/           Motor: sociologia, dinamica, tecnologia, espacio, tiempos, sensibilidad, pipeline, factory
 analysis/      Post-procesamiento: destruccion, GHZ, vecino mas cercano, robustez multi-seed
 common/        Config (dataclass con todos los parametros), I/O, tipos
 cli/           Entradas CLI: sim_main.py, analyze_main.py
 tests/         Tests de regresion (5/5 pasando)
run_pipeline.py     Orquestador: simulacion + analisis + LLM opcional
multiseed.py        Barrido multi-semilla pesimista (50 seeds)
control_multiseed.py Control: geometria ZGH pura sin Bosque Oscuro
mn2e.cls            Clase de documento MNRAS
dark_forest_paper_es.tex   Paper principal (espanol)
### Ejecucion rapida

```bash
source ~/anaconda3/bin/activate                 # Requerido: numpy, scipy, pandas, SALib
python -m bosque_oscuro.run_pipeline --outdir ./output_sim --seed 42
```

Escenario optimista (pesado, N=10,000 civilizaciones):
```bash
python -m bosque_oscuro.run_pipeline --outdir ./output_sim --seed 42 --full-optimistic
```

### Resultados clave

| Regimen | N | Destruidas | Delta-r | Sigma | Interpretacion |
|---------|---|------------|---------|-------|----------------|
| Pesimista | 440 | 69.6 +- 5.4 (15.8%) | +0.007 +- 0.066 | 0.1 | DF indistinguible de geometria ZGH |
| **Optimista** | **10,000** | **8,583 +- 22 (85.8%)** | **-0.54 +- 0.02** | **27** | **DF MASIVO -- concentra supervivientes** |

**Resultado principal**: en regimen de alta densidad, el Bosque Oscuro reduce el cociente
observado/Poisson en **Delta-r = -0.54** (27 sigma). El silencio observado es consistente con
Bosque Oscuro activo. En baja densidad, la geometria galactica (GHZ) domina la senal.

### Sobol -- sensibilidad global

| Parametro | S1 | ST |
|-----------|-----|-----|
| f_agresivo | 0.067 +- 0.04 | 0.912 +- 0.04 |
| d0_atenuacion | 0.021 +- 0.04 | 0.942 +- 0.04 |
| umbral_amenaza | -0.016 +- 0.04 | 0.947 +- 0.04 |
| radio_max | 0.034 +- 0.04 | 0.980 +- 0.04 |
| vida_media_ext | 0.046 +- 0.04 | 0.954 +- 0.04 |

ST < 1.0 en todos los parametros. Sin parametro dominante -- el modelo esta controlado
por interacciones de alto orden. CV = 68%. La fraccion de agresivos es el parametro
con mayor efecto de primer orden (1.5 sigma de cero).

### Parametros clave (common/config.py)

| Parametro | Valor | Referencia |
|-----------|-------|------------|
| `ghz_peak_radius` | 25,000 ly | Lineweaver et al. (2004) |
| `ghz_sigma` | 8,000 ly | Perfil gaussiano GHZ |
| `vida_media_civilizacion` | 10,000 yr | L de Drake (media lognormal) |
| `vida_media_extendida` | 1.43e8 yr | Calibrado (Sandberg et al. 2018) |
| `radio_max_realista` | 1,000 ly | Troitskij 1989; Loeb & Zaldarriaga 2007 |
| `d0` | 100 ly | Loeb & Zaldarriaga 2007; Forgan & Nichol 2011 |
| `umbral_amenaza` | 0.7 | Parametro libre (Sobol: S1=-0.016) |

---

## 🇬🇧 English

Monte Carlo simulation of the full **detection -> destruction -> silence** cycle of the Dark Forest
hypothesis as a solution to the Fermi Paradox.

Publication target: **International Journal of Astrobiology / MNRAS**.

### Key Features

- **N-body simulation engine** with cKDTree for neighbour detection and destruction dynamics
- **Civilisation sociology**: aggressive, passive, and hidden types with threat thresholds
- **Galactic Habitable Zone (GHZ)**: continuous Gaussian profile (Lineweaver et al. 2004), 10-30 kly
- **Sobol sensitivity analysis** (N=4096, 49,152 evaluations, 5 Drake parameters) -- ST < 1.0 for all
- **Multi-seed validation**: 50 seeds (pessimistic), 3-10 seeds (optimistic), CV on key metrics
- **5x vectorisation**: `prob_deteccion_batch` + inner numpy loop in step 5
- **Full scientific paper** (`mn2e.cls` MNRAS format, 8pp, 3 figures, English abstract)
- **5 reviews passed** -- Final score: **96/100** (ACCEPT WITHOUT CHANGES)

### Quick Start

```bash
source ~/anaconda3/bin/activate                 # Requires: numpy, scipy, pandas, SALib
python -m bosque_oscuro.run_pipeline --outdir ./output_sim --seed 42
```

Optimistic scenario (heavy, N=10,000 civilisations):
```bash
python -m bosque_oscuro.run_pipeline --outdir ./output_sim --seed 42 --full-optimistic
```

### Key Results

| Regime | N | Destroyed | Delta-r | Sigma | Interpretation |
|--------|---|-----------|---------|-------|----------------|
| Pessimistic | 440 | 69.6 +- 5.4 (15.8%) | +0.007 +- 0.066 | 0.1 | DF indistinguishable from GHZ geometry |
| **Optimistic** | **10,000** | **8,583 +- 22 (85.8%)** | **-0.54 +- 0.02** | **27** | **MASSIVE DF -- concentrates survivors** |

**Main result**: in the high-density regime, the Dark Forest reduces the observed-to-Poisson ratio
by **Delta-r = -0.54** (27 sigma). Observed silence is consistent with an active Dark Forest.
At low density, galactic geometry (GHZ) dominates the signal.

### Global Sensitivity (Sobol)

No single parameter dominates -- the model is controlled by high-order interactions.
CV = 68%. The aggressive fraction shows the largest first-order effect (1.5 sigma from zero).

---

## Referencias clave / Key References

| Reference | Topic |
|-----------|-------|
| Liu Cixin (2008) -- The Three-Body Problem | Dark Forest hypothesis (original concept) |
| Forgan (2009) -- IJA | Galactic Monte Carlo (methodological base) |
| Lineweaver et al. (2004) | Galactic Habitable Zone boundaries |
| Drake (1961) | Drake Equation |
| De Vladar (2013) | Game theory for civilisations |
| Carroll-Nellenback et al. (2019) | Stellar motion in galactic simulations |
| Sandberg et al. (2018) | Dissolving the Fermi Paradox (parameter calibration) |
| Loeb & Zaldarriaga (2007) | Eavesdropping on radio broadcasts |
| Troitskij (1989) | Radio detectability horizon |
| Forgan & Nichol (2011) | Failure of the Drake Equation (d0 baseline) |

---

## Citacion / Citation

Paper in preparation for MNRAS. Zenodo DOI pending.

```bibtex
@article{galaz2026darkforest,
  title={{Del Silencio a la Concentracion: la Hipotesis del Bosque Oscuro
          como Explicacion de la Paradoja de Fermi}},
  author={Galaz, Juan and others},
  journal={In preparation for MNRAS},
  year={2026}
}
```

---

*"El universo es un bosque oscuro. Cada civilizacion es un cazador armado,
acechando entre los arboles, tratando de no hacer ruido."* -- Liu Cixin

*"The universe is a dark forest. Every civilisation is an armed hunter,
stalking through the trees, trying to keep quiet."* -- Liu Cixin
