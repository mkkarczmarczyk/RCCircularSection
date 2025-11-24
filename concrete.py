"""
Streamlit demo app that reproduces **both** concreteproperties worked examples
on a single page – no view-switching required:

* **Gross Area Properties** – shows the gross section properties for a
  reinforced-concrete rectangular beam.
* **Moment Interaction Diagrams** – plots axial-moment envelopes for bending
  about the x- and y-axes side-by-side.

⚙️  *Install requirements*:
    pip install streamlit concreteproperties sectionproperties matplotlib

🚀 *Run*:
    streamlit run streamlit_concrete_app.py
"""

import warnings

import streamlit as st
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

# Silence the non-interactive backend warning raised by concreteproperties
warnings.filterwarnings(
    "ignore", message="FigureCanvasAgg is non-interactive, and thus cannot be shown"
)
matplotlib.use("Agg")  # Headless-friendly backend for Streamlit

from sectionproperties.pre.library import concrete_rectangular_section
from concreteproperties import (
    Concrete,
    ConcreteLinear,
    ConcreteSection,
    RectangularStressBlock,
    SteelBar,
    SteelElasticPlastic,
)
from concreteproperties.post import si_kn_m, si_n_mm
from sectionproperties.pre.library import concrete_circular_section

st.set_page_config(page_title="ConcreteProperties Examples", layout="wide")
st.title("ConcreteProperties Example Explorer 🏗️ – All Results")

# ──────────────────────────────────────────────────────────────
# Sidebar – user inputs
# ──────────────────────────────────────────────────────────────
st.sidebar.header("Geometry (mm)")
D = st.sidebar.number_input("Diameter D", value=400.0, min_value=100.0, step=10.0)
#d = st.sidebar.number_input("Depth d", value=600.0, min_value=100.0, step=10.0)

st.sidebar.header("Reinforcement")
dia_bar = st.sidebar.number_input("Bar Ø", value=20.0, min_value=10.0)
n_bar=st.sidebar.number_input("Number of bars", value=3, min_value=1, step=1)
cover_to_bar = st.sidebar.number_input("Concrete cover", value=30.0, min_value=5.0)

st.sidebar.header("Materials")
fc = st.sidebar.number_input("Concrete f′c (MPa)", value=32.0, min_value=20.0)
fy = st.sidebar.number_input("Steel fᵧ (MPa)", value=500.0, min_value=200.0)


# ──────────────────────────────────────────────────────────────
# Build material models (AS 3600:2018)
# ──────────────────────────────────────────────────────────────
concrete = Concrete(
    name=f"{fc:.0f} MPa Concrete",
    density=2.4e-6,
    stress_strain_profile=ConcreteLinear(elastic_modulus=30.1e3),
    ultimate_stress_strain_profile=RectangularStressBlock(
        compressive_strength=fc,
        alpha=0.802,
        gamma=0.89,
        ultimate_strain=0.003,
    ),
    flexural_tensile_strength=3.4,
    colour="lightgrey",
)

steel = SteelBar(
    name=f"{fy:.0f} MPa Steel",
    density=7.85e-6,
    stress_strain_profile=SteelElasticPlastic(
        yield_strength=fy, elastic_modulus=200e3, fracture_strain=0.05
    ),
    colour="grey",
)

# ──────────────────────────────────────────────────────────────
# Create geometry & ConcreteSection
# ──────────────────────────────────────────────────────────────

area_conc = np.pi * (D**2) / 4.0
area_bar  = np.pi * (dia_bar**2) / 4.0  # ≈ 1018 mm^2

geom = concrete_circular_section(
    d=D,
    area_conc=area_conc,
    n_conc=96,           # dyskretyzacja koła (np. 96 punktów)
    dia_bar=dia_bar,
    area_bar=area_bar,
    n_bar=n_bar,
    cover=cover_to_bar,  # = 62 mm do powierzchni pręta
    n_circle=16,         # dyskretyzacja kółka pręta
    conc_mat=concrete,
    steel_mat=steel,
)

section = ConcreteSection(geom)

# ──────────────────────────────────────────────────────────────
# 1️⃣  Plot reinforced-concrete section
# ──────────────────────────────────────────────────────────────
ax_sec = section.plot_section()
fig_sec = ax_sec.get_figure() if isinstance(ax_sec, Axes) else ax_sec
st.subheader("Cross-Section")
st.pyplot(fig_sec)
plt.close(fig_sec)

# ──────────────────────────────────────────────────────────────
# 2️⃣  Gross Area Properties
# ──────────────────────────────────────────────────────────────
st.subheader("Gross Area Properties")
props = section.get_gross_properties()
st.json(
    {
        "Total Area (mm²)": f"{props.total_area:.0f}",
        "E.Ixx_g (N·mm²)": f"{props.e_ixx_g:.3e}",
        "E.Iyy_g (N·mm²)": f"{props.e_iyy_g:.3e}",
    }
)
# ──────────────────────────────────────────────────────────────
# 2️⃣  Gross Area Properties
# ──────────────────────────────────────────────────────────────
st.subheader("Distance between bars")
st.write(f"Clear distance (mm): {(np.pi * (D - 2 * cover_to_bar) / n_bar - dia_bar):.0f}")

# ──────────────────────────────────────────────────────────────
# 3️⃣  Moment Interaction Diagrams for x- and y-axis bending
# ──────────────────────────────────────────────────────────────
st.subheader("Moment Interaction Diagrams")
col_x, col_y = st.columns(2)

# — x-axis bending, θ = 0°
with st.spinner("Running MI diagram for θ = 0° (x-axis)…"):
    mi_x = section.moment_interaction_diagram(theta=0.0, progress_bar=False)

ax_x = mi_x.plot_diagram(eng=True, units=si_n_mm, moment="m_x")
fig_x = ax_x.get_figure() if isinstance(ax_x, Axes) else ax_x
with col_x:
    st.pyplot(fig_x)
    st.caption("x-axis bending (θ = 0°) – units: N·mm")
plt.close(fig_x)

# — y-axis bending, θ = 90°
with st.spinner("Running MI diagram for θ = 90° (y-axis)…"):
    mi_y = section.moment_interaction_diagram(theta=np.pi / 2, progress_bar=False)

ax_y = mi_y.plot_diagram(eng=True, units=si_kn_m, moment="m_y")
fig_y = ax_y.get_figure() if isinstance(ax_y, Axes) else ax_y
with col_y:
    st.pyplot(fig_y)
    st.caption("y-axis bending (θ = 90°) – units: kN·m")
plt.close(fig_y)

# ──────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────
st.caption("App built with concreteproperties v0.7 and Streamlit – results match the library tutorials.")