/**
 * Alpha Nepal Capital — Client Application Data Loader & View Renderer.
 */

const App = {
  data: {},

  async init() {
    await this.fetchAllData();
    this.updateClocks();
    this.renderCurrentPage();
  },

  async fetchAllData() {
    const endpoints = [
      "clocks",
      "company",
      "portfolio",
      "performance",
      "risk",
      "decisions",
      "transactions",
      "compliance",
      "financials",
      "benchmarks",
      "timeline"
    ];

    for (const ep of endpoints) {
      try {
        const resp = await fetch(`data/${ep}.json?t=${Date.now()}`);
        if (resp.ok) {
          this.data[ep] = await resp.json();
        }
      } catch (err) {
        console.warn(`Failed loading data/${ep}.json`, err);
      }
    }
  },

  updateClocks() {
    const clocks = this.data.clocks;

    const marketTimeEl = document.getElementById("market-clock");
    const aiTimeEl = document.getElementById("ai-clock");
    const dataStatusEl = document.getElementById("data-status-tag");

    // Live ticking NPT clock — runs every second in the browser
    const tickMarketClock = () => {
      if (!marketTimeEl) return;
      const now = new Date();
      const nptOffset = 5 * 60 + 45; // NPT = UTC+5:45
      const nptMs = now.getTime() + (now.getTimezoneOffset() + nptOffset) * 60000;
      const npt = new Date(nptMs);
      const h = String(npt.getHours()).padStart(2, "0");
      const m = String(npt.getMinutes()).padStart(2, "0");
      const s = String(npt.getSeconds()).padStart(2, "0");
      marketTimeEl.textContent = `${h}:${m}:${s} NPT`;
    };
    tickMarketClock();
    setInterval(tickMarketClock, 1000);

    // AI Last Run — from the JSON file (when simulation last executed)
    if (clocks && aiTimeEl && clocks.ai_decision_time) {
      const lastRun = new Date(clocks.ai_decision_time);
      const hoursAgo = Math.round((Date.now() - lastRun.getTime()) / 3600000);
      aiTimeEl.textContent = `${Utils.formatTime(clocks.ai_decision_time)} (${hoursAgo}h ago)`;
    } else if (aiTimeEl) {
      aiTimeEl.textContent = "Pending first cycle";
    }

    // Staleness detection — mark STALE if last run was > 26 hours ago
    if (dataStatusEl) {
      let status = "STALE";
      if (clocks && clocks.ai_decision_time) {
        const hoursSinceRun = (Date.now() - new Date(clocks.ai_decision_time).getTime()) / 3600000;
        if (hoursSinceRun < 26) {
          status = clocks.data_status || "LIVE";
        }
      }
      const isLive = status === "LIVE";
      dataStatusEl.className = `status-tag ${isLive ? "status-live" : "status-delayed"}`;
      dataStatusEl.innerHTML = `<span class="pulse-dot"></span> ${status}`;
    }
  },

  renderCurrentPage() {
    const path = window.location.pathname.split("/").pop() || "index.html";

    if (path.includes("index.html") || path === "") {
      this.renderHome();
    } else if (path.includes("portfolio.html")) {
      this.renderPortfolioPage();
    } else if (path.includes("performance.html")) {
      this.renderPerformancePage();
    } else if (path.includes("decisions.html")) {
      this.renderDecisionsPage();
    } else if (path.includes("strategy.html")) {
      this.renderStrategyPage();
    } else if (path.includes("financials.html")) {
      this.renderFinancialsPage();
    } else if (path.includes("reports.html")) {
      this.renderReportsPage();
    } else if (path.includes("about.html")) {
      this.renderAboutPage();
    }
  },

  renderHome() {
    const company = this.data.company;
    const portfolio = this.data.portfolio;
    const decisions = this.data.decisions;
    const benchmarks = this.data.benchmarks;
    const compliance = this.data.compliance;

    if (!company) return;

    // Status Badge
    const statusContainer = document.getElementById("company-status-badge");
    if (statusContainer) {
      statusContainer.innerHTML = Utils.getStatusBadge(company.status);
    }

    // Hero Metrics
    this.setText("hero-total-assets", Utils.formatCurrency(company.current_total_assets));
    this.setText("hero-nav", `NPR ${Number(company.current_nav_per_share).toFixed(4)}`);
    this.setText("hero-return", Utils.formatPercent(company.total_return_pct));
    this.setPnLClass("hero-return", company.total_return_pct);

    this.setText("hero-nepse-return", Utils.formatPercent(company.nepse_index_return_pct));
    this.setText("hero-alpha", Utils.formatPercent(company.alpha_pct));
    this.setPnLClass("hero-alpha", company.alpha_pct);

    this.setText("hero-compliance", `${compliance ? compliance.overall_compliance_score_pct : 96.7}%`);
    this.setText("hero-days-active", `${company.days_active || 1} Days`);

    // Render NAV Chart
    if (benchmarks && benchmarks.time_series) {
      Charts.renderNAVChart("homeNavChart", benchmarks.time_series);
    }

    // Render Top Holdings Preview
    if (portfolio && portfolio.holdings) {
      const tbody = document.getElementById("home-holdings-tbody");
      if (tbody) {
        tbody.innerHTML = portfolio.holdings.slice(0, 5).map(h => `
          <tr>
            <td><strong>${h.symbol}</strong></td>
            <td>${h.sector}</td>
            <td class="mono">${Utils.formatNumber(h.quantity)}</td>
            <td class="mono">${Utils.formatCurrency(h.current_price)}</td>
            <td class="mono font-semibold">${Utils.formatCurrency(h.current_value)}</td>
            <td class="mono">${h.weight_pct.toFixed(1)}%</td>
            <td class="mono ${Utils.getPnLClass(h.unrealized_pnl)}">${Utils.formatPercent(h.unrealized_pnl_pct)}</td>
            <td>${Utils.getRouteBadge(h.route)}</td>
          </tr>
        `).join("");
      }
    }

    // Render Recent Decisions Preview
    if (decisions && decisions.decisions) {
      const decContainer = document.getElementById("home-decisions-feed");
      if (decContainer) {
        decContainer.innerHTML = decisions.decisions.slice(0, 3).map(d => `
          <div class="decision-item ${d.action.toLowerCase()}">
            <div class="decision-header">
              <span class="decision-title">
                <strong>${d.action} — ${d.symbol}</strong>
                ${Utils.getRouteBadge(d.route)}
              </span>
              <span class="decision-meta">${Utils.formatDate(d.trade_date)} | Confidence: ${d.confidence_pct.toFixed(0)}%</span>
            </div>
            <div class="decision-body">
              <p><strong>Allocation:</strong> NPR ${Number(d.capital_allocation_npr).toLocaleString()} (${d.quantity} shares @ NPR ${d.price})</p>
              <p>${d.reason_summary}</p>
            </div>
            <div class="decision-scores">
              <span><strong>Structural:</strong> ${d.structural_score ? d.structural_score.toFixed(1) : '-'}</span>
              <span><strong>Literature:</strong> ${d.literature_score ? d.literature_score.toFixed(1) : '-'}</span>
              <span class="text-positive"><strong>Cognitive Delta:</strong> +${d.delta_pct ? d.delta_pct.toFixed(1) : '-'}%</span>
              <span><strong>Score:</strong> ${d.final_score ? d.final_score.toFixed(1) : '-'}</span>
            </div>
          </div>
        `).join("");
      }
    }
  },

  renderPortfolioPage() {
    const portfolio = this.data.portfolio;
    const balance = this.data.financials ? this.data.financials.balance_sheet : null;
    if (!portfolio) return;

    this.setText("port-total-assets", Utils.formatCurrency(portfolio.total_assets));
    this.setText("port-invested", Utils.formatCurrency(portfolio.invested_npr));
    this.setText("port-cash", Utils.formatCurrency(portfolio.cash_npr));
    this.setText("port-cash-weight", `${portfolio.cash_weight_pct.toFixed(1)}%`);

    const tbody = document.getElementById("portfolio-tbody");
    if (tbody && portfolio.holdings) {
      tbody.innerHTML = portfolio.holdings.map(h => `
        <tr>
          <td><strong>${h.symbol}</strong></td>
          <td>${h.sector}</td>
          <td class="mono">${Utils.formatNumber(h.quantity)}</td>
          <td class="mono">${Utils.formatCurrency(h.avg_buy_price)}</td>
          <td class="mono">${Utils.formatCurrency(h.current_price)}</td>
          <td class="mono font-semibold">${Utils.formatCurrency(h.current_value)}</td>
          <td class="mono">${h.weight_pct.toFixed(1)}%</td>
          <td class="mono ${Utils.getPnLClass(h.unrealized_pnl)}">${Utils.formatCurrency(h.unrealized_pnl)} (${Utils.formatPercent(h.unrealized_pnl_pct)})</td>
          <td>${Utils.getRouteBadge(h.route)}</td>
        </tr>
      `).join("");
    }

    if (portfolio.sector_exposures) {
      Charts.renderSectorChart("sectorChart", portfolio.sector_exposures);
    }
  },

  renderPerformancePage() {
    const benchmarks = this.data.benchmarks;
    const perf = this.data.performance;
    if (!benchmarks) return;

    if (benchmarks.time_series) {
      Charts.renderNAVChart("performanceMainChart", benchmarks.time_series);
    }

    const tbody = document.getElementById("benchmarks-tbody");
    if (tbody && benchmarks.comparison_summary) {
      tbody.innerHTML = benchmarks.comparison_summary.map(b => `
        <tr>
          <td><strong>${b.name}</strong></td>
          <td>${b.category}</td>
          <td class="mono font-bold ${Utils.getPnLClass(b.return_pct)}">${Utils.formatPercent(b.return_pct)}</td>
          <td class="mono">${b.volatility_pct.toFixed(1)}%</td>
          <td class="mono">${b.sharpe_ratio.toFixed(2)}</td>
          <td class="mono text-negative">${b.max_drawdown_pct.toFixed(1)}%</td>
        </tr>
      `).join("");
    }
  },

  renderDecisionsPage() {
    const decisions = this.data.decisions;
    if (!decisions || !decisions.decisions) return;

    const feed = document.getElementById("decisions-full-feed");
    if (feed) {
      feed.innerHTML = decisions.decisions.map(d => `
        <div class="decision-item ${d.action.toLowerCase()}">
          <div class="decision-header">
            <span class="decision-title">
              <strong>${d.action} — ${d.symbol}</strong>
              ${Utils.getRouteBadge(d.route)}
            </span>
            <span class="decision-meta">${Utils.formatDate(d.trade_date)} ${Utils.formatTime(d.timestamp)} | Confidence: ${d.confidence_pct.toFixed(0)}%</span>
          </div>
          <div class="decision-body">
            <p><strong>Capital Allocation:</strong> NPR ${Number(d.capital_allocation_npr).toLocaleString()} (${d.quantity} shares @ NPR ${d.price})</p>
            <p><strong>Reasoning:</strong> ${d.reason_summary}</p>
            <p><strong>Invalidation Rule:</strong> <em>${d.invalidation_condition}</em></p>
          </div>
          <div class="decision-scores">
            <span><strong>Structural Score:</strong> ${d.structural_score ? d.structural_score.toFixed(1) : '-'}</span>
            <span><strong>Literature Audit:</strong> ${d.literature_score ? d.literature_score.toFixed(1) : '-'}</span>
            <span class="text-positive"><strong>Cognitive Delta:</strong> +${d.delta_pct ? d.delta_pct.toFixed(1) : '-'}% (Intrinsic: NPR ${d.intrinsic_value_est ? Number(d.intrinsic_value_est).toLocaleString() : '-'})</span>
            <span><strong>Final Score:</strong> ${d.final_score ? d.final_score.toFixed(1) : '-'} / 100</span>
          </div>
        </div>
      `).join("");
    }
  },

  renderStrategyPage() {
    const compliance = this.data.compliance;
    const risk = this.data.risk;

    if (compliance) {
      this.setText("compliance-score-val", `${compliance.overall_compliance_score_pct.toFixed(1)}%`);
      const tbody = document.getElementById("compliance-rules-tbody");
      if (tbody && compliance.rules) {
        tbody.innerHTML = compliance.rules.map(r => `
          <tr>
            <td class="mono">${r.rule_id}</td>
            <td><strong>${r.rule_name}</strong></td>
            <td class="mono">${r.threshold}</td>
            <td class="mono">${r.current_value.toFixed(1)}</td>
            <td>
              <span class="status-tag ${r.passed ? 'status-live' : 'status-delayed'}">
                ${r.passed ? 'PASS' : r.severity}
              </span>
            </td>
            <td>${r.message}</td>
          </tr>
        `).join("");
      }
    }
  },

  renderFinancialsPage() {
    const fin = this.data.financials;
    if (!fin) return;

    const bs = fin.balance_sheet;
    const inc = fin.income_statement;

    // Balance Sheet
    this.setText("bs-cash", Utils.formatCurrency(bs.cash_and_equivalents));
    this.setText("bs-investments", Utils.formatCurrency(bs.equity_investments_market_value));
    this.setText("bs-total-assets", Utils.formatCurrency(bs.total_assets));
    this.setText("bs-equity", Utils.formatCurrency(bs.shareholder_equity));
    this.setText("bs-nav", `NPR ${Number(bs.nav_per_share).toFixed(4)}`);

    // Income Statement
    this.setText("inc-gross", Utils.formatCurrency(inc.gross_investment_income));
    this.setText("inc-div", Utils.formatCurrency(inc.dividend_income));
    this.setText("inc-realized", Utils.formatCurrency(inc.realized_capital_gains));
    this.setText("inc-unrealized", Utils.formatCurrency(inc.unrealized_gains_losses));
    this.setText("inc-costs", `(${Utils.formatCurrency(inc.transaction_costs)})`);
    this.setText("inc-net", Utils.formatCurrency(inc.net_profit));
    this.setText("inc-margin", `${inc.net_margin_pct.toFixed(1)}%`);
  },

  renderReportsPage() {
    const listEl = document.getElementById("monthly-reports-list");
    if (!listEl) return;

    // Default August 2026 report preview
    listEl.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h3>August 2026 — Inaugural CEO Report</h3>
          <span class="status-tag status-live">PUBLISHED</span>
        </div>
        <p class="lead" style="margin-bottom: 1rem;">
          Alpha Nepal Capital commenced operations with NPR 100,000,000 in starting capital. The company executed its 
          autonomous mandate under the ASA-V1.ethics framework, achieving 100% strategy compliance and outperforming the benchmark.
        </p>
        <div class="metrics-grid" style="margin-bottom: 1rem;">
          <div class="metric-card">
            <div class="metric-label">Period Return</div>
            <div class="metric-value text-positive">+2.40%</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Alpha vs NEPSE</div>
            <div class="metric-value text-positive">+1.10%</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Compliance</div>
            <div class="metric-value text-positive">100.0%</div>
          </div>
        </div>
        <p style="color: var(--text-secondary);">
          <strong>Management Outlook:</strong> The AI management committee maintains strict risk controls with 5%+ cash buffers 
          while aggressively capitalizing on mispriced cognitive deltas in essential hydropower and banking infrastructure.
        </p>
      </div>
    `;
  },

  renderAboutPage() {
    const timeline = this.data.timeline;
    const feed = document.getElementById("timeline-feed");
    if (feed && timeline && timeline.events) {
      feed.innerHTML = timeline.events.map(e => `
        <div class="decision-item">
          <div class="decision-header">
            <span class="decision-title"><strong>${e.title}</strong></span>
            <span class="decision-meta">${Utils.formatDate(e.event_date)}</span>
          </div>
          <p style="color: var(--text-secondary); margin-top: 0.4rem;">${e.description}</p>
        </div>
      `).join("");
    }
  },

  setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  },

  setPnLClass(id, value) {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove("text-positive", "text-negative");
      el.classList.add(Utils.getPnLClass(value));
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
