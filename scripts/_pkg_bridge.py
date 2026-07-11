# -*- coding: utf-8 -*-
"""
Puente de nombre de paquete para los scripts en scripts/.

Los submódulos internos (sim/, analysis/, cli/) usan imports relativos de
DOS niveles (ej. `from ..common.config import Parametros`), que asumen
que viven anidados bajo un paquete de nivel superior llamado literalmente
"bosque_oscuro". Si la carpeta del repo se llama distinto (p. ej.
"dark-forest-mc", que ni siquiera es un identificador válido por el guion),
esos imports fallan con "attempted relative import beyond top-level
package".

Para no reescribir esos módulos, se crea un symlink puente
"bosque_oscuro" -> raíz real del repo en un directorio temporal, y se
agrega ese directorio a sys.path (y se deja preparado un entorno con
PYTHONPATH para los subprocesos que lo necesiten).
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PKG_NAME = "bosque_oscuro"


def ensure_pkg_bridge(repo_root: Path, pkg_name: str = PKG_NAME) -> Path:
    """Crea (si falta) el symlink puente y lo agrega a sys.path. Devuelve el directorio puente."""
    bridge_dir = Path(tempfile.gettempdir()) / "bosque_oscuro_bridge"
    bridge_dir.mkdir(exist_ok=True)
    link_path = bridge_dir / pkg_name

    if link_path.is_symlink() and link_path.resolve() == repo_root.resolve():
        pass
    else:
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        link_path.symlink_to(repo_root, target_is_directory=True)

    if str(bridge_dir) not in sys.path:
        sys.path.insert(0, str(bridge_dir))

    return bridge_dir


def subprocess_env(bridge_dir: Path) -> dict:
    """Copia os.environ agregando el directorio puente al PYTHONPATH, para subprocesos."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(bridge_dir) + os.pathsep + env.get("PYTHONPATH", "")
    return env
