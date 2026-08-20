/**
 * Chart.js configurations for Alpha Nepal Capital.
 */

const Charts = {
  renderNAVChart(canvasId, timeSeriesData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !timeSeriesData || timeSeriesData.length === 0) return null;

    const labels = timeSeriesData.map(d => d.date);
    const aiNavs = timeSeriesData.map(d => d.ai_nav || d.nav || 10.0);
    const nepseNavs = timeSeriesData.map(d => 10.0 * (1 + (d.nepse_return_pct || 0) / 100));
    const humanNavs = timeSeriesData.map(d => d.human_nav || 10.0);
    const eqNavs = timeSeriesData.map(d => d.equal_weight_nav || 10.0);

    return new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Alpha Nepal Capital (AI)",
            data: aiNavs,
            borderColor: "#00d26a",
            backgroundColor: "rgba(0, 210, 106, 0.12)",
            borderWidth: 3,
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: "NEPSE Index Benchmark",
            data: nepseNavs,
            borderColor: "#38bdf8",
            borderWidth: 2,
            borderDash: [5, 5],
            fill: false,
            tension: 0.3,
            pointRadius: 3,
          },
          {
            label: "Human Static Strategy",
            data: humanNavs,
            borderColor: "#f59e0b",
            borderWidth: 2,
            borderDash: [2, 2],
            fill: false,
            tension: 0.3,
            pointRadius: 2,
          },
          {
            label: "Equal-Weight Benchmark",
            data: eqNavs,
            borderColor: "#c084fc",
            borderWidth: 1.5,
            borderDash: [3, 3],
            fill: false,
            tension: 0.3,
            pointRadius: 2,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false
        },
        plugins: {
          legend: {
            position: "top",
            labels: {
              color: "#94a3b8",
              font: { family: "Inter", size: 12 }
            }
          },
          tooltip: {
            backgroundColor: "#182234",
            titleColor: "#f1f5f9",
            bodyColor: "#94a3b8",
            borderColor: "#24324d",
            borderWidth: 1,
            padding: 12,
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: NPR ${context.parsed.y.toFixed(4)}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { color: "rgba(36, 50, 77, 0.4)" },
            ticks: { color: "#64748b", font: { family: "Inter", size: 11 } }
          },
          y: {
            grid: { color: "rgba(36, 50, 77, 0.4)" },
            ticks: {
              color: "#64748b",
              font: { family: "JetBrains Mono", size: 11 },
              callback: val => `NPR ${val.toFixed(2)}`
            }
          }
        }
      }
    });
  },

  renderSectorChart(canvasId, sectorExposures) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !sectorExposures) return null;

    const labels = Object.keys(sectorExposures);
    const data = Object.values(sectorExposures);

    const colors = [
      "#00d26a", "#38bdf8", "#f59e0b", "#c084fc", "#ec4899", "#14b8a6", "#f97316", "#6366f1"
    ];

    return new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: colors.slice(0, labels.length),
          borderColor: "#121826",
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "right",
            labels: { color: "#94a3b8", font: { family: "Inter", size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.label}: ${ctx.parsed.toFixed(1)}%`
            }
          }
        },
        cutout: "68%"
      }
    });
  }
};
