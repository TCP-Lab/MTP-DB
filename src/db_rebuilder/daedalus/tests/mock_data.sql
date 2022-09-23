BEGIN;

INSERT INTO gene_ids (ensg, ensg_version_leaf, refseq_gene_id, refseq_gene_id_version, go_terms) 
    VALUES
    (100000000001, 1, 'NM_000000001', 5, NULL),
    (100000000002, 2, 'NM_000000002', 6, 'GO:0000001, GO:0000002'),
    (100000000003, 3, 'NM_000000003', 7, 'GO:0000003'),
    (100000000004, 4, 'NM_000000004', 8, NULL);


INSERT INTO transcript_ids (ensg, enst, is_primary_transcript, pdb_id, refseq_protein_id)
    VALUES
    (100000000001, 20000000001, 1, '1AB2', 'NP_100000001'),
    (100000000001, 20000000002, 0, '2CD3', 'NP_100000002'),
    (100000000002, 20000000003, 1, '4EF5', 'NP_100000003'),
    (100000000002, 20000000004, 0, '6GH7', 'NP_100000004'),
    (100000000003, 20000000005, 1, '8IJ8', 'NP_100000005'),
    (100000000003, 20000000006, 0, '9KL1', 'NP_100000006'),
    (100000000004, 20000000007, 1, '2MN3', 'NP_100000007'),
    (100000000004, 20000000008, 0, '4OP5', 'NP_100000008');

INSERT INTO gene_names (ensg, hugo_gene_symbol, hugo_gene_name, gene_symbol_synonyms)
    VALUES
    (100000000001, 'AAAA', 'AAAA! Longer.', 'AAA, AA, A'),
    (100000000002, 'BBBB', 'BBBB! Longer.', 'BBB, BB'),
    (100000000003, 'CCCC', 'CCCC! Longer.', 'CCC'),
    (100000000004, 'DDDD', 'DDDD! Longer.', NULL);

INSERT INTO iuphar_ids (
    ensg, target_id, target_name, family_id, family_name
) VALUES
    (10000000001, 1, 'target_1', 5, 'fam_1'),
    (10000000002, 20, 'target_2', 60, 'fam_2'),
    (10000000003, 300, 'target_3', 700, 'fam_3'),
    (10000000004, 4000, 'target_4', 8000, 'fam_4');

INSERT INTO iuphar_ligands (
    ligand_id, is_proteic, ensg, gene_symbol, pubchem_sid, is_endogenous, name
) VALUES
    (9009, 1, 10000000010, 'LIG1', NULL, 1, 'Mockerin'),
    (1010, 0, NULL, NULL, 9876, NULL, 'Magicherin'),
    (1111, 1, 10000000020, 'SUPB', NULL, 0, 'Sup Bro'),
    (1212, 0, NULL, NULL, 5432, NULL, 'Panacea');

INSERT INTO iuphar_interaction (
    interaction_id, target_id, ligand_id, is_approved_drug, interaction_type,
    ligand_action, ligand_action_extras, ligand_selectivity, is_primary_target,
    receptor_site, ligand_context
) VALUES
    ('1::9009', 1, 9009, 0, 'covalent binding', 'inhibition', 
    NULL, 'high', 1, 'intracellular', 'some_context'),
    ('20::1010', 20, 1010, 1, 'reversible', 'activation', 
    'Does not work when bananas are involved', 0, 'low', 'in the middle', 'No context at all'),
    ('300::1111', 300, 1111, 0, 'covalent binding', 'inhibition', 
    'Works only in the presence of Elrond', 0, 'medium', 'extracellular', NULL),
    ('4000::1212', 4000, 1212, 1, 'covalent binding', NULL, 
    NULL, 1, NULL, NULL, NULL);

INSERT INTO tcdb_ids (
    enst, tcid, tcid_type, tcid_subtype, tcid_family, tcid_subfamily
) VALUES
    (20000000001, '1.A.1.1.1', 1, '1.A', '1.A.1', '1.A.1.1'),
    (20000000002, '2.B.2.1.1', 2, '2.B', '2.B.1', '2.B.1.1'),
    (20000000003, '1.A.2.4.1', 1, '1.A', '1.A.2', '1.A.2.4'),
    (20000000004, '5.C.2.1.5', 2, '5.C', '5.C.2', '5.C.2.1');

INSERT INTO tcdb_subfamily (
    tcid_subfamily, subfamily_name
) VALUES
    ('1.A.1.1', 'Channel Protein Everest Subfamily'),
    ('2.B.1.1', 'Exchanger Protein Beta'),
    ('1.A.2.4', 'Channel Protein Banana'),
    ('5.C.2.1', 'Transmembrane elecronic carrier Subfamily Tron');

INSERT INTO tcdb_families (
    tcid_family, family_name, is_superfamily
) VALUES
    ('1.A.1', 'Mountain Channels', 1),
    ('2.B.1', 'Greek exchangers', 1),
    ('1.A.2', 'Hill-like Channels', 0),
    ('5.C.2', 'Virtual electron carriers', 0);

INSERT INTO gene_onthology (
    term, term_name, onthology_type 
) VALUES
    ('GO:0000001', 'Awesome property', 'biological_process'),
    ('GO:0000002', 'Lame property', 'biological_process'),
    ('GO:0000003', 'In the cell', 'cellular_compartment'),
    ('GO:0000004', 'On earth', 'cellular_compartment');

INSERT INTO channels (
    enst, is_active_transport, conductance, permeability
) VALUES
    (20000000001, 1, 'very small', 'Na'),
    (20000000002, 1, 'small', 'Ca, Na'),
    (20000000003, 1, 'big', 'Si'),
    (20000000004, 1, 'huge', 'Cations');

INSERT INTO carriers (
    enst, class, is_secondary, to_lumen_pubchem_id, to_exterior_pubchem_id,
    rate_coefficient, rate_maximum
) VALUES
    (20000000005, 'symport', 1, 'Na, Ca', 'N/A', '1.23', '3'),
    (20000000006, 'antiport', 0, 'Si', 'N/A', '1', '2'),
    (20000000007, 'monoport', 0, 'Cations', 'N/A', '22.5', '11'),
    (20000000008, 'manyport', 1, 'Everything', 'Everything Else', '1000', '3000');

END;