-- collects the tables of the normalized, hierarchical schema into a single,
-- unnormalized table with redundant information
WITH halfway_points AS
-- select assumes continuous timestamps per session, no reset per task!
-- start/end are determined based on *all* chunks, even those missing features
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
), stats AS
(
 SELECT score.mn score_mn,
        score.sd score_sd,
        spk.tipi_o_md,
        spk.tipi_c_md,
        spk.tipi_e_md,
        spk.tipi_a_md,
        spk.tipi_n_md,
        spk.mc_sds_md,
        spk.iri_pt_md,
        spk.rmi_md
 FROM   (
         SELECT AVG(score) mn,
                STDEV(score) sd
         FROM   tasks
        ) score,
        (
         SELECT MEDIAN(tipi_o) tipi_o_md,
                MEDIAN(tipi_c) tipi_c_md,
                MEDIAN(tipi_e) tipi_e_md,
                MEDIAN(tipi_a) tipi_a_md,
                MEDIAN(tipi_n) tipi_n_md,
                MEDIAN(mc_sds) mc_sds_md,
                MEDIAN(iri_pt) iri_pt_md,
                MEDIAN(rmi) rmi_md
         FROM   speakers
         WHERE  spk_id != 0
        ) spk
), spk AS
(
 SELECT tur.tur_id,
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
        END rmi
 FROM   turns tur
 JOIN   tasks tsk
 ON     tur.tsk_id == tsk.tsk_id
 JOIN   sessions ses
 ON     tsk.ses_id == ses.ses_id
 JOIN   speakers spk_a
 ON     ses.spk_id_a == spk_a.spk_id
 JOIN   speakers spk_b
 ON     ses.spk_id_b == spk_b.spk_id
)


SELECT grp.grp_id,
       ses.ses_id,
       tsk.tsk_id,
       tur.tur_id,
       chu.chu_id,
       ses.rnd,
       CASE
           WHEN grp.grp_id % 2 == 1 AND ses.type == "GAME" 
           THEN ses.rnd
           WHEN grp.grp_id % 2 == 1 AND ses.type == "CONV" 
           THEN ses.rnd - 5
           WHEN grp.grp_id % 2 == 0 AND ses.type == "CONV" 
           THEN ses.rnd
           WHEN grp.grp_id % 2 == 0 AND ses.type == "GAME" 
           THEN ses.rnd - 2
       END rnd_of_type,
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
       IFNULL((tsk.score - stats.score_mn) / stats.score_sd, 
              0) score_z,
       tsk_prev.score prev_score,
       IFNULL((tsk_prev.score - stats.score_mn) / stats.score_sd, 
              0) prev_score_z,
       tan.valence valence_avg,
       tan.arousal arousal_avg,
       ses.type ses_type,
       ses.cfg,
       ses.spk_a_smoothness,
       ses.spk_b_smoothness,
       ses.spk_a_likeable,
       ses.spk_b_likeable,
       ses.init_time,
       spk.speaker_a_or_b,
       spk.spk_id,
       spk.subject_index,
       spk.age,
       spk.sex,
       spk.gender_identification,
       spk.racial_identification,
       spk.hispanic,
       spk.tipi_o,
       CASE 
           WHEN spk.tipi_o < stats.tipi_o_md
           THEN "l"
           ELSE "h"
       END tipi_o_hl,
       spk.tipi_c,
       CASE 
           WHEN spk.tipi_c < stats.tipi_c_md
           THEN "l"
           ELSE "h"
       END tipi_c_hl,
       spk.tipi_e,
       CASE 
           WHEN spk.tipi_e < stats.tipi_e_md
           THEN "l"
           ELSE "h"
       END tipi_e_hl,
       spk.tipi_a,
       CASE 
           WHEN spk.tipi_a < stats.tipi_a_md
           THEN "l"
           ELSE "h"
       END tipi_a_hl,
       spk.tipi_n,
       CASE 
           WHEN spk.tipi_n < stats.tipi_n_md
           THEN "l"
           ELSE "h"
       END tipi_n_hl,
       spk.mc_sds,
       CASE 
           WHEN spk.mc_sds < stats.mc_sds_md
           THEN "l"
           ELSE "h"
       END mc_sds_hl,
       spk.iri_pt,
       CASE 
           WHEN spk.iri_pt < stats.iri_pt_md
           THEN "l"
           ELSE "h"
       END iri_pt_hl,
       spk.rmi,
       CASE 
           WHEN spk.rmi < stats.rmi_md
           THEN "l"
           ELSE "h"
       END rmi_hl,
       -- it's useful to know the partner's speaker id for *all* chunks;
       -- other paired info can be loaded for only real/fake turn exchanges  
       -- using extra_cols in ap._load_pairs()
       CASE
           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
           THEN spk_b.spk_id
           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
           THEN spk_b.spk_id
           ELSE spk_a.spk_id
       END partner_spk_id
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
LEFT JOIN (
       SELECT ses_id, 
              task_index,
              score
       FROM   tasks) tsk_prev
ON     tsk.ses_id == tsk_prev.ses_id
AND    tsk.task_index == (tsk_prev.task_index + 1)
JOIN   stats
JOIN   spk
ON     tur.tur_id == spk.tur_id
WHERE  chu.do_include == 1
ORDER BY ses.ses_id, tsk.task_index, tur.turn_index, chu.chunk_index;


