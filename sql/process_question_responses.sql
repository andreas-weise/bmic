UPDATE speakers
SET    questionnaire_complete = 1
WHERE  NOT EXISTS (SELECT 1
                   FROM   questions que
                   LEFT JOIN question_responses qre
                   ON     que.que_id == qre.que_id
                   AND    speakers.spk_id == qre.spk_id
                   WHERE  qre.spk_id IS NULL);
                                      


UPDATE speakers
SET    age = (SELECT qre.val
              FROM   question_responses qre
              JOIN   questions que
              ON     qre.que_id == que.que_id
              WHERE  que.qai_id == 1
              AND    que.seq == 1
              AND    qre.spk_id == speakers.spk_id)
WHERE  spk_id != 0;

UPDATE speakers
SET    sex = (SELECT CASE 
                         WHEN LOWER(qre.val) IN ('m', 'male', 'boy') 
                         THEN 'm'
                         WHEN LOWER(qre.val) IN ('f', 'female', 'girl') 
                         THEN 'f'
                         ELSE NULL
                     END
              FROM   question_responses qre
              JOIN   questions que
              ON     qre.que_id == que.que_id
              WHERE  que.qai_id == 1
              AND    que.seq == 2
              AND    qre.spk_id == speakers.spk_id)
WHERE  spk_id != 0;

UPDATE speakers
SET    gender_identification = (SELECT CASE 
                                           WHEN LOWER(qre.val) IN ('m', 'male', 'boy') 
                                           THEN 'm'
                                           WHEN LOWER(qre.val) IN ('f', 'female', 'girl') 
                                           THEN 'f'
                                           WHEN LOWER(qre.val) == 'no report'
                                           THEN NULL
                                           ELSE qre.val
                                       END
                                FROM   question_responses qre
                                JOIN   questions que
                                ON     qre.que_id == que.que_id
                                WHERE  que.qai_id == 1
                                AND    que.seq == 3
                                AND    qre.spk_id == speakers.spk_id)
WHERE  spk_id != 0;

UPDATE speakers
SET    hispanic = (SELECT CASE 
                              WHEN qre.val == '1'
                              THEN 1
                              WHEN qre.val == '2'
                              THEN 0
                              ELSE NULL
                          END
                   FROM   question_responses qre
                   JOIN   questions que
                   ON     qre.que_id == que.que_id
                   WHERE  que.qai_id == 1
                   AND    que.seq == 4
                   AND    qre.spk_id == speakers.spk_id)
WHERE  spk_id != 0;

UPDATE speakers
SET    racial_identification = (SELECT GROUP_CONCAT(que.meta)
                                FROM   question_responses qre
                                JOIN   questions que
                                ON     qre.que_id == que.que_id
                                WHERE  que.qai_id == 1
                                AND    que.seq >= 5
                                AND    qre.spk_id == speakers.spk_id
                                AND    qre.val == 1)
WHERE  spk_id != 0;


UPDATE speakers
SET    mc_sds = (SELECT COUNT(*)
                 FROM   question_responses qre
                 JOIN   questions que
                 ON     qre.que_id == que.que_id
                 WHERE  que.qai_id == 2
                 AND    qre.spk_id == speakers.spk_id
                 AND   ((que.meta == 'F' AND qre.val == 0)
                        OR (que.meta == 'T' AND qre.val == 1)))
WHERE  spk_id != 0;


UPDATE speakers
SET    iri_pt = (SELECT SUM(CASE 
                                WHEN que.meta == '+' THEN qre.val
                                ELSE 6 - qre.val
                            END)
                 FROM   question_responses qre
                 JOIN   questions que
                 ON     qre.que_id == que.que_id
                 WHERE  que.qai_id == 3
                 AND    qre.spk_id == speakers.spk_id)
WHERE  spk_id != 0;

UPDATE speakers
SET    rmi = (SELECT COUNT(*)
              FROM   question_responses qre
              JOIN   questions que
              ON     qre.que_id == que.que_id
              WHERE  que.qai_id == 5
              AND    qre.spk_id == speakers.spk_id
              AND    que.meta == qre.val)
WHERE  spk_id != 0;

-- left join because there is no data on the second question for some speakers
-- due to a programming error
UPDATE speakers
SET    tipi_o = (SELECT qre_pos.val + IFNULL(8 - qre_neg.val, qre_pos.val)
                 FROM   question_responses qre_pos
                 JOIN   questions que_pos
                 ON     qre_pos.que_id == que_pos.que_id
                 LEFT JOIN  (SELECT qre.spk_id, qre.val
                             FROM   question_responses qre
                             JOIN   questions que
                             ON     qre.que_id == que.que_id
                             WHERE  que.qai_id == 4
                             AND    que.seq == 10) qre_neg
                 ON     qre_pos.spk_id == qre_neg.spk_id
                 WHERE  qre_pos.spk_id == speakers.spk_id
                 AND    que_pos.qai_id == 4
                 AND    que_pos.seq == 5)
WHERE  spk_id != 0;

UPDATE speakers
SET    tipi_c = (SELECT qre_pos.val + IFNULL(8 - qre_neg.val, qre_pos.val)
                 FROM   question_responses qre_pos
                 JOIN   questions que_pos
                 ON     qre_pos.que_id == que_pos.que_id
                 LEFT JOIN  (SELECT qre.spk_id, qre.val
                             FROM   question_responses qre
                             JOIN   questions que
                             ON     qre.que_id == que.que_id
                             WHERE  que.qai_id == 4
                             AND    que.seq == 8) qre_neg
                 ON     qre_pos.spk_id == qre_neg.spk_id
                 WHERE  qre_pos.spk_id == speakers.spk_id
                 AND    que_pos.qai_id == 4
                 AND    que_pos.seq == 3)
WHERE  spk_id != 0;

UPDATE speakers
SET    tipi_e = (SELECT qre1.val + IFNULL(8 - qre2.val, qre1.val)
                 FROM   question_responses qre1
                 JOIN   questions que1
                 ON     qre1.que_id == que1.que_id
                 JOIN   question_responses qre2
                 ON     qre1.spk_id == qre2.spk_id
                 JOIN   questions que2
                 ON     qre2.que_id == que2.que_id
                 WHERE  qre1.spk_id == speakers.spk_id
                 AND    que1.qai_id == 4
                 AND    que1.seq == 1
                 AND    que2.qai_id == 4
                 AND    que2.seq == 6)
WHERE  spk_id != 0;

UPDATE speakers
SET    tipi_a = (SELECT qre1.val + IFNULL(8 - qre2.val, qre1.val)
                 FROM   question_responses qre1
                 JOIN   questions que1
                 ON     qre1.que_id == que1.que_id
                 JOIN   question_responses qre2
                 ON     qre1.spk_id == qre2.spk_id
                 JOIN   questions que2
                 ON     qre2.que_id == que2.que_id
                 WHERE  qre1.spk_id == speakers.spk_id
                 AND    que1.qai_id == 4
                 AND    que1.seq == 7
                 AND    que2.qai_id == 4
                 AND    que2.seq == 2)
WHERE  spk_id != 0;

UPDATE speakers
SET    tipi_n = (SELECT qre_pos.val + IFNULL(8 - qre_neg.val, qre_pos.val)
                 FROM   question_responses qre_pos
                 JOIN   questions que_pos
                 ON     qre_pos.que_id == que_pos.que_id
                 LEFT JOIN  (SELECT qre.spk_id, qre.val
                             FROM   question_responses qre
                             JOIN   questions que
                             ON     qre.que_id == que.que_id
                             WHERE  que.qai_id == 4
                             AND    que.seq == 9) qre_neg
                 ON     qre_pos.spk_id == qre_neg.spk_id
                 WHERE  qre_pos.spk_id == speakers.spk_id
                 AND    que_pos.qai_id == 4
                 AND    que_pos.seq == 4)
WHERE  spk_id != 0;

