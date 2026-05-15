FROM continuumio/miniconda3:latest

LABEL org.opencontainers.image.title="Dark Forest Monte Carlo"
LABEL org.opencontainers.image.description="Simulación Monte Carlo de la hipótesis del Bosque Oscuro — paper MNRAS 2026"
LABEL org.opencontainers.image.authors="Juan Galaz <juan.galaz@proton.me>"
LABEL org.opencontainers.image.source="https://github.com/CienciaEstelar/dark-forest-mc"

RUN conda install -y -c conda-forge \
    numpy=1.26.4 \
    scipy=1.13.0 \
    pandas=2.2.2 \
    matplotlib=3.8.4 \
    pytest=8.2.0 \
    seaborn=0.13.2 \
    && conda clean -afy

RUN pip install --no-cache-dir SALib==1.5.2

WORKDIR /workspace
COPY . /workspace/bosque_oscuro/

ENV PYTHONPATH=/workspace
ENV OPTIMISTIC_CAP=10000

RUN python -c "from bosque_oscuro.common.config import Parametros; print('✓ Pipeline OK')"

CMD ["python", "-m", "bosque_oscuro.run_pipeline", \
     "--outdir", "./output_sim", \
     "--seed", "42", \
     "--analysis-outdir", "./output_analisis", \
     "--no-sensitivity"]
