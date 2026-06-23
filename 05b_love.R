#!/usr/bin/env Rscript
# ─────────────────────────────────────────────────────────────────────
# COVID-19 Severity × SDoH — eFigure 1: PSM Balance (Love Plot)
#
# Plots pre- vs post-matching |SMD| for the 3 PSM targeting variables
# only.  Two panels: (a) All of Us, (b) MarketScan.
#
# Design rationale:
#   The propensity score model targets three encounter-density proxies
#   (enrollment date, diagnosis count, EHR/coverage length) to balance
#   informative presence bias.  Confounders (demographics, comorbidities,
#   SDoH) are adjusted in the conditional logistic regression model,
#   not the matching step.  The balance diagnostic therefore shows only
#   the variables the PSM was designed to balance.
#
# Inputs:
#   results/aou_v7/07c_smd_pre_matching.csv
#   results/ms/07c_smd_pre_matching.csv
#
# Outputs:
#   results/figures/efig1_love_plot.pdf
#   results/figures/efig1_love_plot.png
#
# Usage:  Rscript 05b_love.R [results_dir]
# ─────────────────────────────────────────────────────────────────────

# ── Packages ─────────────────────────────────────────────────────────
for (pkg in c("ggplot2", "dplyr", "readr", "cowplot")) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg)
}
library(ggplot2)
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))
library(cowplot)

# ── Paths ────────────────────────────────────────────────────────────
args    <- commandArgs(trailingOnly = TRUE)
BASE    <- if (length(args) >= 1) args[1] else "results"
FIG_DIR <- file.path(BASE, "figures")
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

aou_path <- file.path(BASE, "aou_v7", "07c_smd_pre_matching.csv")
ms_path  <- file.path(BASE, "ms",     "07c_smd_pre_matching.csv")

cat(strrep("=", 60), "\n")
cat("eFIGURE 1: PSM Balance Love Plot\n")
cat(strrep("=", 60), "\n")

# ── Human-readable variable labels ───────────────────────────────────
VAR_LABELS <- c(
  enrollment_ord    = "Enrollment date (ordinal)",
  num_diagnosis     = "Number of diagnoses",
  ehr_length_days   = "EHR length (days)",
  coverage_span_days = "Coverage span (days)"
)

# ── Wong/Okabe-Ito palette ───────────────────────────────────────────
C_PRE  <- "#D55E00"  # vermillion: before matching
C_POST <- "#0072B2"  # blue: after matching

# ── JAMIA theme ──────────────────────────────────────────────────────
theme_jamia <- function(base_size = 8) {
  theme_bw(base_size = base_size, base_family = "Arial") +
    theme(
      panel.grid.major.y = element_blank(),
      panel.grid.minor   = element_blank(),
      panel.grid.major.x = element_line(color = "#E8E8E8", linewidth = 0.3),
      panel.border       = element_rect(color = "black", linewidth = 0.5),
      axis.ticks.y       = element_blank(),
      axis.ticks.x       = element_line(linewidth = 0.4),
      axis.text          = element_text(size = 7, color = "black"),
      axis.title         = element_text(size = 8),
      legend.position    = "bottom",
      legend.text        = element_text(size = 7),
      legend.title       = element_blank(),
      legend.key.size    = unit(0.35, "cm"),
      legend.margin      = margin(t = -2),
      plot.title         = element_text(size = 8, face = "bold", hjust = 0),
      plot.margin        = margin(t = 5, r = 8, b = 2, l = 5)
    )
}

# ── Read and reshape one site's SMD file ─────────────────────────────
read_smd <- function(path, site_label) {
  df <- read_csv(path, show_col_types = FALSE)

  # Filter to matching variables only (exclude distance if present)
  df <- df %>% filter(variable != "distance")

  # Clean labels
  df$label <- ifelse(df$variable %in% names(VAR_LABELS),
                     VAR_LABELS[df$variable], df$variable)

  # Reshape to long: pre vs post
  pre  <- df %>%
    transmute(site = site_label, label, phase = "Before matching",
              abs_smd = abs(smd_unadjusted))
  post <- df %>%
    transmute(site = site_label, label, phase = "After matching",
              abs_smd = abs(smd_adjusted))

  bind_rows(pre, post)
}

# ── Build data ───────────────────────────────────────────────────────
dfs <- list()

if (file.exists(aou_path)) {
  dfs$aou <- read_smd(aou_path, "All of Us")
  cat("  AoU: ", nrow(dfs$aou) / 2, " matching variables\n", sep = "")
} else {
  cat("  WARNING:", aou_path, "not found\n")
}

if (file.exists(ms_path)) {
  dfs$ms <- read_smd(ms_path, "MarketScan")
  cat("  MS:  ", nrow(dfs$ms) / 2, " matching variables\n", sep = "")
} else {
  cat("  WARNING:", ms_path, "not found\n")
}

if (length(dfs) == 0) {
  cat("  No SMD files found, skipping love plot.\n")
  quit(status = 0)
}

# ── Plot function for one panel ──────────────────────────────────────
make_love_panel <- function(df, panel_title) {

  # Order variables by pre-matching |SMD| (largest at top)
  pre_order <- df %>%
    filter(phase == "Before matching") %>%
    arrange(abs_smd) %>%
    pull(label)
  df$label <- factor(df$label, levels = pre_order)

  # Shape mapping
  df$phase <- factor(df$phase, levels = c("Before matching", "After matching"))

  p <- ggplot(df, aes(x = abs_smd, y = label, color = phase, shape = phase)) +
    geom_vline(xintercept = 0.10, linetype = "dashed", color = "#888888",
               linewidth = 0.4) +
    geom_vline(xintercept = 0.05, linetype = "dotted", color = "#AAAAAA",
               linewidth = 0.3) +
    geom_segment(
      data = df %>%
        select(label, phase, abs_smd) %>%
        tidyr::pivot_wider(names_from = phase, values_from = abs_smd),
      aes(x = `Before matching`, xend = `After matching`,
          y = label, yend = label),
      inherit.aes = FALSE,
      color = "#CCCCCC", linewidth = 0.5
    ) +
    geom_point(size = 3, stroke = 0.3) +
    scale_color_manual(
      values = c("Before matching" = C_PRE, "After matching" = C_POST)
    ) +
    scale_shape_manual(
      values = c("Before matching" = 17, "After matching" = 16)  # triangle, circle
    ) +
    scale_x_continuous(
      limits = c(0, 0.65),
      expand = expansion(mult = c(0, 0))
    ) +
    annotate("text", x = 0.10, y = 0.6, label = "|SMD| = 0.10",
             hjust = -0.1, size = 2.3, color = "#888888") +
    labs(x = "|Standardized Mean Difference|", y = NULL, title = panel_title) +
    theme_jamia() +
    guides(color = guide_legend(override.aes = list(size = 2.5)))

  p
}

# ── Assemble panels ──────────────────────────────────────────────────
panels <- list()

if (!is.null(dfs$aou)) {
  panels$a <- make_love_panel(dfs$aou, "a   All of Us")
}
if (!is.null(dfs$ms)) {
  panels$b <- make_love_panel(dfs$ms, "b   MarketScan")
}

if (length(panels) == 2) {
  # Side-by-side: shared legend at bottom
  combined <- plot_grid(
    panels$a + theme(legend.position = "none"),
    panels$b + theme(legend.position = "none"),
    ncol = 2, align = "h", axis = "tb",
    rel_widths = c(1, 1)
  )
  legend <- get_legend(panels$a + theme(legend.position = "bottom"))
  final  <- plot_grid(combined, legend, ncol = 1, rel_heights = c(1, 0.08))
  fig_w <- 7.008   # JAMIA double-column (178 mm)
  fig_h <- 2.8     # compact: only 3 rows per panel
} else {
  final <- panels[[1]]
  fig_w <- 3.386   # single column
  fig_h <- 2.5
}

# ── Export ────────────────────────────────────────────────────────────
pdf_path <- file.path(FIG_DIR, "efig1_love_plot.pdf")
png_path <- file.path(FIG_DIR, "efig1_love_plot.png")

ggsave(pdf_path, final, width = fig_w, height = fig_h, device = cairo_pdf)
ggsave(png_path, final, width = fig_w, height = fig_h, dpi = 600)
cat("  Saved:", pdf_path, "\n")
cat("  Saved:", png_path, "\n")

# ── Print summary ────────────────────────────────────────────────────
cat("\n  Balance summary:\n")
for (nm in names(dfs)) {
  d <- dfs[[nm]]
  pre_d  <- d %>% filter(phase == "Before matching")
  post_d <- d %>% filter(phase == "After matching")
  cat(sprintf("  %s:\n", unique(d$site)))
  for (i in seq_len(nrow(pre_d))) {
    cat(sprintf("    %-30s  pre |SMD| = %.4f  ->  post |SMD| = %.4f\n",
                pre_d$label[i], pre_d$abs_smd[i], post_d$abs_smd[i]))
  }
}

cat("\nDone.\n")
