# biocManager::install("fgsea")

library(tidyverse)

requireNamespace("biomaRt")
requireNamespace("fgsea")

options(readr.num_columns = 0)

load_genesets <- function(folder) {
  # Load genesets as made by "make_genesets.py"
  file_names <- list.files(folder)
  file_paths <- file.path(folder, file_names)

  data <- list()
  for (i in seq_along(file_names)) {
    data[[ file_names[i] ]] <- read_table(file_paths[i], col_names = "ensg")[["ensg"]]
  }

  filter_values <- reduce(data, c)
  filter_values <- unique(filter_values)

  # Convert from ENSG to gene symbol
  embl <- biomaRt::useEnsembl(biomart = "genes")
  hs.embl <- biomaRt::useDataset(dataset = "hsapiens_gene_ensembl", mart = embl)
  annotations <- biomaRt::getBM(
    attributes = c("ensembl_gene_id", "hgnc_symbol"),
    filters = "ensembl_gene_id",
    values = filter_values,
    mart = hs.embl
  )

  ensg_to_symbol <- function(ensgs) {
    symbols <- annotations$hgnc_symbol[annotations$ensembl_gene_id %in% ensgs]

    return(symbols)
  }

  data <- lapply(data, ensg_to_symbol)

  return(data)
}

extract_ranks <- function(deg_file) {
  data <- read_csv(deg_file, show_col_types = FALSE)

  data |> select(all_of(c("SYMBOL", "t"))) -> data
  data <- na.omit(data)

  named_vec <- data$t
  names(named_vec) <- data$SYMBOL

  embl <- biomaRt::useEnsembl(biomart = "genes")
  hs.embl <- biomaRt::useDataset(dataset = "hsapiens_gene_ensembl", mart = embl)
  annotations <- biomaRt::getBM(
    attributes = c("hgnc_symbol", "gene_biotype"),
    filters = "hgnc_symbol",
    values = names(named_vec),
    mart = hs.embl
  )

  coding <- annotations$hgnc_symbol[annotations$gene_biotype == "protein_coding"]

  named_vec <- named_vec[names(named_vec) %in% coding]

  return(named_vec)
}

run_gsea <- function(genesets, ranks) {
  result <- fgsea::fgsea(
    pathways = genesets,
    stats = ranks
  )

  result
}

plot_gsea <- function(genesets, ranks) {
  results <- list()
  for (i in seq_along(genesets)) {
    p <- fgsea::plotEnrichment(genesets[[i]], ranks)
    results[[names(genesets)[i]]] <- p
  }

  return(results)
}

run_all_gsea <- function(input_data_folder, genesets_folder_path) {
  file_names <- list.files(input_data_folder)
  file_paths <- file.path(input_data_folder, file_names)

  genesets <- load_genesets(genesets_folder_path)

  results <- list()
  for (i in seq_along(file_names)) {
    ranks <- extract_ranks(file_paths[i])

    results[[file_names[i]]] <- run_gsea(genesets, ranks)
    results[[paste0("plot_", file_names[[i]])]] <- plot_gsea(genesets, ranks)
  }

  return(results)
}

save_result <- function(result, out_dir, name, plot = FALSE) {
  out_path <- file.path(out_dir, name)
  
  if (plot) {
    for (i in seq_along(result)) {
      pdf(paste0(out_path, names(result)[i], ".pdf"), width = 12, height = 8)
      print(result[[i]])
      dev.off()
    }
    return(TRUE)
  }
  
  write_csv(result, out_path)
  return(TRUE)
}

save_results <- function(results, out_dir, skip_plots = FALSE) {
  wrap <- function(x, name) {
    print(paste0("Saving ", name))
    
    is_plot <- startsWith(name, "plot")
    if (is_plot & skip_plots) {
      print("Skipped.")
      return()
    }
    save_result(x, out_dir, name, is_plot)
  }
  # I can't make it work with sapply so, get a for loop
  for (i in seq_along(results)) {
    wrap(results[[i]], names(results)[i])
  }
}

select_results <- function(results, plots = FALSE) {
  key <- startsWith(names(results), "plot")
  if (plots) {
    return(results[key])
  } else {
    return(results[! key])
  }
}

results <- run_all_gsea(
  "/home/hedmad/Files/data/mtpdb/input_deg_tables/",
  "/home/hedmad/Files/data/mtpdb/genesets/"
)

save_results(results, out_dir = "/home/hedmad/Files/data/mtpdb/gsea_output/", skip_plots = TRUE)

save_result(
  result = results$`jankyr_Limma - DEG Table tumor-normal.csv`,
  "/home/hedmad/Files/data/mtpdb/gsea_output/",
  "jankyr_Limma - DEG Table tumor-normal.csv",
  plot = FALSE
)

save_result(
  result = results$`plot_jankyr_Limma - DEG Table tumor-normal.csv`,
  "/home/hedmad/Files/data/mtpdb/gsea_output/",
  "plot_jankyr_Limma - DEG Table tumor-normal.csv",
  plot = TRUE
)

res_tables <- select_results(results, plots = FALSE)

summarise_results <- function(result) {
  sig_pathways <- result[result$padj < 0.05, , drop=FALSE]
  
  if (nrow(sig_pathways) == 0) {
    cat("No significant enrichment found.\n")
    return(invisible())
  }
  cat(paste0("Found ", nrow(sig_pathways), " enriched sets.\n"))
  sig_pathways |> arrange(padj) |> select(all_of(c("pathway", "padj", "ES", "NES", "size"))) |> print()
  return(invisible())
}

# TEST

summarise_results(results$`jankyr_Limma - DEG Table tumor-normal.csv`)
summarise_results(results$`jiang_Limma - DEG Table tumor-normal.csv`)
summarise_results(results$`wangh_Limma - DEG Table tumor-normal.csv`)
summarise_results(results$`zhang_Limma - DEG Table tumor-normal.csv`)
