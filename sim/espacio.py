"""
Generación de posiciones galácticas realistas con perfil de habitabilidad continuo.

Distribución radial basada en Lineweaver et al. (2004), Science 303, 59-62:
    f(r) = exp(-((r - r_peak)^2) / (2 * sigma^2))
con r_peak = 25 000 ly, sigma = 8 000 ly.

La distribución de muestreo efectiva es w(r) = r * f(r), que pondera f(r)
por el área del anillo galáctico (∝ r dr). Se muestrea mediante CDF inversa
precalculada sobre una grilla de 10 000 puntos (vectorizado, sin bucles Python).

30 % de las civilizaciones se ubican en el bulbo galáctico (distribución
exponencial), cuya habitabilidad no está regida por la GHZ estándar pero
representa poblaciones estelares de alta metalicidad.
"""

import numpy as np
from ..common.config import Parametros


def _cdf_lineweaver(p: Parametros, n_grid: int = 10_000):
    """
    Precalcula la CDF de w(r) = r * exp(-((r - r_peak)^2 / (2*sigma^2)))
    en el intervalo [0, radio_galaxia].
    Devuelve (r_grid, cdf) para uso con np.interp.
    """
    r_grid = np.linspace(0.0, float(p.radio_galaxia), n_grid)
    r_peak = float(p.ghz_peak_radius)
    sigma = float(p.ghz_sigma)
    w = r_grid * np.exp(-((r_grid - r_peak) ** 2) / (2.0 * sigma ** 2))
    cdf = np.cumsum(w)
    cdf /= cdf[-1]
    return r_grid, cdf


def generar_posiciones(n_civs: int, p: Parametros) -> np.ndarray:
    """
    Genera posiciones 3D (x, y, z) en años-luz.

    - 30 % bulbo: r ~ Exponencial(escala_radio_bulbo), z ~ N(0, 100)
    - 70 % disco: r muestreado del perfil GHZ continuo de Lineweaver 2004,
                  z ~ Exponencial(escala_altura_disco) con signo aleatorio
    """
    r_grid, cdf = _cdf_lineweaver(p)

    n_bulbo = int(n_civs * 0.30)
    n_disco = n_civs - n_bulbo

    # --- Disco: r desde CDF Lineweaver, z exponencial ---
    u_disco = np.random.uniform(0.0, 1.0, n_disco)
    r_disco = np.interp(u_disco, cdf, r_grid).astype(np.float32)
    z_disco = (
        np.random.exponential(float(p.escala_altura_disco), n_disco)
        * np.random.choice([-1.0, 1.0], n_disco)
    ).astype(np.float32)

    # --- Bulbo: r exponencial, z gaussiano estrecho ---
    r_bulbo = np.random.exponential(float(p.escala_radio_bulbo), n_bulbo).astype(np.float32)
    z_bulbo = np.random.normal(0.0, 100.0, n_bulbo).astype(np.float32)

    # --- Combinar y mezclar ---
    r_all = np.concatenate([r_disco, r_bulbo])
    z_all = np.concatenate([z_disco, z_bulbo])
    theta = np.random.uniform(0.0, 2.0 * np.pi, n_civs).astype(np.float32)

    # Mezcla aleatoria para que no haya sesgo bulbo/disco por posición en el DataFrame
    idx = np.random.permutation(n_civs)
    r_all = r_all[idx]
    z_all = z_all[idx]
    theta = theta[idx]

    pos = np.empty((n_civs, 3), dtype=np.float32)
    pos[:, 0] = r_all * np.cos(theta)
    pos[:, 1] = r_all * np.sin(theta)
    pos[:, 2] = z_all
    return pos
