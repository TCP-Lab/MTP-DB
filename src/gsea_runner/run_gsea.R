# biocManager::install("fgsea")

library(tidyverse)

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


results <- run_all_gsea("/home/hedmad/Desktop/test_gsea_data/", "/home/hedmad/Files/repos/MTP-DB/src/geneset_maker/out/")


# TEST

genesets <- load_genesets("/home/hedmad/Files/repos/MTP-DB/src/geneset_maker/out/")
ranks <- extract_ranks("/home/hedmad/Desktop/test_gsea_data/wangh_Limma - DEG Table tumor-normal.csv")

test_gsea <- run_gsea(genesets, ranks)

fgsea::plotGseaTable(genesets, ranks, test_gsea)
