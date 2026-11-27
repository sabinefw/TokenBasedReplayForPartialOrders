FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    MPLBACKEND=Agg

RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && useradd --create-home --shell /usr/sbin/nologin potrack \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=potrack:potrack . .

USER potrack

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["streamlit", "run", "tool.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
