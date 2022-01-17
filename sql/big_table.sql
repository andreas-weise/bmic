-- collects the tables of the normalized, hierarchical schema into a single,
-- unnormalized table with redundant information
WITH halfway_points AS
-- select assumes continuous timestamps per session, no reset per task!
(
 SELECT NULL tsk_id,
        tsk.ses_id, 
        MIN(chu.start_time) + (MAX(chu.end_time) - MIN(chu.start_time)) / 2 ts
 FROM   chunks chu
 JOIN   turns tur
 ON     chu.tur_id == tur.tur_id
 JOIN   tasks tsk
 ON     tur.tsk_id == tsk.tsk_id
 GROUP BY tsk.ses_id

 UNION

 SELECT tur.tsk_id,
        NULL ses_id, 
        MIN(chu.start_time) + (MAX(chu.end_time) - MIN(chu.start_time)) / 2 ts
 FROM   chunks chu
 JOIN   turns tur
 ON     chu.tur_id == tur.tur_id
 GROUP BY tur.tsk_id
), tan (tur_id, ann_index, valence, arousal) AS
(
 SELECT tur_id,
        ann_index,
        valence,
        arousal
 FROM   turn_annotations
 WHERE  NOT INSTR(valence, ",")
 
 UNION
 
 -- in turns with more than one emotion, only the first one is returned
 SELECT tur_id,
        ann_index,
        SUBSTR(valence, 0, INSTR(valence, ",")),
        SUBSTR(arousal, 0, INSTR(arousal, ","))
 FROM   turn_annotations tan
 WHERE  INSTR(valence, ",")
)
SELECT grp.grp_id,
       ses.ses_id,
       tsk.tsk_id,
       tur.tur_id,
       chu.chu_id,
       ses.rnd,
       tsk.task_index,
       tur.turn_index,
       tur.turn_index_ses,
       chu.chunk_index,
       CASE 
           WHEN chu.start_time > hlf_ses.ts
           THEN 2
           ELSE 1
       END ses_half,
       CASE 
           WHEN chu.start_time > hlf_tsk.ts
           THEN 2
           ELSE 1
       END tsk_half,
       chu.start_time,
       chu.end_time,
       chu.end_time - chu.start_time duration,
       chu.words,
       chu.words_asr1,
       chu.words_asr2,
       chu.words_asr3,
       chu.words_asr4,
       chu.pitch_min pitch_min_raw,
       chu.pitch_max pitch_max_raw,
       chu.pitch_mean pitch_mean_raw,
       chu.pitch_std pitch_std_raw,
       chu.rate_syl rate_syl_raw,
       chu.rate_vcd rate_vcd_raw,
       chu.intensity_min intensity_min_raw,
       chu.intensity_max intensity_max_raw,
       chu.intensity_mean intensity_mean_raw,
       chu.intensity_std intensity_std_raw,
       chu.jitter jitter_raw,
       chu.shimmer shimmer_raw,
       chu.nhr nhr_raw,
       tur.speaker_role,
       tsk.a_or_b,
       tsk.score,
       tan.valence valence_avg,
       tan.arousal arousal_avg,
       ses.type ses_type,
       ses.cfg,
       ses.spk_a_smoothness,
       ses.spk_b_smoothness,
       ses.spk_a_likeable,
       ses.spk_b_likeable,
       ses.init_time,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN "A"
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN "A"
           ELSE "B"
       END speaker_a_or_b,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.spk_id
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.spk_id
           ELSE spk_b.spk_id
       END spk_id,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.subject_index
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.subject_index
           ELSE spk_b.subject_index
       END subject_index,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.age
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.age
           ELSE spk_b.age
       END age,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.sex
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.sex
           ELSE spk_b.sex
       END sex,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.gender_identification
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.gender_identification
           ELSE spk_b.gender_identification
       END gender_identification,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.racial_identification
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.racial_identification
           ELSE spk_b.racial_identification
       END racial_identification,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.hispanic
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.hispanic
           ELSE spk_b.hispanic
       END hispanic,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.tipi_o
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.tipi_o
           ELSE spk_b.tipi_o
       END tipi_o,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.tipi_c
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.tipi_c
           ELSE spk_b.tipi_c
       END tipi_c,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.tipi_e
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.tipi_e
           ELSE spk_b.tipi_e
       END tipi_e,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.tipi_a
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.tipi_a
           ELSE spk_b.tipi_a
       END tipi_a,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.tipi_n
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.tipi_n
           ELSE spk_b.tipi_n
       END tipi_n,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.mc_sds
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.mc_sds
           ELSE spk_b.mc_sds
       END mc_sds,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.iri_pt
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.iri_pt
           ELSE spk_b.iri_pt
       END iri_pt,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_a.rmi
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_a.rmi
           ELSE spk_b.rmi
       END rmi,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN "A"
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN "A"
           ELSE "B"
       END partner_a_or_b,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.spk_id
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.spk_id
           ELSE spk_b.spk_id
       END partner_spk_id,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.subject_index
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.subject_index
           ELSE spk_b.subject_index
       END partner_subject_index,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.age
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.age
           ELSE spk_b.age
       END partner_age,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.sex
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.sex
           ELSE spk_b.sex
       END partner_sex,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.gender_identification
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.gender_identification
           ELSE spk_b.gender_identification
       END partner_gender_identification,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.racial_identification
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.racial_identification
           ELSE spk_b.racial_identification
       END partner_racial_identification,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.hispanic
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.hispanic
           ELSE spk_b.hispanic
       END partner_hispanic,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.tipi_o
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.tipi_o
           ELSE spk_b.tipi_o
       END partner_tipi_o,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.tipi_c
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.tipi_c
           ELSE spk_b.tipi_c
       END partner_tipi_c,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.tipi_e
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.tipi_e
           ELSE spk_b.tipi_e
       END partner_tipi_e,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.tipi_a
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.tipi_a
           ELSE spk_b.tipi_a
       END partner_tipi_a,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.tipi_n
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.tipi_n
           ELSE spk_b.tipi_n
       END partner_tipi_n,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.mc_sds
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.mc_sds
           ELSE spk_b.mc_sds
       END partner_mc_sds,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.iri_pt
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.iri_pt
           ELSE spk_b.iri_pt
       END partner_iri_pt,
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "f"
           THEN spk_a.rmi
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "d"
           THEN spk_a.rmi
           ELSE spk_b.rmi
       END partner_rmi
FROM   chunks chu
JOIN   turns tur
ON     chu.tur_id == tur.tur_id
JOIN   tasks tsk
ON     tur.tsk_id == tsk.tsk_id
JOIN   sessions ses
ON     tsk.ses_id == ses.ses_id
JOIN   speakers spk_a
ON     ses.spk_id_a == spk_a.spk_id
JOIN   speakers spk_b
ON     ses.spk_id_b == spk_b.spk_id
JOIN   groups grp
ON     ses.grp_id == grp.grp_id
JOIN   halfway_points hlf_tsk
ON     tsk.tsk_id == hlf_tsk.tsk_id
JOIN   halfway_points hlf_ses
ON     ses.ses_id == hlf_ses.ses_id
LEFT JOIN (
       SELECT tur_id,
              AVG(valence) valence,
              AVG(arousal) arousal
       FROM   tan
       GROUP BY tur_id) tan
ON     tur.tur_id == tan.tur_id
WHERE  chu.do_include == 1
ORDER BY ses.ses_id, tsk.task_index, tur.turn_index, chu.chunk_index;


