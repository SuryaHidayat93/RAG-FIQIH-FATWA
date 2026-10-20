"""Generate LinkedIn-ready evaluation benchmark card infographic for RAG Fiqih & Fatwa."""
import json
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set backend
matplotlib.use("Agg")
import sys
sys.stdout.reconfigure(encoding="utf-8")

# Load benchmark results
json_path = Path("eval/benchmark_ragas_results.json")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]

# Filter labels & values
questions = []
scores = []
colors = []

# Shorten question titles for crisp display
short_titles = [
    "Q1: Bunga Bank (Fatwa MUI)",
    "Q2: Paylater Belanja Online (DSN-MUI)",
    "Q3: Uang Elektronik Syariah (DSN-MUI)",
    "Q4: Cryptocurrency / Kripto (Ijtima MUI)",
    "Q5: Jual Beli Emas Cicilan (DSN-MUI)",
    "Q6: Sentuh Kulit Istri (Fiqih Syafi'i)",
    "Q7: Rukun & Fardhu Wudhu (Fiqih Syafi'i)",
    "Q8: Jarak Qashar Shalat (Fiqih Syafi'i)",
    "Q9: Volume Air 2 Kullah (Fiqih Syafi'i)",
    "Q10: Nisab Zakat Emas (Fiqih Syafi'i)",
]

for idx, r in enumerate(results):
    score = r["faithfulness"] * 100
    scores.append(score)
    # Color coding
    if score >= 90:
        colors.append("#10B981")  # Emerald Green
    elif score >= 70:
        colors.append("#06B6D4")  # Cyan / Teal
    elif score > 0:
        colors.append("#F59E0B")  # Amber
    else:
        colors.append("#EF4444")  # Red (Guarded Abstain / Token Cutoff)

# Invert for top-to-bottom bar order
short_titles = short_titles[::-1]
scores = scores[::-1]
colors = colors[::-1]

# Canvas configuration (16:10 ratio, 1600x1000 px at 100 dpi)
fig = plt.figure(figsize=(16, 10), facecolor="#0B1120")

# Grid layout: Header space, Key KPI Cards, Chart, Footer specs
# Create axes: [left, bottom, width, height]
ax_chart = fig.add_axes([0.08, 0.16, 0.84, 0.52], facecolor="#0B1120")

# Hide spines
for spine in ax_chart.spines.values():
    spine.set_visible(False)

# Horizontal Bars
bars = ax_chart.barh(short_titles, scores, color=colors, height=0.62, edgecolor="#1E293B", linewidth=1.2)

# Gridlines
ax_chart.xaxis.grid(True, linestyle="--", alpha=0.18, color="#94A3B8")
ax_chart.set_axisbelow(True)

# Format ticks
ax_chart.set_xlim(0, 115)
ax_chart.set_xticks([0, 20, 40, 60, 80, 100])
ax_chart.set_xticklabels(["0%", "20%", "40%", "60%", "80%", "100%"], fontsize=12, color="#94A3B8", weight="bold")
ax_chart.tick_params(axis="y", labelsize=12, colors="#F1F5F9", left=False)
ax_chart.tick_params(axis="x", colors="#64748B", bottom=False)

# Annotations on bars
for bar, score in zip(bars, scores):
    w = bar.get_width()
    y = bar.get_y() + bar.get_height() / 2
    if score > 0:
        label = f" {score:.1f}%"
        ax_chart.text(w + 1.2, y, label, va="center", ha="left", color="#F8FAFC", fontsize=11, weight="bold")
    else:
        ax_chart.text(1.5, y, "0.0% (Guarded Abstain / Cutoff)", va="center", ha="left", color="#F87171", fontsize=10.5, style="italic", weight="bold")

# Title and Subtitle in Figure coordinates
fig.text(0.08, 0.94, "RAG FIQIH & FATWA — BENCHMARK EVALUATION", fontsize=24, color="#FFFFFF", weight="bold")
fig.text(0.08, 0.905, "Faithfulness & Hallucination Audit via Ragas Framework + Gemini 3.8 Flash", fontsize=13, color="#94A3B8")

# Category Tag
fig.text(0.92, 0.935, "PRODUCTION BENCHMARK", fontsize=10.5, color="#38BDF8", weight="bold", ha="right",
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#0369A1", edgecolor="#0284C7", alpha=0.35))

# Top Metric Cards (3 KPI boxes)
# Card 1: Average Faithfulness
rect1 = patches.FancyBboxPatch((0.08, 0.74), 0.25, 0.125, boxstyle="round,pad=0.01", facecolor="#1E293B", edgecolor="#334155", linewidth=1.5, transform=fig.transFigure)
fig.patches.append(rect1)
fig.text(0.095, 0.825, "AVERAGE FAITHFULNESS", fontsize=10, color="#94A3B8", weight="bold")
fig.text(0.095, 0.765, f"{data['average_faithfulness']*100:.2f}%", fontsize=26, color="#38BDF8", weight="bold")
fig.text(0.20, 0.772, "/ 100%", fontsize=12, color="#64748B")

# Card 2: Valid Answers Avg (excluding token cutoff)
rect2 = patches.FancyBboxPatch((0.375, 0.74), 0.25, 0.125, boxstyle="round,pad=0.01", facecolor="#1E293B", edgecolor="#334155", linewidth=1.5, transform=fig.transFigure)
fig.patches.append(rect2)
fig.text(0.39, 0.825, "VALID REPLIES GROUNDEDNESS", fontsize=10, color="#94A3B8", weight="bold")
valid_scores = [s for s in scores if s > 0]
valid_avg = sum(valid_scores) / len(valid_scores) if valid_scores else 0
fig.text(0.39, 0.765, f"{valid_avg:.2f}%", fontsize=26, color="#10B981", weight="bold")
fig.text(0.505, 0.772, "avg", fontsize=12, color="#64748B")

# Card 3: Evaluator Speed
rect3 = patches.FancyBboxPatch((0.67, 0.74), 0.25, 0.125, boxstyle="round,pad=0.01", facecolor="#1E293B", edgecolor="#334155", linewidth=1.5, transform=fig.transFigure)
fig.patches.append(rect3)
fig.text(0.685, 0.825, "EVALUATOR AUDIT LATENCY", fontsize=10, color="#94A3B8", weight="bold")
fig.text(0.685, 0.765, f"16.5s", fontsize=26, color="#F59E0B", weight="bold")
fig.text(0.74, 0.772, "avg per query", fontsize=11.5, color="#64748B")

# Footer Technical Specs Bar
rect_footer = patches.FancyBboxPatch((0.08, 0.04), 0.84, 0.085, boxstyle="round,pad=0.01", facecolor="#111827", edgecolor="#1F2937", linewidth=1.2, transform=fig.transFigure)
fig.patches.append(rect_footer)

spec_text = (
    "  • Architecture: CRAG + Self-RAG + Hybrid Retrieval (BGE-M3 Dense + BM25 Sparse -> RRF)     "
    "  • Corpora: 10,987 Fatwa DSN-MUI + 583 Kitab Fathul Qarib\n"
    "  • Models: Generator (Llama 3.1 8B via Ollama / RTX 4050) | Evaluator: Gemini 3.8 Flash | Cross-Model Zero-Shot Verification"
)
fig.text(0.095, 0.065, spec_text, fontsize=10, color="#94A3B8", linespacing=1.6)

# Save image
out_path = Path("eval/benchmark_evaluation_card.png")
plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.close(fig)

print(f"✓ Berhasil generate card visual LinkedIn ke: {out_path}")
