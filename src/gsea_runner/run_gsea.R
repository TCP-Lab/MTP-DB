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

extract_ranks <- function(deg_file, biomart_data) {
  data <- read_csv(deg_file, show_col_types = FALSE)

  if (! "SYMBOL" %in% colnames(data)) {
    cat("SYMBOL not found in colnames. Attempting to grab it from ids...\n")
    if ("id" %in% colnames(data)) {
      relevant_data <- biomart_data[biomart_data$ensembl_gene_id %in% data$id, c("ensembl_gene_id", "hgnc_symbol")]
      data <- merge(
        data, relevant_data, by.y = "ensembl_gene_id", by.x = "id",
        all.y = FALSE, all.x = TRUE, sort = FALSE
      )
      data |> rename(SYMBOL = hgnc_symbol) -> data
    } else {
      stop("Cannot find id column. No symbols!")
    }
  }

  # Patch to use DESeq2 data
  if ("stat" %in% colnames(data)) {
    cat("Converting stat to t - for compatibility...\n")
    data |> rename(t = stat) -> data
  }

  data |> select(all_of(c("SYMBOL", "t"))) -> data
  data <- na.omit(data)

  named_vec <- data$t
  names(named_vec) <- data$SYMBOL

  coding <- biomart_data$hgnc_symbol[biomart_data$gene_biotype == "protein_coding"]

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

run_all_gsea <- function(input_data_folder, genesets_folder_path, biomart_data) {
  file_names <- list.files(input_data_folder)
  file_paths <- file.path(input_data_folder, file_names)

  cat("Loading genesets...\n")
  genesets <- load_genesets(genesets_folder_path)

  results <- list()
  for (i in seq_along(file_names)) {
    cat(paste0("Running GSEA on ", file_names[i], "\n"))
    ranks <- extract_ranks(file_paths[i], biomart_data)

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

embl <- biomaRt::useEnsembl(biomart = "genes")
hs.embl <- biomaRt::useDataset(dataset = "hsapiens_gene_ensembl", mart = embl)
ensg_data <- biomaRt::getBM(
  attributes = c("ensembl_gene_id", "hgnc_symbol", "gene_biotype"),
  mart = hs.embl
)

results <- run_all_gsea(
  "/home/hedmad/Files/data/mtpdb/input_deg_tables/",
  "/home/hedmad/Files/data/mtpdb/genesets/",
  ensg_data
)

save_results(results, out_dir = "/home/hedmad/Files/data/mtpdb/gsea_output/", skip_plots = TRUE)
