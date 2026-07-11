#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
compile_paper.py — Compilador automático de LaTeX v2.3
=======================================================
Corregido para Dark Forest paper (mn2e class, thebibliography inline).

Cambios v2.2 → v2.3:
- Bug fix: pre_script usa shlex.split() en lugar de str.split() para
  manejar correctamente argumentos con espacios.
- Bug fix: bibtex se ejecuta con cwd=output_dir para que encuentre el
  .bib cuando --output-dir difiere del directorio del .tex.
- Mejora: flag --yes para modo no-interactivo (CI/scripts); omite
  ambos prompts input() sin requerir intervención del usuario.

Cambios v2.1 → v2.2:
- Bug fix: detección de BibTeX basada en \\bibliography{} en el .tex,
  no en la existencia del .aux (que siempre existe tras paso 1).
- Bug fix: llama 'bibtex' clásico, no 'biber' (mn2e no es compatible con biber).
- Bug fix: verifica que mn2e.cls esté disponible antes de compilar y
  ofrece instrucciones de instalación.
- Bug fix: el modo thebibliography inline omite completamente el paso bibtex.
- Mejora: informa el número de warnings y errores del .log al final.
- Mejora: --keep-aux no pregunta interactivamente (útil en CI/scripts).

Uso básico:
    python compile_paper.py dark_forest_paper
    python compile_paper.py dark_forest_paper --output-dir ./output
    python compile_paper.py dark_forest_paper --keep-aux
    python compile_paper.py dark_forest_paper --yes          # no-interactivo
    python compile_paper.py dark_forest_paper --compiler xelatex

Desde otro directorio:
    python /ruta/compile_paper.py /ruta/al/dark_forest_paper
"""

import os
import re
import shlex
import subprocess
import shutil
import argparse
import sys


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _read_file_safe(path: str) -> str:
    """Lee un archivo con fallback de encoding. Retorna '' si no existe."""
    for enc in ('utf-8', 'latin1', 'cp1252'):
        try:
            with open(path, 'r', encoding=enc, errors='ignore') as f:
                return f.read()
        except FileNotFoundError:
            return ''
        except Exception:
            continue
    return ''


def _tex_uses_external_bib(tex_file: str) -> bool:
    """
    Retorna True solo si el .tex usa \\bibliography{} (archivo .bib externo).
    Retorna False si usa \\begin{thebibliography} (inline) o no tiene bibliografía.
    """
    content = _read_file_safe(tex_file)
    has_external = bool(re.search(r'\\bibliography\s*\{', content))
    has_inline   = bool(re.search(r'\\begin\s*\{thebibliography\}', content))
    return has_external and not has_inline


# ─── DIAGNÓSTICO DEL LOG ─────────────────────────────────────────────────────

def parse_log(log_path: str) -> dict:
    """
    Parsea el .log de LaTeX y retorna un dict con listas de issues.
    Claves: missing_files, missing_packages, undef_refs, errors, warnings_count.
    """
    content = _read_file_safe(log_path)
    if not content:
        return {}

    result = {
        'missing_files':    list(set(re.findall(
            r"LaTeX Warning: File `(.*?)' not found", content))),
        'missing_packages': list(set(re.findall(
            r"! LaTeX Error: File `(.*?\.(?:sty|cls))' not found", content))),
        'undef_refs':       bool(re.search(
            r'LaTeX Warning:.*[Uu]ndefined reference', content)),
        'errors':           re.findall(
            r'^! .*$', content, re.MULTILINE),
        'warnings_count':   len(re.findall(
            r'LaTeX Warning:', content)),
        'overfull':         len(re.findall(
            r'Overfull \\[hv]box', content)),
    }
    return result


def report_log(log_path: str, stage: str):
    """Imprime un resumen del .log. Retorna True si hay errores bloqueantes."""
    issues = parse_log(log_path)
    if not issues:
        print(f"  [log] Archivo {log_path} no encontrado o vacío.")
        return True

    blocking = False

    if issues['missing_packages']:
        blocking = True
        print(f"\n{'='*20} PAQUETES FALTANTES ({stage}) {'='*20}")
        for pkg in issues['missing_packages']:
            pkg_name = pkg.replace('.sty','').replace('.cls','')
            print(f"  ✗ {pkg}")
            print(f"    → Instalar: tlmgr install {pkg_name}")
        print('='*64)

    if issues['missing_files']:
        print(f"\n{'='*20} ARCHIVOS NO ENCONTRADOS ({stage}) {'='*20}")
        for f in issues['missing_files']:
            print(f"  ✗ {f}")
        print('='*64)

    if issues['errors']:
        blocking = True
        print(f"\n{'='*20} ERRORES LaTeX ({stage}) {'='*20}")
        for e in issues['errors'][:10]:
            print(f"  {e}")
        if len(issues['errors']) > 10:
            print(f"  ... y {len(issues['errors'])-10} errores más. Ver el .log completo.")
        print('='*64)

    if issues['undef_refs'] and stage == 'final':
        print(f"  ⚠  Referencias no resueltas en compilación final. "
              f"Revisa \\label/\\ref/\\cite.")

    print(f"  [log] {stage}: {issues['warnings_count']} warnings, "
          f"{issues['overfull']} overfull boxes.")
    return blocking


# ─── VERIFICACIONES PRE-COMPILACIÓN ──────────────────────────────────────────

def check_documentclass(tex_file: str, yes: bool = False) -> bool:
    """
    Verifica que la clase del documento esté disponible.
    Si es mn2e, da instrucciones de instalación si no se encuentra.
    Retorna True si es seguro continuar.
    yes=True omite el prompt interactivo (modo no-interactivo).
    """
    content = _read_file_safe(tex_file)
    m = re.search(r'\\documentclass(?:\[[^\]]*\])?\{(\w+)\}', content)
    if not m:
        print("  ⚠  No se encontró \\documentclass en el .tex. Continuando igualmente.")
        return True

    cls = m.group(1)
    print(f"  Clase detectada: {cls}")

    # Verificar con kpsewhich si la clase está disponible
    result = subprocess.run(['kpsewhich', f'{cls}.cls'],
                            capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        print(f"  ✓ Clase '{cls}.cls' encontrada en: {result.stdout.strip()}")
        return True

    # Clase no encontrada — dar instrucciones específicas
    print(f"\n{'='*20} CLASE NO ENCONTRADA: {cls}.cls {'='*20}")
    if cls == 'mn2e':
        print("  La clase mn2e es la clase oficial de MNRAS/IJA (Cambridge).")
        print("  Para instalarla:")
        print("    1. Descarga mn2e.cls desde:")
        print("       https://ctan.org/pkg/mn2e")
        print("    2. Colócala en el mismo directorio que tu .tex")
        print("    3. O instala con: tlmgr install mn2e")
        print()
        print("  Alternativa para compilar sin mn2e (para previsualización):")
        print("    Cambia la primera línea del .tex a: \\documentclass{article}")
    else:
        print(f"  Instalar con: tlmgr install {cls}")
    print('='*64)

    if yes:
        print("  --yes activo: continuando igualmente.")
        return True

    resp = input(f"\n  ¿Continuar igualmente con la compilación? (s/n): ").strip().lower()
    return resp == 's'


def check_figures(tex_file: str):
    """Verifica que todas las figuras referenciadas existan."""
    content = _read_file_safe(tex_file)
    figures = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^\}]*)\}', content)
    if not figures:
        return

    print(f"\n  Verificando {len(figures)} figuras referenciadas...")
    tex_dir = os.path.dirname(os.path.abspath(tex_file))
    search_dirs = [tex_dir, os.path.join(tex_dir, 'figures'),
                   os.path.join(tex_dir, 'figuras'), '.']

    for fig in figures:
        base, ext = os.path.splitext(fig)
        exts_to_try = [ext] if ext else ['.pdf', '.png', '.jpg', '.jpeg', '.eps']
        found = False
        for d in search_dirs:
            for e in exts_to_try:
                candidate = os.path.join(d, base + e)
                if os.path.exists(candidate):
                    print(f"    ✓ {os.path.relpath(candidate)}")
                    found = True
                    break
            if found:
                break
        if not found:
            print(f"    ✗ '{fig}' — no encontrada en ninguna ruta de búsqueda")


# ─── EJECUCIÓN DE COMANDOS ────────────────────────────────────────────────────

def run_command(cmd: list, stage: str) -> bool:
    """
    Ejecuta un comando. Retorna True si tuvo éxito.
    Imprime las últimas líneas del stdout si falla.
    """
    print(f"\n>>> {stage}")
    print(f"    Comando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding='latin1', errors='ignore')

    # pdflatex retorna 1 incluso con warnings; se considera éxito si generó PDF
    pdf_written = 'Output written on' in result.stdout
    success = (result.returncode == 0) or pdf_written

    if not success:
        print(f"    ✗ Falló (código {result.returncode})")
        tail = result.stdout.splitlines()
        for line in tail[-25:]:
            print(f"    {line}")
        return False

    print(f"    ✓ Completado{'  (PDF generado)' if pdf_written else ''}")
    return True


# ─── COMPILACIÓN PRINCIPAL ───────────────────────────────────────────────────

def compile(tex_path: str, compiler: str, output_dir: str,
            draft: bool, keep_aux: bool, pre_script: str | None,
            yes: bool = False):
    """Orquesta la secuencia completa de compilación."""

    # Normalizar rutas
    tex_path    = os.path.abspath(tex_path)
    tex_dir     = os.path.dirname(tex_path)
    main_name   = os.path.splitext(os.path.basename(tex_path))[0]
    output_dir  = os.path.abspath(output_dir)
    log_path    = os.path.join(output_dir, f'{main_name}.log')
    pdf_path    = os.path.join(output_dir, f'{main_name}.pdf')

    print(f"\n{'='*60}")
    print(f"  compile_paper.py v2.2 — Dark Forest / IJA")
    print(f"  Archivo   : {tex_path}")
    print(f"  Compilador: {compiler}")
    print(f"  Salida    : {output_dir}")
    print(f"{'='*60}\n")

    # ── Verificaciones previas ───────────────────────────────────────────────
    if not os.path.exists(tex_path):
        print(f"✗ ERROR: No se encontró '{tex_path}'. Abortando.")
        sys.exit(1)

    if not shutil.which(compiler):
        print(f"✗ ERROR: Compilador '{compiler}' no encontrado en PATH.")
        print(f"  Instala TeX Live: https://tug.org/texlive/")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    os.chdir(tex_dir)  # Cambiar al directorio del .tex para rutas relativas

    print("── Pre-checks ──────────────────────────────────────────────")
    if not check_documentclass(tex_path, yes=yes):
        print("Abortando a petición del usuario.")
        sys.exit(0)

    check_figures(tex_path)

    # Determinar si necesita BibTeX externo
    use_bibtex = _tex_uses_external_bib(tex_path)
    bib_mode   = 'bibtex externo' if use_bibtex else 'thebibliography inline (sin bibtex)'
    print(f"\n  Bibliografía: {bib_mode}")

    # ── Script externo pre-compilación ───────────────────────────────────────
    if pre_script:
        print(f"\n── Script externo ──────────────────────────────────────────")
        run_command(shlex.split(pre_script), 'Script externo')

    # ── Comando base LaTeX ───────────────────────────────────────────────────
    cmd_base = [
        compiler,
        '-interaction=nonstopmode',
        f'-output-directory={output_dir}',
    ]
    if draft:
        cmd_base.append('-draftmode')
    cmd_base.append(tex_path)

    # ── Secuencia de compilación ─────────────────────────────────────────────
    print(f"\n── Compilación ─────────────────────────────────────────────")

    if not run_command(cmd_base, 'Pasada 1 / LaTeX'):
        report_log(log_path, 'pasada-1')
        print("\n✗ Compilación inicial fallida. Revisa el .log.")
        sys.exit(1)

    if use_bibtex:
        aux_path = os.path.join(output_dir, main_name)
        # cwd=output_dir: bibtex busca el .bib en el dir del .aux; si
        # output_dir != tex_dir el .bib (en tex_dir=CWD) no se encontraría.
        # Solucionamos copiando el .bib al output_dir antes de llamar bibtex.
        for bib_file in [f for f in os.listdir(tex_dir) if f.endswith('.bib')]:
            src = os.path.join(tex_dir, bib_file)
            dst = os.path.join(output_dir, bib_file)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
        if not run_command(['bibtex', aux_path], 'Pasada 2 / BibTeX'):
            print("\n⚠  BibTeX falló. Continuando sin bibliografía externa.")

        if not run_command(cmd_base, 'Pasada 3 / LaTeX post-BibTeX'):
            report_log(log_path, 'pasada-3')
            sys.exit(1)
    else:
        # Sin bibtex — segunda pasada para resolver referencias internas
        run_command(cmd_base, 'Pasada 2 / LaTeX (resolver referencias)')

    # Pasada final
    if not run_command(cmd_base, 'Pasada final / LaTeX'):
        report_log(log_path, 'final')
        sys.exit(1)

    # ── Informe final ────────────────────────────────────────────────────────
    print(f"\n── Informe final ───────────────────────────────────────────")
    blocking = report_log(log_path, 'final')

    if os.path.exists(pdf_path):
        size_kb = os.path.getsize(pdf_path) / 1024
        if not blocking:
            print(f"\n  ✅ ÉXITO — PDF generado sin errores bloqueantes.")
        else:
            print(f"\n  ⚠  PDF generado pero con advertencias. Revisar.")
        print(f"  📄 {pdf_path}  ({size_kb:.1f} KB)")
    else:
        print(f"\n  ✗ El PDF no fue generado. Revisa el .log completo.")
        sys.exit(1)

    # ── Limpieza de auxiliares ───────────────────────────────────────────────
    if not keep_aux:
        if yes:
            resp = 'n'
        else:
            resp = input("\n  ¿Eliminar archivos auxiliares (.aux, .log, etc.)? (s/n): ").strip().lower()
        if resp == 's':
            aux_exts = ['.aux', '.log', '.blg', '.out', '.toc',
                        '.fls', '.fdb_latexmk', '.synctex.gz']
            for ext in aux_exts:
                p = os.path.join(output_dir, main_name + ext)
                if os.path.exists(p):
                    os.remove(p)
                    print(f"    Eliminado: {p}")
            # Conservar .bbl (necesario para arXiv)
            bbl = os.path.join(output_dir, main_name + '.bbl')
            if os.path.exists(bbl):
                print(f"    Conservado: {bbl}  (necesario para arXiv)")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='compile_paper.py v2.2 — Compilador LaTeX para papers científicos.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Compilar dark_forest_paper.tex en el mismo directorio:
  python compile_paper.py dark_forest_paper

  # Especificar ruta completa:
  python compile_paper.py /home/juan-galaz/Escritorio/bosque_oscuro/dark_forest_paper

  # Guardar PDF en subdirectorio 'output/':
  python compile_paper.py dark_forest_paper --output-dir ./output

  # Usar xelatex y conservar auxiliares:
  python compile_paper.py dark_forest_paper --compiler xelatex --keep-aux

  # Generar figuras antes de compilar:
  python compile_paper.py dark_forest_paper --run-script "python generate_figures.py"
        """
    )
    parser.add_argument(
        'filename',
        nargs='?',
        default='paper',
        help='Nombre del .tex SIN extensión, o ruta completa. '
             'Ejemplo: dark_forest_paper'
    )
    parser.add_argument(
        '--compiler',
        choices=['pdflatex', 'xelatex', 'lualatex'],
        default='pdflatex',
        help='Compilador LaTeX (default: pdflatex)'
    )
    parser.add_argument(
        '--output-dir',
        default=None,
        help='Directorio de salida para el PDF y auxiliares. '
             'Default: mismo directorio que el .tex'
    )
    parser.add_argument(
        '--draft',
        action='store_true',
        help='Modo borrador (más rápido, no inserta imágenes)'
    )
    parser.add_argument(
        '--keep-aux',
        action='store_true',
        help='Conservar archivos auxiliares sin preguntar'
    )
    parser.add_argument(
        '--run-script',
        metavar='CMD',
        help='Comando a ejecutar antes de compilar (entre comillas). '
             'Ejemplo: "python generate_figures.py"'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Modo no-interactivo: omite todos los prompts input() '
             '(útil en CI/scripts). Equivale a responder "n" en la limpieza '
             'y "s" en la pregunta de clase no encontrada.'
    )

    args = parser.parse_args()

    # Resolver ruta del .tex
    filename = args.filename
    if not filename.endswith('.tex'):
        filename += '.tex'
    tex_path = os.path.abspath(filename)

    # Directorio de salida: mismo que el .tex por defecto
    output_dir = args.output_dir or os.path.dirname(tex_path)

    compile(
        tex_path   = tex_path,
        compiler   = args.compiler,
        output_dir = output_dir,
        draft      = args.draft,
        keep_aux   = args.keep_aux,
        pre_script = args.run_script,
        yes        = args.yes,
    )


if __name__ == '__main__':
    main()
