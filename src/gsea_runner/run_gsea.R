#!/usr/bin/env Rscript

# This script runs GSEA on all the DEG tables with all the genesets
# and saves the resulting deg tables to an output folder.

# If you are running this from RStudio, you can skip this >>>>>>>>>>>>>>>>>>
if (sys.nframe() == 0L) {
  # Parsing arguments
  requireNamespace("argparser")

  parser <- argparser::arg_parser("Run GSEA on DEG tables")

  parser |>
    argparser::add_argument(
      "input_deg_folder", help="Folder with DEG tables to run GSEA on.", type="character"
    ) |>
    argparser::add_argument(
      "input_genesets_folder", help = "Folder with input genesets as .txt files",
      type = "character"
    ) |>
    argparser::add_argument(
      "output_dir", help = "Output directory",
      type = "character"
    ) |>
    argparser::add_argument(
      "--low-memory", help = "If specified, saves only output tables, skipping plots, and using less memory.",
      flag = TRUE, type = "logical"
    ) |>
    argparser::add_argument(
      "--save-plots", help = "If specified, also save GSEA plots alongside tables.",
      flag = TRUE, type = "logical"
    ) -> parser

  args <- argparser::parse_args(parser)
}
# To here <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

requireNamespace("biomaRt")
requireNamespace("fgsea")
library(tidyverse, quietly = TRUE)

# This suppresses the messages from readr::read_table
options(readr.num_columns = 0)

load_genesets <- function(folder, biomart_data) {
  #' Load all genesets from FOLDER.
  #'
  #' Genesets should have been made by make_genests.py
  #'
  #' @param folder The folder to find files in, all in .csv format.
  #' @param biomart_data A data.frame with at least the "ensembl_gene_id" and
  #'   "hgnc_symbol" columns, with the correspondence from ENSG to symbol.
  #'   Such a table can be retrieved from Biomart with biomaRt.
  #' @returns A list of vectors, each with the gene symbols of that gene set

  files <- list.files(folder, full.names = TRUE, recursive = TRUE)

  data <- list()
  for (file in files) {
    file |> str_remove("\\/data\\.txt$") |> str_remove(paste0("^", folder)) -> id
    data[[ id ]] <- read_table(file, col_names = "ensg")[["ensg"]]
  }

  filter_values <- reduce(data, c)
  filter_values <- unique(filter_values)

  # Convert from ENSG to gene symbol
  biomart_data |> select(all_of(c("ensembl_gene_id", "hgnc_symbol"))) -> biomart_data
  ensg_to_symbol <- function(ensgs) {
    symbols <- biomart_data$hgnc_symbol[biomart_data$ensembl_gene_id %in% ensgs]

    return(symbols)
  }

  data <- lapply(data, ensg_to_symbol)

  return(data)
}

extract_ranks <- function(deg_file, biomart_data) {
  #' Make a frame ready for GSEA from a DEG file, made by BioTEA or DESeq2.
  #'
  #' Some compatibility is needed to parse DESeq2 files, as they have no
  #' "SYMBOL" column.
  #'
  #' @param deg_file (full) Path to the DEG file that needs to be extracted, as .csv.
  #' @param biomart_data A data.frame with at least the "ensembl_gene_id" and
  #'   "gene_biotype" columns.
  #'   Such a table can be retrieved from Biomart with biomaRt.
  #'
  #' @returns A named vector of gene_names : statistic, ready for fgsea::fgsea
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


#' Run GSEA with many genesets on some data
#'
#' This is a tiny wrapper for future compatibility in case we need to change
#' from fgsea.
#'
#' @param genesets A list of genesets to check, with each geneset a vector of
#'   gene names.
#' @param ranks A named list of gene names: statistic to use as ranked list for gsea.
#'
#' @returns A table with GSEA results. See fgsea:fgsea for details.
run_gsea <- function(genesets, ranks) {
  result <- fgsea::fgsea(
    pathways = genesets,
    stats = ranks
  )

  result
}

#' (run and) Plot GSEA
#'
#' @param genesets A list of genesets to check, with each geneset a vector of
#'   gene names.
#' @param ranks A named list of gene names: statistic to use as ranked list for gsea.
#'
#' @returns A list of geneset: ggplot object with the generated GSEA plots.
plot_gsea <- function(genesets, ranks) {
  results <- list()
  for (i in seq_along(genesets)) {
    p <- fgsea::plotEnrichment(genesets[[i]], ranks)
    results[[names(genesets)[i]]] <- p
  }

  return(results)
}


#' Run GSEA on all DEG tables in a folder, with all genesets from another folder.
#'
#' @param input_data_folder (Full) path to the input data folder with the DEG
#'   tables to be loaded with `extract_ranks`.
#' @param output_dir The output directory to save output files to. If NA, does
#'   not save files, and instead returns a list of results.
#' @param genesets_folder_patdh (Full) path to the folder with genesets, as .txt
#'   files with one gene id per row.
#' @param biomart_data A data.frame with at least the "ensembl_gene_id",
#'   "hgnc_symbol" and "gene_biotype" columns.
#'   Such a table can be retrieved from Biomart with biomaRt.
#'
#' @returns A list of values with file names as names and GSEA results as values.
run_all_gsea <- function(input_data_folder, genesets_folder_path, biomart_data, output_dir = NA) {
  file_names <- list.files(input_data_folder)
  file_paths <- file.path(input_data_folder, file_names)

  cat("Loading genesets...\n")
  genesets <- load_genesets(genesets_folder_path, biomart_data = biomart_data)

  results <- list()
  for (i in seq_along(file_names)) {
    cat(paste0("Running GSEA on ", file_names[i], "\n"))
    ranks <- extract_ranks(file_paths[i], biomart_data)

    if (! is.na(output_dir)) {
      result <- run_gsea(genesets, ranks)

      cat(paste0("Saving data to ", paste0(file.path(output_dir, file_names[i]), ".csv"), "\n"))
      save_result(result, output_dir, file_names[i])
    } else {
      results[[file_names[i]]] <- run_gsea(genesets, ranks)
      results[[paste0("plot_", file_names[[i]])]] <- plot_gsea(genesets, ranks)
    }
  }

  if (length(results) > 0) {
    return(results)
  }
  return(NULL)
}


#' Save a result from `run_all_gsea` to a file.
#'
#' @param result An item from a list made by `run_all_gsea`.
#' @param out_dir The output directory.
#' @param name The name to give to the output file
#' @param plot If `result` is a plot, pass plot = TRUE to treat it as one.
#'
#' @returns NULL
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

#' Save all results from `run_all_gsea` to a series of files.
#'
#' Detects plots to save from their name in the list, starting with `plot`.
#' Filenames are taken from the corresponding list names.
#'
#' @param results The list generated by `run_all_gsea`.
#' @param out_dir The output directory to save to.
#' @param skip_plots If TRUE, does not save plots to output directory.
#'
#' @returns NULL
save_results <- function(results, out_dir, skip_plots = FALSE) {
  wrap <- function(x, name) {
    cat(paste0("Saving ", name, "..."))

    is_plot <- startsWith(name, "plot")
    if (is_plot & skip_plots) {
      cat(" .. Skipped\n")
      return()
    }
    save_result(x, out_dir, name, is_plot)
    cat(".. OK\n")
  }
  # I can't make it work with sapply so, get a for loop
  for (i in seq_along(results)) {
    wrap(results[[i]], names(results)[i])
  }
}

if (FALSE){ # LOCAL DEBUGGING RUN ONLY

embl <- biomaRt::useEnsembl(biomart = "genes")
hs.embl <- biomaRt::useDataset(dataset = "hsapiens_gene_ensembl", mart = embl)
ensg_data <- biomaRt::getBM(
  attributes = c("ensembl_gene_id", "hgnc_symbol", "gene_biotype"),
  mart = hs.embl
)

results <- run_all_gsea(
  "/home/hedmad/Files/data/mtpdb/input_deg_tables/",
  "/home/hedmad/Files/data/mtpdb/genesets/bottomup/root/",
  ensg_data
)

save_results(results, out_dir = "/home/hedmad/Files/data/mtpdb/gsea_output/", skip_plots = TRUE)

} # ----------------------------------------------------------------------------

# If you are running this from RStudio, you can skip this >>>>>>>>>>>>>>>>>>
if (sys.nframe() == 0L) {

  if (args$low_memory && args$save_plots) {
    cat("WARNING: Low memory mode. Cannot save plots!")
  }

  embl <- biomaRt::useEnsembl(biomart = "genes")
  hs.embl <- biomaRt::useDataset(dataset = "hsapiens_gene_ensembl", mart = embl)
  ensg_data <- biomaRt::getBM(
    attributes = c("ensembl_gene_id", "hgnc_symbol", "gene_biotype"),
    mart = hs.embl
  )

  if (args$low_memory) {
    run_all_gsea(
      args$input_deg_folder,
      args$input_genesets_folder,
      ensg_data,
      output_dir = args$output_dir
    )
  } else {
    results <- run_all_gsea(
      args$input_deg_folder,
      args$input_genesets_folder,
      ensg_data
    )

    save_results(results, out_dir = args$output_dir, skip_plots = !args$save_plots)
  }
}
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
