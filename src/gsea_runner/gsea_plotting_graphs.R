library(tidyverse)
requireNamespace("RColorBrewer")
requireNamespace("igraph")
library(ggraph) # This needs to be a library() call
library(grid)

BASE_EDGE_LIST <- as.data.frame(rbind(
  c("whole_transportome", "pores"),
  c("whole_transportome", "transporters"),
  c("pores", "channels"),
  c("pores", "aquaporins"),
  c("transporters", "solute_carriers"),
  c("transporters", "atp_driven"),
  c("atp_driven", "ABC"),
  c("atp_driven", "pumps")
))

LAYERS <- as.data.frame(rbind(
  c("whole_transportome", 1),
  c("pores", 4),
  c("transporters", 4),
  c("atp_driven", 6),
  c("solute_carriers", 6),
  c("channels", 6),
  c("aquaporins", 6),
  c("ABC", 8),
  c("pumps", 8)
))

read_results <- function(input_dir) {
  files <- list.files(input_dir)
  res <- list()
  for (i in seq_along(files)) {
    res[[files[i]]] <- read_csv(file.path(input_dir, files[i]), show_col_types = FALSE)
  }
  return(res)
}

assert <- function(exprs, message) {
  if (!exprs) {
    stop(message)
  }
  cat(paste0("Assertion Passed: ", message, "\n"))
}

name_to_layer <- function(x, layers) {
  # x is the name of a pathway
  keyword <- str_split_1(x, "~")[1]
  value <- layers[layers[,1] == keyword, 2]
  if (x %in% layers[,1]) {
    return(as.numeric(value))
  } else {
    return(as.numeric(value) + 1)
  }
}

result_to_graph <- function(result, base_edges, layers) {
  # This fun gets a results list (w/o plots) and converts it to a dataframe
  # that can be used by ggraph and igraph

  # First, we need to see if the base edges are in the results
  req_nodes <- unique(unlist(base_edges))
  id_nodes <- result$pathway[endsWith(result$pathway, "id.txt")]
  available_nodes <- unique(sapply(id_nodes, \(x){str_split_1(x, "~")[1]}))

  assert(all(req_nodes %in% available_nodes), "All base nodes are available")
  # Ok, now we can add the edges to the resulting graph.

  res <- list()
  # We need all non-id nodes
  for (item in result$pathway[! endsWith(result$pathway, "id.txt")]) {
    res[[item]] <- c(str_split_1(item, "~")[1], item)
  }
  res <- do.call(rbind.data.frame, res)
  colnames(res) <- c(1, 2)

  assert(all(unique(res[,1]) %in% req_nodes), "All nodes are children of base nodes")

  # We can now build the frame
  edge_frame <- rbind(setNames(base_edges, names(res)), res)

  vres <- list()
  vertices <- unique(unlist(edge_frame))
  for (i in seq_along(vertices)) {
    item <- vertices[i]
    if (item %in% req_nodes) {
      # This is a base node. There is an entry with `_id.txt` in there somewhere
      # with the value we need
      vres[[i]] <- c(item, unlist(result[result$pathway == paste0(item, "~id.txt"), c("NES", "padj")]))
    } else {
      vres[[i]] <- c(item, unlist(result[result$pathway == item, c("NES", "padj")]))
    }
  }
  vertice_frame <- do.call(rbind.data.frame, vres)
  colnames(vertice_frame) <- c(1, "NES", "padj")

  vertice_frame$NES[is.na(vertice_frame$NES)] <- 0

  # We can now add the layers that the vertices will sit in
  vertice_frame$layers <- sapply(vertice_frame[[1]], name_to_layer, layers = layers)

  return(igraph::graph_from_data_frame(edge_frame, vertices = vertice_frame))
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
  sapply(x, \(x){
    splits <- str_split_1(x, "~")
    value <- if (length(splits) == 1) {
      splits[1]
    } else {
      paste0(splits[2], ": ", str_remove(splits[3], ".txt"))
    }

    if (startsWith(value, "carried_solute")) {
      value <- str_remove(value, "carried_solute: ")
    }

    replacements <- c(
      "outward", "inward", "voltage independent", "voltage gated", "not LG", "ligand gated",
      "voltage independent", "voltage gated", "not LG", "LG", ""
    )
    names(replacements) <- c(
      "direction: out", "direction: in", "is_voltage_gated: 0", "is_voltage_gated: 1",
      "is_ligand_gated: 0", "is_ligand_gated: 1", "is_voltage_gated: 0.0", "is_voltage_gated: 1.0",
      "is_ligand_gated: 0.0", "is_ligand_gated: 1.0", "whole_transportome"
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
  pos_dataframe[hypothenuses - max(hypothenuses) > max(hypothenuses) * 0.001,] |> print()

  pos_dataframe
}

plot_result <- function(result, base_edges, layers, title = "") {

  data_graph <- result_to_graph(result, base_edges, layers)
  colours <- make_colours(c("blue", "gray", "red"), as.numeric(igraph::vertex_attr(data_graph, "NES")))

  # "Plot" a graph with just the labels
  p <- ggraph(data_graph, layout='igraph', algorithm = "tree", circular = TRUE) +
    coord_fixed() +
    geom_node_text(
      aes(
        label = parse_name_to_label(igraph::vertex_attr(data_graph, "name"))
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

plot_result(results$`wangh_Limma - DEG Table tumor-normal.csv`, base_edges = BASE_EDGE_LIST, LAYERS)

plot_all_results <- function(results, base_edges, layers, out_dir, width=10, height=8, png = TRUE) {
  for (i in seq_along(results)) {
    cat(paste0("Saving ", names(results)[i], "...\n"))
    if (png) {
      png(
        file.path(out_dir, paste0(names(results)[i], ".png")),
        width = width, height = height,
        units = "in",
        res = 400
      )
    } else {
      pdf(
          file.path(
          out_dir, paste0(names(results[i], ".png")),
          width = width, height = height
        )
      )
    }
    print(
      plot_result(results[[i]], base_edges = base_edges, layers = layers, title = names(results)[i])
    )
    graphics.off()
  }
}

results <- read_results("/home/hedmad/Files/data/mtpdb/gsea_output/")

plot_all_results(results, BASE_EDGE_LIST, LAYERS, "~/Files/data/mtpdb/graphs/")
