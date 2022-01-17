-- finds partners and non-partners for all speakers and tasks/sessions

-- AUXILIARY query with speaker and partner information
-- finds speaker sex and role as well as partner sex from either speaker's 
-- "perspective"; *_s and *_p refer to speaker and partner, resp.
WITH sub AS
(
 SELECT ses.grp_id grp_id,
        ses.type ses_type,
        ses.ses_id ses_id,
        tsk.tsk_id tsk_id,
        ses.spk_id_a spk_id_s,
        ses.spk_id_b spk_id_p,
        "A" a_or_b_s,
        "B" a_or_b_p,
        spk_a.sex sex_s,
        spk_b.sex sex_p,
        CASE 
            WHEN ses.type == "CONV" 
            THEN "CONV"
            WHEN tsk.a_or_b == "A" 
            THEN "d"
            ELSE "f"
        END role_s
 FROM   tasks tsk
 JOIN   sessions ses
 ON     tsk.ses_id == ses.ses_id
 JOIN   speakers spk_a
 ON     ses.spk_id_a == spk_a.spk_id
 JOIN   speakers spk_b
 ON     ses.spk_id_b == spk_b.spk_id
 WHERE  ses.spk_id_a != 0
 AND    ses.spk_id_b != 0

 UNION

 SELECT ses.grp_id grp_id,
        ses.type ses_type,
        ses.ses_id ses_id,
        tsk.tsk_id tsk_id,
        ses.spk_id_b spk_id_s,
        ses.spk_id_a spk_id_p,
        "B" a_or_b_s,
        "A" a_or_b_p,
        spk_b.sex sex_s,
        spk_a.sex sex_p,
        CASE 
            WHEN ses.type == "CONV" 
            THEN "CONV"
            WHEN tsk.a_or_b == "B"
            THEN "d"
            ELSE "f"
        END role_s
 FROM   tasks tsk
 JOIN   sessions ses
 ON     tsk.ses_id == ses.ses_id
 JOIN   speakers spk_a
 ON     ses.spk_id_a == spk_a.spk_id
 JOIN   speakers spk_b
 ON     ses.spk_id_b == spk_b.spk_id
 WHERE  ses.spk_id_a != 0
 AND    ses.spk_id_b != 0
)

-- NON-PARTNER query for tasks
-- finds all non-partner tasks and speakers that match certain sex/role criteria
SELECT "x" p_or_x,
       tgt.ses_type,
       tgt.ses_id ses_id,
       tgt.tsk_id tsk_id,
       tgt.spk_id_s spk_id,
       tgt.a_or_b_s a_or_b,
       prd.ses_id ses_id_paired,
       prd.tsk_id tsk_id_paired,
       prd.spk_id_s spk_id_paired,
       prd.a_or_b_s a_or_b_paired
FROM   sub tgt -- "target"
JOIN   sub prd -- "paired"
-- paired speaker and target speaker's partner must not be the same
-- (made redundant by next condition but left in as a reminder)
ON     tgt.spk_id_p != prd.spk_id_s
-- paired speaker must be from different group (non-partners never interacted)
AND    tgt.grp_id != prd.grp_id
-- paired speaker must be engaged in the same type of interaction
AND    tgt.ses_type == prd.ses_type
-- paired speaker must have the same sex as the target's partner
AND    tgt.sex_p == prd.sex_s
-- paired speaker's partner must have the same sex as the target speaker
AND    tgt.sex_s == prd.sex_p
-- paired speaker must have the same role as the target speaker's partner
-- i.e., paired speaker and target speaker must have different roles
AND    (tgt.role_s != prd.role_s OR tgt.role_s == "CONV")

UNION

-- NON-PARTNER query for sessions; same as above but with one entry per session
SELECT DISTINCT
       "x" p_or_x,
       tgt.ses_type,
       tgt.ses_id ses_id,
       0 tsk_id,
       tgt.spk_id_s spk_id,
       tgt.a_or_b_s a_or_b,
       prd.ses_id ses_id_paired,
       0 tsk_id_paired,
       prd.spk_id_s spk_id_paired,
       prd.a_or_b_s a_or_b_paired
FROM   sub tgt
JOIN   sub prd
ON     tgt.spk_id_p != prd.spk_id_s
AND    tgt.grp_id != prd.grp_id
AND    tgt.ses_type == prd.ses_type
AND    tgt.sex_p == prd.sex_s
AND    tgt.sex_s == prd.sex_p
AND    (tgt.role_s != prd.role_s OR tgt.role_s == "CONV")

UNION

-- PARTNER query (both speakers from same task) for tasks
SELECT "p" p_or_x,
       ses_type,
       ses_id,
       tsk_id,
       spk_id_s spk_id,
       a_or_b_s a_or_b,
       ses_id ses_id_paired,
       tsk_id tsk_id_paired,
       spk_id_p spk_id_paired,
       a_or_b_p a_or_b_paired
FROM   sub

UNION

-- PARTNER query for sessions; same as above but with one entry per session
SELECT DISTINCT 
	   "p" p_or_x,
       ses_type,
       ses_id,
       0 tsk_id,
       spk_id_s spk_id,
       a_or_b_s a_or_b,
       ses_id ses_id_paired,
       0 tsk_id_paired,
       spk_id_p spk_id_paired,
       a_or_b_p a_or_b_paired
FROM   sub





