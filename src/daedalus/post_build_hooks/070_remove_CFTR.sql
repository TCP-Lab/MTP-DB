-- CFTR is both in the ABC-transporters and Ion channels lists, for
-- evolutionistic reasons. Fede believes that it is more correct to include
-- it only in the channels list, so we delete it here.
DELETE FROM ABC_transporters WHERE ensg == "ENSG00000001626";
