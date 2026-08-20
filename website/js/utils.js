/**
 * Utility formatting functions for Alpha Nepal Capital.
 */

const Utils = {
  formatCurrency(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) return "NPR 0.00";
    return "NPR " + Number(value).toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  },

  formatShortNPR(value) {
    if (value === null || value === undefined || isNaN(value)) return "NPR 0";
    const val = Number(value);
    if (Math.abs(val) >= 10000000) {
      return "NPR " + (val / 10000000).toFixed(2) + " Cr";
    } else if (Math.abs(val) >= 1000000) {
      return "NPR " + (val / 1000000).toFixed(2) + "M";
    } else if (Math.abs(val) >= 1000) {
      return "NPR " + (val / 1000).toFixed(1) + "K";
    }
    return "NPR " + val.toFixed(2);
  },

  formatPercent(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) return "0.00%";
    const val = Number(value);
    const sign = val > 0 ? "+" : "";
    return `${sign}${val.toFixed(decimals)}%`;
  },

  formatNumber(value, decimals = 0) {
    if (value === null || value === undefined || isNaN(value)) return "0";
    return Number(value).toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  },

  formatDate(dateStr) {
    if (!dateStr) return "";
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    } catch {
      return dateStr;
    }
  },

  formatTime(isoStr) {
    if (!isoStr) return "";
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return isoStr;
    }
  },

  getPnLClass(value) {
    const val = Number(value);
    if (val > 0) return "text-positive";
    if (val < 0) return "text-negative";
    return "";
  },

  getRouteBadge(routeName) {
    if (!routeName) return "";
    if (routeName.includes("Alpha")) return `<span class="badge badge-alpha">Route Alpha</span>`;
    if (routeName.includes("Beta")) return `<span class="badge badge-beta">Route Beta</span>`;
    if (routeName.includes("Gamma")) return `<span class="badge badge-gamma">Route Gamma</span>`;
    return `<span class="badge">${routeName}</span>`;
  },

  getStatusBadge(status) {
    if (status === "FLOURISHING") return `<span class="status-tag status-flourishing"><span class="pulse-dot"></span> FLOURISHING</span>`;
    if (status === "STABLE") return `<span class="status-tag status-live"><span class="pulse-dot"></span> STABLE</span>`;
    if (status === "DECLINING") return `<span class="status-tag status-delayed"><span class="pulse-dot"></span> DECLINING</span>`;
    return `<span class="status-tag"><span class="pulse-dot"></span> ${status}</span>`;
  }
};
