from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

app = FastAPI(title="Ventas - Pollo/Carne")

# =========================
# Paths (Corregidos a 'processed')
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"           

PRODUCTOS = {
    "pollo": DATA_DIR / "Analisis_Final_Ventas_Pollo_Final.xlsx",
    "carne": DATA_DIR / "Analisis_Final_Ventas_Carne_Final.xlsx",
}

SHEET = "Sheet1"

# =========================
# Colores por fase
# =========================
PHASE_COLORS = {
    "train": "#1f77b4",  # azul
    "test":  "#ff7f0e",  # naranja
    "proj":  "#2ca02c",  # verde
}

# =========================
# Helpers
# =========================
def load_producto(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=SHEET)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


def build_figure(producto: str) -> go.Figure:
    if producto not in PRODUCTOS:
        producto = "pollo"

    path = PRODUCTOS[producto]

    # Si falta archivo, mostramos mensaje dentro del gráfico
    if not path.exists():
        fig = go.Figure()
        fig.add_annotation(
            text=f"❌ No se encontró el archivo:<br>{path}",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(template="plotly_white", title="Error de archivo")
        return fig

    df = load_producto(path)

    fig = go.Figure()

    # TRAIN (azul, sólido)
    if "Venta_Real" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["Fecha"], y=df["Venta_Real"],
            mode="lines",
            name="Train (real)",
            line=dict(color=PHASE_COLORS["train"], width=2)
        ))

    # TEST (naranja, dash)
    if "Validacion_Test_2025" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["Fecha"], y=df["Validacion_Test_2025"],
            mode="lines",
            name="Test 2025",
            line=dict(color=PHASE_COLORS["test"], width=2, dash="dash")
        ))

    # PROYECCIÓN (verde, dot)
    if "Proyeccion_Noviembre" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["Fecha"], y=df["Proyeccion_Noviembre"],
            mode="lines",
            name="Proyección (Noviembre)",
            line=dict(color=PHASE_COLORS["proj"], width=2, dash="dot")
        ))

    fig.update_layout(
        title=f"Ventas ({producto.capitalize()}): Train vs Test vs Proyección",
        xaxis_title="Fecha",
        yaxis_title="Ventas",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", y=1.02),
        margin=dict(l=40, r=20, t=60, b=40),
        uirevision="keep"
    )

    return fig


# =========================
# UI (Botones)
# =========================
@app.get("/", response_class=HTMLResponse)
def home():
    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <title>Ventas - Pollo/Carne</title>

      <!-- Plotly cargado una sola vez -->
      <script src="https://cdn.plot.ly/plotly-2.30.0.min.js"></script>

      <style>
        body {{ font-family: Arial, sans-serif; margin: 18px; }}
        .bar {{ display:flex; gap:10px; align-items:center; margin-bottom: 12px; }}
        button {{
          padding: 10px 14px; border-radius: 10px; border: 1px solid #ddd;
          background: #f7f7f7; cursor:pointer; font-weight: 700;
        }}
        button.active {{ background:#111; color:#fff; border-color:#111; }}
        .hint {{ color:#555; font-size: 13px; margin-left:auto; }}
        #plotWrap {{ border: 1px solid #eee; border-radius: 14px; padding: 10px; }}
        #plot {{ width: 100%; height: 520px; }}
        .paths {{ margin-top:10px; font-size: 12px; color: #666; }}
        code {{ background:#f5f5f5; padding:2px 6px; border-radius:8px; }}
      </style>
    </head>
    <body>
      <div class="bar">
        <button id="btn-pollo" class="active" onclick="setProduct('pollo')">Pollo</button>
        <button id="btn-carne" onclick="setProduct('carne')">Carne</button>
        <div class="hint">Train=azul · Test=naranja · Proyección=verde</div>
      </div>

      <div id="plotWrap">
        <div id="plot"></div>
      </div>

      <div class="paths">
        Archivos esperados en: <code>{DATA_DIR}</code><br/>
        Pollo: <code>{PRODUCTOS["pollo"]}</code><br/>
        Carne: <code>{PRODUCTOS["carne"]}</code>
      </div>

      <script>
        function setActiveButton(prod) {{
          ['pollo','carne'].forEach(x => {{
            document.getElementById('btn-' + x).classList.toggle('active', x === prod);
          }});
        }}

        async function renderPlot(prod) {{
          const res = await fetch('/plot-json?producto=' + prod);
          const fig = await res.json();
          Plotly.react('plot', fig.data, fig.layout, {{responsive: true}});
        }}

        async function setProduct(prod) {{
          setActiveButton(prod);
          await renderPlot(prod);
        }}

        // Render inicial
        setProduct('pollo');
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


# =========================
# Endpoint JSON
# =========================
@app.get("/plot-json")
def plot_json(producto: str = "pollo"):
    fig = build_figure(producto)
    fig_json = pio.to_json(fig)
    return Response(content=fig_json, media_type="application/json")