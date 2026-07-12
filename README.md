# Dark Forest Monte Carlo -- Simulacion del Bosque Oscuro

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![MNRAS](https://img.shields.io/badge/paper-MNRAS--format-brightgreen)](https://mnras.oxfordjournals.org)
[![Zenodo](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20451754-blue)](https://doi.org/10.5281/zenodo.20451754)

**Español** (Chile 🇨🇱) abajo | **English** (UK 🇬🇧) below

---

## 🇨🇱 Español

Simulacion Monte Carlo del ciclo completo **deteccion -> destruccion -> silencio** de la hipotesis del Bosque Oscuro como solucion a la Paradoja de Fermi.

Target de publicacion: **International Journal of Astrobiology / MNRAS**.

> ⚠️ **Correccion v6 (julio 2026):** una auditoria posterior a las primeras revisiones detecto que el termino de falsos positivos (`p_fp`) actuaba como piso de deteccion a cualquier distancia, generando >96% de las destrucciones a distancias no fisicas e invirtiendo el signo del efecto espacial reportado. La v5 reportaba concentracion masiva (Delta-r=-0.54); el modelo corregido muestra dispersion modesta (Delta-r=+0.060). Ver `docs/ROADMAP_CORRECCION.md` (Revision 6) y el Apendice B del paper para el historial completo.

### Caracteristicas principales

- **Motor N-body con cKDTree** para deteccion de vecinos y dinamica de destruccion
- **Condicion de causalidad**: ninguna civilizacion es detectable antes de que su señal, viajando a `c`, alcance al observador
- **Sociologia de civilizaciones**: tipos agresivos, pasivos y ocultos con umbrales de amenaza
- **Zona Galactica Habitable (GHZ)**: perfil gaussiano continuo (Lineweaver et al. 2004) con corte entre 10-30 kly
- **Analisis de sensibilidad de un factor sobre `p_fp`**: compara el modelo v5, sin piso de falsos positivos, y el modelo final (ver Resultados)
- **Validacion multi-semilla**: 50 semillas DF + 50 de control apareadas en regimen pesimista, 10 DF + 3 de control en optimista
- **Vectorizacion x5**: `prob_deteccion_batch` + loop interno numpy en paso5
- **Paper cientifico completo** en espanol con `mn2e.cls` (formato MNRAS), una columna, referencias con backref
- **Suite de tests**: regresion (5 semillas) + propiedades fisicas del canal de deteccion (ausencia de piso, causalidad)

### Estructura del proyecto

```
dark-forest-mc/
├── sim/           Motor: sociologia, dinamica, tecnologia, espacio, tiempos, sensibilidad, pipeline, factory
├── analysis/      Post-procesamiento: destruccion, GHZ, vecino mas cercano, robustez multi-seed
├── common/        Config (dataclass con todos los parametros), I/O, tipos
├── cli/           Entradas CLI: sim_main.py, analyze_main.py
├── tests/         test_regression.py (5/5) + test_fisica_deteccion.py (propiedades del canal)
├── scripts/       Orquestadores: run_pipeline.py, compile_paper.py, control_multiseed.py
├── docs/          ROADMAP_CORRECCION.md (trazabilidad completa) + resultados_definitivos_fix_pfp_causal.json
├── paper/archive/ Versiones descartadas del paper (obsoletas o alternativas)
├── multiseed.py   Barrido multi-semilla pesimista (50 seeds)
├── mn2e.cls       Clase de documento MNRAS
└── dark_forest_paper_es.tex   Paper principal (espanol)
```

### Ejecucion rapida

```bash
source ~/anaconda3/bin/activate                 # Requerido: numpy, scipy, pandas, SALib
python scripts/run_pipeline.py --outdir ./output_sim --seed 42
```

Escenario optimista (pesado, N=10,000 civilizaciones):
```bash
python scripts/run_pipeline.py --outdir ./output_sim --seed 42 --full-optimistic
```

### Resultados clave (modelo corregido v6)

| Regimen | N | Destruidas | Delta-r | Sigma | Interpretacion |
|---------|---|------------|---------|-------|----------------|
| Pesimista | 440 | 2.6 +- 1.5 (0.59%) | +0.0045 +- 0.0032 | ~1 | DF indistinguible de geometria ZGH |
| **Optimista** | **10,000** | **2,287 +- 46 (22.9%)** | **+0.060 +- 0.008** | **7.8** | **DF dispersa a los supervivientes** |

**Resultado principal**: el efecto espacial neto del Bosque Oscuro es una **dispersion** modesta de los
supervivientes que crece monotonicamente con la densidad poblacional, no la concentracion masiva
reportada por la version previa del modelo. Las destrucciones son locales (eliminan preferentemente
al vecino mas cercano), lo que desplaza la distribucion de distancias hacia valores mayores.

### Sensibilidad -- el rol dominante de p_fp

| Configuracion | Tasa pesimista | Tasa optimista | Delta-r optimista |
|----------------|----------------|----------------|--------------------|
| v5 (p_fp aditivo) | 16.1% | 85.8% | -0.538 |
| sin piso p_fp | 0.69% | 23.0% | +0.061 |
| final (+ causalidad) | 0.59% | 22.9% | +0.060 |

`p_fp` era el parametro individual dominante del modelo v5 -- su eliminacion cambia las tasas de
destruccion en factores de 4-27x e invierte el signo del efecto espacial diferencial. El analisis de
Sobol de la v5 (que no incluia `p_fp` entre sus factores) reportaba correctamente que "ningun parametro
dominaba", una conclusion valida solo dentro de ese subespacio de parametros. Un Sobol del modelo
corregido, con replicas por punto y `p_fp`/`p_fn` incluidos, queda declarado como trabajo futuro.

### Parametros clave (common/config.py)

| Parametro | Valor | Referencia |
|-----------|-------|------------|
| `ghz_peak_radius` | 25,000 ly | Lineweaver et al. (2004) |
| `ghz_sigma` | 8,000 ly | Perfil gaussiano GHZ |
| `vida_media_civilizacion` | 10,000 yr | L de Drake (media lognormal) |
| `vida_media_extendida` | 1.43e8 yr | Calibrado (Sandberg et al. 2018) |
| `radio_max_realista` | 1,000 ly | Troitskij 1989; Loeb & Zaldarriaga 2007 |
| `d0` | 100 ly | Loeb & Zaldarriaga 2007; Forgan & Nichol 2011 |
| `umbral_amenaza` | 0.7 | Parametro libre |
| `p_fp` | 0.01* | Libre; *desde v6 no participa del canal letal (ver Apendice B) |

---

## 🇬🇧 English

Monte Carlo simulation of the full **detection -> destruction -> silence** cycle of the Dark Forest
hypothesis as a solution to the Fermi Paradox.

Publication target: **International Journal of Astrobiology / MNRAS**.

> ⚠️ **v6 correction (July 2026):** an audit following the initial review rounds found that the
> false-positive term (`p_fp`) acted as a detection floor at any distance, generating >96% of
> destructions at non-physical distances and inverting the sign of the reported spatial effect.
> v5 reported massive concentration (Delta-r=-0.54); the corrected model shows modest dispersion
> (Delta-r=+0.060). See `docs/ROADMAP_CORRECCION.md` (Revision 6) and Appendix B of the paper for
> the full correction history.

### Key Features

- **N-body simulation engine** with cKDTree for neighbour detection and destruction dynamics
- **Causality condition**: no civilisation is detectable before its signal, travelling at `c`, reaches the observer
- **Civilisation sociology**: aggressive, passive, and hidden types with threat thresholds
- **Galactic Habitable Zone (GHZ)**: continuous Gaussian profile (Lineweaver et al. 2004), 10-30 kly
- **One-factor sensitivity analysis on `p_fp`**: compares the v5 model, the model without the false-positive floor, and the final model (see Results)
- **Multi-seed validation**: 50 DF seeds + 50 paired controls (pessimistic), 10 DF + 3 controls (optimistic)
- **5x vectorisation**: `prob_deteccion_batch` + inner numpy loop in step 5
- **Full scientific paper** (`mn2e.cls` MNRAS format, single column, backref-enabled bibliography)
- **Test suite**: regression (5 seeds) + physical properties of the detection channel (no floor, causality)

### Quick Start

```bash
source ~/anaconda3/bin/activate                 # Requires: numpy, scipy, pandas, SALib
python scripts/run_pipeline.py --outdir ./output_sim --seed 42
```

Optimistic scenario (heavy, N=10,000 civilisations):
```bash
python scripts/run_pipeline.py --outdir ./output_sim --seed 42 --full-optimistic
```

### Key Results (corrected model, v6)

| Regime | N | Destroyed | Delta-r | Sigma | Interpretation |
|--------|---|-----------|---------|-------|----------------|
| Pessimistic | 440 | 2.6 +- 1.5 (0.59%) | +0.0045 +- 0.0032 | ~1 | DF indistinguishable from GHZ geometry |
| **Optimistic** | **10,000** | **2,287 +- 46 (22.9%)** | **+0.060 +- 0.008** | **7.8** | **DF disperses survivors** |

**Main result**: the net spatial effect of the Dark Forest is a modest dispersion of survivors that
grows monotonically with population density, not the massive concentration reported by the previous
version of the model. Destructions are local (they preferentially remove the nearest neighbour),
which shifts the survivor distance distribution towards larger values.

### Sensitivity -- the dominant role of p_fp

`p_fp` was the individually dominant parameter of the v5 model: removing it changes destruction
rates by factors of 4-27x and flips the sign of the differential spatial effect (see Spanish table
above). The v5 Sobol analysis (which did not include `p_fp` among its factors) correctly reported
that "no parameter dominates" -- a conclusion valid only within that parameter subspace. A Sobol
analysis of the corrected model, with per-point replicates and `p_fp`/`p_fn` included, is left as
future work.

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

Manuscript in MNRAS format, being prepared for submission. Published on Zenodo (the concept DOI
below always resolves to the latest version):

**Concept DOI:** [10.5281/zenodo.20451754](https://doi.org/10.5281/zenodo.20451754)

```bibtex
@article{galaz2026darkforest,
  title={{Del Silencio a la Dispersion: El Efecto Espacial Neto del Bosque Oscuro
          es Modesto y Crece con la Densidad}},
  author={Galaz, Juan},
  year={2026},
  doi={10.5281/zenodo.20451754},
  note={Manuscript in MNRAS format; software and data at
        \url{https://github.com/CienciaEstelar/dark-forest-mc}}
}
```

---

*"El universo es un bosque oscuro. Cada civilizacion es un cazador armado,
acechando entre los arboles, tratando de no hacer ruido."* -- Liu Cixin

*"The universe is a dark forest. Every civilisation is an armed hunter,
stalking through the trees, trying to keep quiet."* -- Liu Cixin
