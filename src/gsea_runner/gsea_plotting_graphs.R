#!/usr/bin/env Rscript

if (sys.nframe() == 0L) {
  # Parsing arguments
  requireNamespace("argparser")

  parser <- argparser::arg_parser("Run GSEA on DEG tables")

  parser |>
    argparser::add_argument(
      "input_gsea_results", help="Folder with GSEA output .csv files to read.", type="character"
    ) |>
    argparser::add_argument(
      "output_dir", help = "Output directory to save files in",
      type = "character"
    ) |>
    argparser::add_argument(
      "--png", help = "If specified, saves plots as PNG. Use `--res` to set the resolution",
      flag = TRUE, type = "logical"
    ) |>
    argparser::add_argument(
      "--res", help = "Resolution of PNG plots, in pixels per inch.",
      default= 400, type = "logical"
    ) |>
    argparser::add_argument(
      "--width", help = "Plot width, in inches.",
      default = 10, type = "numerical"
    ) |>
    argparser::add_argument(
      "--height", help = "Plot height, in inches.",
      default = 10, type = "numerical"
    ) -> parser

  args <- argparser::parse_args(parser)
}


library(tidyverse)
requireNamespace("RColorBrewer")
requireNamespace("igraph")
requireNamespace("uuid")
library(ggraph) # This needs to be a library() call
library(grid)
library(assertthat)

#' Read a series of .csv files from a directory
#'
#' This is for the output files from fgsea::fgsea in the `run_gsea.R` file
#'
#' @param input_dir The input directory to read from. Reads ALL files.
#'
#' @returns A list with file names as names and tibbles as values.
read_results <- function(input_dir) {
  files <- list.files(input_dir)
  res <- list()
  for (i in seq_along(files)) {
    res[[files[i]]] <- read_csv(file.path(input_dir, files[i]), show_col_types = FALSE)
  }
  return(res)
}

#' Convert a result table to a graph structure for plotting
#'
#' The graph structure is derived from the list names, using `\` as node name
#' splitting character. E.g. `a\b\c` becomes `a -> b -> c` in the graph.
#'
#' @param result The data.frame with the GSEA results. Needs at least the
#'   "pathway", "NES" and "padj" columns, to add the data to the graph.
#' @param base_edges A data.frame with base edges
result_to_graph <- function(result) {
  # This fun gets a results list (w/o plots) and converts it to a dataframe
  # that can be used by ggraph and igraph

  # Tiny wrapper to get the end of the file name
  end_of <- function(string) {
    parts <- str_split_1(string, "\\/")
    return(parts[length(parts)])
  }

  remove_leading_backslash <- function(str) {
    str_remove(str, "^/")
  }

  # We have to assign unique IDs to every node, so that we have
  # no ambiguity when rebuilding the graph
  available_nodes <- sapply(result$pathway, end_of)
  uuids <- data.frame(
    paths = sapply(result$pathway, remove_leading_backslash),
    human_node_name = available_nodes,
    uuids = uuid::UUIDgenerate(n = length(available_nodes))
  )

  to_uuid <- function(str) {
    uuids$uuids[uuids$paths == str]
  }

  # We can now build the frame of edges, where each row is a source -> sink
  # edge.
  insert <- function(x, item) {
    x[[length(x) + 1]] <- item

    x
  }

  edges <- list()
  for (i in seq_along(uuids$paths)) {
    # For every path, we need to reconstruct the graph
    parts <- str_split_1(uuids$paths[i], "\\/")

    for (k in seq_along(parts)) {
      if (length(parts) == 1) {
        # This is a root node, we need to skip it.
        next
      }
      if (k + 1 > length(parts)) {
        # We have arrived at the last item in the list. We can skip it.
        next
      }
      new_row <- c(
        # The current node
        to_uuid(paste0(parts[1:k], collapse="/")),
        # The next node
        to_uuid(paste0(parts[1:(k + 1)], collapse="/"))
      )
      assert_that(length(new_row) == 2)
      edges <- insert(edges, new_row)
    }
  }

  edges <- as.data.frame(do.call(rbind, edges))
  colnames(edges) <- c("source", "sink")

  edges |> distinct() -> edges

  # Now we have a frame of edges, so we can grab the node data from the results

  vertice_data <- list()
  vertices <- unique(unlist(edges))
  for (i in seq_along(vertices)) {
    item <- vertices[i]

    item_data <- c(
      item,
      uuids$human_node_name[uuids$uuids == item],
      unlist(result[result$pathway == paste0("/", uuids$paths[uuids$uuids == item]), c("NES", "padj")])
    )

    assert_that(length(item_data) == 4)

    vertice_data[[i]] <- item_data

  }
  vertice_frame <- as.data.frame(do.call(rbind, vertice_data))

  colnames(vertice_frame) <- c("uuid", "human_label", "NES", "padj")
  # Convert to numbers
  vertice_frame |> mutate(NES = as.numeric(NES), padj = as.numeric(padj)) -> vertice_frame

  vertice_frame$NES[is.na(vertice_frame$NES)] <- 0

  return(igraph::graph_from_data_frame(edges, vertices = vertice_frame))
}

# ----

make_colours <- function(palette, values) {
  colour_fun <- colorRamp(palette)

  values <- (values-min(values))/(max(values)-min(values))

  col_values <- colour_fun(values)

  colours <- apply(col_values, 1, function(x) {
    x[is.na(x)] <- 0
    rgb(x[1], x[2], x[3], maxColorValue = 255)
  })
}

parse_name_to_label <- function(x) {
  sapply(x, \(value){
    if (startsWith(value, "carried_solute::")) {
      value <- str_remove(value, "carried_solute::")
    }

    replacements <- c(
      "outward", "inward", "voltage independent", "voltage gated", "not LG", "ligand gated",
      "voltage independent", "voltage gated", "not LG", "LG", ""
    )
    names(replacements) <- c(
      "direction::out", "direction::in", "is_voltage_gated::0", "is_voltage_gated::1",
      "is_ligand_gated::0", "is_ligand_gated::1", "is_voltage_gated::0.0", "is_voltage_gated::1.0",
      "is_ligand_gated::0.0", "is_ligand_gated::1.0", "whole_transportome"
    )

    if (value %in% names(replacements)) {
      value <- replacements[value]
    }

    value
  })
}

get_point_coords <- function(p) {
  ggp <- ggplot_build(p)

  return(ggp$data[[1]][, c("label", "x", "y")])

}

calculate_angle_from_pos <- function(pos_dataframe, specials = NULL) {
  pos_dataframe$angle <- apply(pos_dataframe[,c("x", "y")], 1, \(x) {atan(x[2] / x[1])})
  # Replace every NaN (like, 0/0) with angle = 0
  pos_dataframe[is.na(pos_dataframe)] <- 0

  # Change the positions to be slightly more outward
  # 1. we calculate the hypothenuse + the dodge value
  scaling_factor <- 0.01
  new_coords <- apply(pos_dataframe, 1, \(row) {
    name <- row["label"]; y <- as.numeric(row["y"]); angle <- as.numeric(row["angle"])
    # It's important that we
    x <- as.numeric(row["x"]);
    hypothenuse <- sqrt(x ** 2 + y ** 2) + (min(max(str_length(name), 5), 15) * scaling_factor)
    if (y < 0) {
      new_y <- hypothenuse * abs(sin(angle)) * - 1
    } else {
      new_y <- hypothenuse * abs(sin(angle))
    }

    if (x < 0) {
      new_x <- hypothenuse * abs(cos(angle)) * -1
    } else {
      new_x <- hypothenuse * abs(cos(angle))
    }

    return(c(new_x, new_y))
  })

  pos_dataframe$dodged_x <- new_coords[1,] # it is filled row-wise
  pos_dataframe$dodged_y <- new_coords[2,]

  # From radians to degrees
  pos_dataframe$angle <- pos_dataframe$angle * 180 / pi

  # Detect which labels do not lay on the outer circle, so that we can
  # label them differently
  hypothenuses <- sqrt(pos_dataframe$x ** 2 + pos_dataframe$y ** 2)

  pos_dataframe
}

plot_result <- function(result, title = "") {

  data_graph <- result_to_graph(result)
  colours <- make_colours(c("blue", "gray", "red"), as.numeric(igraph::vertex_attr(data_graph, "NES")))

  # "Plot" a graph with just the labels
  p <- ggraph(data_graph, layout='igraph', algorithm = "tree", circular = TRUE) +
    coord_fixed() +
    geom_node_text(
      aes(
        label = parse_name_to_label(igraph::vertex_attr(data_graph, "human_label"))
      )
    )

  plot_labels <- calculate_angle_from_pos(get_point_coords(p))

  expand_vec <- c(0.05, 0.05)

  # Now we have the angles, we can build the real plot
  pp <- ggraph(data_graph, layout='igraph', algorithm = "tree", circular = TRUE) +
    geom_edge_diagonal(aes(alpha = after_stat(index)), show.legend = FALSE) +
    coord_fixed() +
    scale_edge_colour_distiller(palette = "RdPu") +
    geom_node_point(
      aes(
        size = -log10(as.numeric(igraph::vertex_attr(data_graph, "padj"))),
        color = colours
      ),
      alpha = (as.numeric(as.numeric(igraph::vertex_attr(data_graph, "padj")) < 0.05) + 0.2 ),
      show.legend = setNames(c(FALSE, FALSE, FALSE), c("color", "size", "alpha"))
    ) +
    geom_node_text(
      aes(
        x = plot_labels$dodged_x,
        y = plot_labels$dodged_y,
        label = plot_labels$label
      ), angle = plot_labels$angle,
      size = 2.5
    ) +
    scale_color_manual(values = colours, limits = colours, guide = guide_legend(title = "NES")) +
    theme(legend.position = "bottom", panel.background = element_blank()) +
    # Give more space to the plot area so the lables are drawn properly
    scale_x_continuous(expand = expand_vec) + scale_y_continuous(expand = expand_vec) +
    ggtitle(title)

  return(pp)
}

plot_all_results <- function(results, out_dir, width=10, height=8, png = TRUE, res = 400) {
  for (i in seq_along(results)) {
    cat(paste0("Saving ", names(results)[i], "...\n"))
    if (png) {
      png(
        file.path(out_dir, paste0(names(results)[i], ".png")),
        width = width, height = height,
        units = "in",
        res = res
      )
    } else {
      pdf(
          file.path(
          out_dir, paste0(names(results)[i], ".pdf")),
          width = width, height = height
        )
    }
    print(
      plot_result(results[[i]], title = names(results)[i])
    )
    graphics.off()
  }
}

# DEBUGGING ONLY
if (FALSE) {
  results <- read_results("/home/hedmad/Files/data/mtpdb/gsea_output/")

  plot_all_results(results, "~/Files/data/mtpdb/graphs/")
}

if (sys.nframe() == 0L) {
  results <- read_results(args$input_gsea_results)

  plot_all_results(
    results, args$output_dir, args$width, args$height, args$png, args$res
  )
}
