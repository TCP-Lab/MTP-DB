library(tidyverse)
requireNamespace("RColorBrewer")
requireNamespace("igraph")

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
  c("pores", 2),
  c("transporters", 2),
  c("atp_driven", 3),
  c("solute_carriers", 3),
  c("channels", 3),
  c("aquaporins", 3),
  c("ABC", 4),
  c("pumps", 4)
))

read_results <- function(input_dir) {
  files <- list.files(input_dir)
  res <- list()
  for (i in seq_along(files)) {
    res[[files[i]]] <- read_csv(file.path(input_dir, files[i]), show_col_types = FALSE)
  }
  return(res)
}

results <- read_results("/home/hedmad/Files/data/mtpdb/gsea_output/")

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
  
  # We can now add the layers that the vertices will sit in
  vertice_frame$layers <- sapply(vertice_frame[[1]], name_to_layer, layers = layers)
  
  return(igraph::graph_from_data_frame(edge_frame, vertices = vertice_frame))
}

graph <- result_to_graph(results$`jankyr_Limma - DEG Table tumor-normal.csv`, BASE_EDGE_LIST, LAYERS)
