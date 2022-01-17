-- the data is stored in a hierarchical schema with groups at the highest level;
-- each group of four subjects has multiple interactions (sessions) with each 
-- other and the wizard of oz; each session consists of one or more tasks (even
-- conversation sessions, which are not broken up, have a single task record for
-- consistency of the interface); tasks consist of individual speaker turns, 
-- which are finally broken up into inter-pausal units (chunks of audio)

DROP TABLE IF EXISTS question_responses;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS questionnaires;

DROP TABLE IF EXISTS chunk_pairs;
DROP TABLE IF EXISTS halfway_points;

DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS turn_annotations;
DROP TABLE IF EXISTS turns;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS speakers;
DROP TABLE IF EXISTS groups;



CREATE TABLE groups (
    grp_id         INTEGER NOT NULL,
    -- sequence of speaker sexes ("MFMF" for groups 1 to 6, else "FMFM")
    sex_seq        TEXT,
    -- image configuration and conversation topic sequence for sessions 
    -- ("DBFAA" and "21" for groups 1,2,5,6,9,10, else "AFBDD" and "12",
    --  in respective order, i.e., games or conversations first)
    cfg_seq    TEXT,
    -- whether game sessions are first (odd group index) or conversations (even)
    games_first    INTEGER,
    -- date of the day the group was recorded, "YYYY-MM-DD"
    record_date    TEXT,
    PRIMARY KEY (grp_id)
);

CREATE TABLE speakers (
    spk_id                    INTEGER NOT NULL,
    -- subject index within the group (1 through 4, matches mch_id they sat at)
    subject_index             INTEGER NOT NULL,
    questionnaire_complete    INTEGER DEFAULT 0,
    age                       INTEGER,
    sex                       TEXT,
    gender_identification     TEXT,
    hispanic                  INTEGER,
    racial_identification     TEXT,
    -- big five personality inventory, based on tipi test (2-14 range)
    -- openness
    tipi_o                    INTEGER,
    -- conscientiousness
    tipi_c                    INTEGER,
    -- extraversion
    tipi_e                    INTEGER,
    -- agreeableness
    tipi_a                    INTEGER,
    -- neuroticism
    tipi_n                    INTEGER,
    -- marlowe-crowne social desirability scale (13 item test, 0-13 range)
    mc_sds                    INTEGER,
    -- interpersonal reactivity index, perspective-taking subscale (5-35 range)
    iri_pt                    INTEGER,
    -- reading the mind in the eyes test score (0-36 range)
    rmi                       INTEGER,
    PRIMARY KEY (spk_id)
);

CREATE TABLE sessions (
    -- interactions between pairs of speakers (one of which might be the woz)
    ses_id             INTEGER NOT NULL,
    grp_id             INTEGER NOT NULL,
    spk_id_a           INTEGER NOT NULL,
    spk_id_b           INTEGER NOT NULL,
    -- round within a group (1 to 7)
    rnd                INTEGER NOT NULL,
    -- 0: init; 1: logs processed; 2: vad run; 3: vad corrected (manually set); 
    -- 4: asr run; 5: asr corrected; 6: annotation done
    status                    INTEGER DEFAULT 0,
    -- type of interaction ("GAME" or "CONV")
    type               TEXT NOT NULL,
    -- image configuration ("A"/"B"/"F"/"D")
    -- or conversation topic ("1"/"2")
    cfg                TEXT NOT NULL,
    -- how smooth the interaction was according to speaker A
    spk_a_smoothness    INTEGER,
    -- how smooth the interaction was according to speaker B
    spk_b_smoothness    INTEGER,
    -- how likeable speaker A was according to speaker B
    -- (note that speaker A is the target, not the one who gave the rating!)
    spk_a_likeable      INTEGER,
    -- how likeable speaker B was according to speaker A
    -- (note that speaker B is the target, not the one who gave the rating!)
    spk_b_likeable      INTEGER,
    -- timestamp when the session was initiated, "HH:MM:SS" (for date see group)
    init_time           TEXT,
    PRIMARY KEY (ses_id),
    FOREIGN KEY (grp_id) REFERENCES groups (grp_id),
    FOREIGN KEY (spk_id_a) REFERENCES speakers (spk_id),
    FOREIGN KEY (spk_id_b) REFERENCES speakers (spk_id)
);

CREATE TABLE tasks (
    -- individual tasks, 14 per game session, one for conversations
    -- (table used even for conversations for consistency)
    tsk_id          INTEGER NOT NULL,
    ses_id          INTEGER NOT NULL,    
    task_index      INTEGER NOT NULL,
    -- who is describer for this task, a or b; other speaker is follower;
    -- only applies to games, always "A" for conversations
    a_or_b          TEXT NOT NULL,
    -- score for a game task, empty for conversations
    score      INTEGER,
    PRIMARY KEY (tsk_id),
    FOREIGN KEY (ses_id) REFERENCES sessions (ses_id)
);

CREATE TABLE turns (
    -- turn = "maximal sequence of inter-pausal units from a single speaker"
    -- (Levitan and Hirschberg, 2011)
    tur_id                 INTEGER NOT NULL,
    tsk_id                 INTEGER NOT NULL,
    -- index of the turn within its task
    turn_index             INTEGER,
    -- index of the turn within its session
    turn_index_ses         INTEGER NOT NULL,
    -- whether "d"(escriber) or "f"(ollower) is speaking
    speaker_role           TEXT NOT NULL,
    PRIMARY KEY (tur_id),
    FOREIGN KEY (tsk_id) REFERENCES tasks (tsk_id)
);

CREATE TABLE turn_annotations (
    -- annotations for outliers and emotions (only for turns with >1s speech);
    -- three annotations per turn from different annotators; 
    -- sessions can have repeat annotations from the same annotator
    -- (to assess self-agreement or fix a broken first round of annotations);
    -- annotators can change annotations; annotations reflect final value, but 
    -- timestamps reflect initial submission (best reflects time spent on turn)
    tan_id                 INTEGER NOT NULL,
    tur_id                 INTEGER NOT NULL,
    -- workerid in psiturk = initials of annotator 
    annotator              TEXT NOT NULL,
    -- round of annotation of this turn's session by this annotator
    -- (always 1, except for repeat annotation)
    ann_index              NUMERIC NOT NULL DEFAUlT 1,
    -- unix timestamp of the initial submission of an annotation for this turn
    ann_unix_ts            INTEGER NOT NULL,                              
    -- outlier values are integers; for intensity, pitch, speech rate:
    --     0 no part of the turn is an outlier
    --     1 part of the turn is an outlier (low)
    --     2 all of the turn is an outlier (low)
    --     3 part of the turn is low, another part high
    --     4 part of the turn is an outlier (high)
    --     5 all of the turn is an outlier (high)
    -- for creaky, breathy:
    --     0 no part of the turn is an outlier
    --     1 part of the turn is an outlier
    --     2 all of the turn is an outlier
    outlier_intensity      NUMERIC NOT NULL,
    outlier_pitch          NUMERIC NOT NULL,
    outlier_speech_rate    NUMERIC NOT NULL,
    outlier_creaky         NUMERIC NOT NULL,
    outlier_breathy        NUMERIC NOT NULL,
    -- emotion annotation as valence and arousal 
    -- can be multiple annotations, comma-separated, 0 to 100 each
    -- empty for first round of first few sessions (different annotation scheme)
    valence                TEXT,
    arousal                TEXT,
    -- flag for turns that appear particularly complex and hard to annotate, 
    -- to mark that they might need "special attention"
    turn_flagged           NUMERIC,
    PRIMARY KEY (tan_id),
    FOREIGN KEY (tur_id) REFERENCES turns (tur_id)
);

CREATE TABLE chunks (
    -- inter-pausal units with acoustic-prosodic and lexical data
    -- "pause-free units of speech from a single speaker separated from one 
    --  another by at least 50ms" (Levitan and Hirschberg, 2011)
    -- increased here to 100ms
    chu_id            INTEGER NOT NULL,
    tur_id            INTEGER NOT NULL,
    chunk_index       INTEGER NOT NULL,
    start_time        NUMERIC NOT NULL,
    end_time          NUMERIC NOT NULL,
    duration          INTEGER,
    words             TEXT,
    -- transcription according to asr, before manual correction
    -- (multiple columns for potential comparison between different systems)
    words_asr1        TEXT,
    words_asr2        TEXT,
    words_asr3        TEXT,
    words_asr4        TEXT,
    pitch_min         NUMERIC,
    pitch_max         NUMERIC,
    pitch_mean        NUMERIC,
    pitch_std         NUMERIC,
    rate_syl          NUMERIC,
    rate_vcd          NUMERIC,
    intensity_min     NUMERIC,
    intensity_max     NUMERIC,
    intensity_mean    NUMERIC,
    intensity_std     NUMERIC,
    jitter            NUMERIC,
    shimmer           NUMERIC,
    nhr               NUMERIC,
    -- whether to include this chunk in the analysis, true by default 
    -- (intended to exclude utterances in woz sessions that are readings of 
    --  prompts for 50 percent or more of the syllables, but named generically 
    --  in case it is later needed for other reasons to exclude as well)
    do_include        NUMERIC DEFAULT 1,
    PRIMARY KEY (chu_id),
    FOREIGN KEY (tur_id) REFERENCES turns (tur_id)
);



CREATE UNIQUE INDEX grp_pk ON groups (grp_id);
CREATE UNIQUE INDEX spk_pk ON speakers (spk_id);
CREATE UNIQUE INDEX ses_pk ON sessions (ses_id);
CREATE INDEX ses_grp_fk ON sessions (grp_id);
CREATE INDEX ses_spk_a_fk ON sessions (spk_id_a);
CREATE INDEX ses_spk_b_fk ON sessions (spk_id_b);
CREATE UNIQUE INDEX tsk_pk ON tasks (tsk_id);
CREATE INDEX tsk_ses_fk ON tasks (ses_id);
CREATE UNIQUE INDEX tsk_uk ON tasks (ses_id, task_index);
CREATE UNIQUE INDEX tur_pk ON turns (tur_id);
CREATE UNIQUE INDEX tur_uk ON turns (tur_id, turn_index);
CREATE INDEX tur_tsk_fk ON turns (tsk_id);
CREATE UNIQUE INDEX tan_pk ON turn_annotations (tan_id);
CREATE UNIQUE INDEX tan_uk ON turn_annotations (tur_id, annotator, ann_index);
CREATE INDEX tan_tur_fk ON turn_annotations (tur_id);
CREATE UNIQUE INDEX chu_pk ON chunks (chu_id);
CREATE UNIQUE INDEX chu_uk ON chunks (chu_id, chunk_index);
CREATE INDEX chu_tur_fk ON chunks (tur_id);



CREATE TABLE questionnaires (
    qai_id    INTEGER NOT NULL,
    txt       TEXT NOT NULL,
    PRIMARY KEY (qai_id)
);

CREATE TABLE questions (
    que_id    INTEGER NOT NULL,
    qai_id    INTEGER NOT NULL,
    seq       INTEGER NOT NULL,
    txt       TEXT NOT NULL,
    -- optional meta data for processing (e.g., correct solution)
    meta      TEXT,
    PRIMARY KEY (que_id),
    FOREIGN KEY (qai_id) REFERENCES questionnaires (qai_id),
    UNIQUE (qai_id, seq)
);

CREATE TABLE question_responses (
    qre_id    INTEGER NOT NULL,
    que_id    INTEGER NOT NULL,
    spk_id    INTEGER NOT NULL,
    -- value of the response
    val       TEXT NOT NULL,
    -- time stamp (time only, see group date for day)
    ts        TEXT NOT NULL,
    PRIMARY KEY (qre_id),
    FOREIGN KEY (que_id) REFERENCES questions (que_id),
    FOREIGN KEY (spk_id) REFERENCES speakers (spk_id),
    UNIQUE (que_id, spk_id)
);



CREATE UNIQUE INDEX qai_pk ON questionnaires (qai_id);
CREATE UNIQUE INDEX que_pk ON questions (que_id);
CREATE UNIQUE INDEX que_uk ON questions (qai_id, seq);
CREATE INDEX que_qai_fk ON questions (qai_id);
CREATE UNIQUE INDEX qre_pk ON question_responses (qre_id);
CREATE UNIQUE INDEX qre_uk ON question_responses (que_id, spk_id);
CREATE INDEX qre_que_fk ON question_responses (que_id);
CREATE INDEX qre_spk_fk ON question_responses (spk_id);



INSERT INTO questionnaires VALUES (1, 'Our funding agency, the National Science Foundation, requires that all studies maintain records of the age, sex, race, and ethnicity of all participants. If you decline to provide this information, it will in no way affect your status as a participant in this study. Your cooperation is appreciated. All information will be kept strictly confidential and will not have your name attached to it.');

INSERT INTO questions VALUES (1, 1, 1, 'What is your age?', NULL);
INSERT INTO questions VALUES (2, 1, 2, 'What is the sex specified on your birth certificate?', NULL);
INSERT INTO questions VALUES (3, 1, 3, 'What is your gender identification?', NULL);
INSERT INTO questions VALUES (4, 1, 4, 'Do you consider yourself to be Hispanic or Latino? (A person of Mexican, Puerto Rican, Cuban, South or Central American, or other Spanish culture or origin, regardless of race.)', NULL);
INSERT INTO questions VALUES (5, 1, 5, 'What race(s) do you consider yourself to be? American Indian or Alaska Native (A person having origins in any of the original peoples of North, Central, or South America, and who maintains tribal affiliation or community attachment.)', 'N');
INSERT INTO questions VALUES (6, 1, 6, 'What race(s) do you consider yourself to be? Asian (A person having origins in any of the original peoples of the Far East, Southeast Asia, or the Indian subcontinent.)', 'A');
INSERT INTO questions VALUES (7, 1, 7, 'What race(s) do you consider yourself to be? Native Hawaiian or Other Pacific Islander (A person having origins in any of the original peoples of Hawaii, Guam, Samoa, or other Pacific Islands.)', 'P');
INSERT INTO questions VALUES (8, 1, 8, 'What race(s) do you consider yourself to be? Black or African American (A person having origins in any of the black racial groups of Africa.)', 'B');
INSERT INTO questions VALUES (9, 1, 9, 'What race(s) do you consider yourself to be? White (A person having origins in any of the original peoples of Europe, the Middle East, or North Africa.)', 'W');
INSERT INTO questions VALUES (10, 1, 10, 'What race(s) do you consider yourself to be? Other', 'O');
INSERT INTO questions VALUES (11, 1, 11, 'What race(s) do you consider yourself to be? Unknown / No Report', '-');



INSERT INTO questionnaires VALUES (2, 'For each of the statements in this questionnaire, please mark whether they are true or false for you.');

INSERT INTO questions VALUES (12, 2, 1, 'It is sometimes hard for me to go on with my work if I am not encouraged.', 'F');
INSERT INTO questions VALUES (13, 2, 2, 'I sometimes feel resentful when I don''t get my own way.', 'F');
INSERT INTO questions VALUES (14, 2, 3, 'On a few occasions, I have given up doing something because I thought too little of my ability.', 'F');
INSERT INTO questions VALUES (15, 2, 4, 'There have been times when I felt like rebelling against people in authority even though I knew they were right.', 'F');
INSERT INTO questions VALUES (16, 2, 5, 'No matter who I''m talking to, I''m always a good listener.', 'T');
INSERT INTO questions VALUES (17, 2, 6, 'There have been occasions when I took advantage of someone.', 'F');
INSERT INTO questions VALUES (18, 2, 7, 'I''m always willing to admit it when I make a mistake.', 
'T');
INSERT INTO questions VALUES (19, 2, 8, 'I sometimes try to get even, rather than forgive and forget.', 'F');
INSERT INTO questions VALUES (20, 2, 9, 'I am always courteous, even to people who are disagreeable.', 'T');
INSERT INTO questions VALUES (21, 2, 10, 'I have never been irked when people expressed ideas very different from my own.', 'F');
INSERT INTO questions VALUES (22, 2, 11, 'There have been times when I was quite jealous of the good fortune of others.', 'F');
INSERT INTO questions VALUES (23, 2, 12, 'I am sometimes irritated by people who ask favors of me.', 'F');
INSERT INTO questions VALUES (24, 2, 13, 'I have never deliberately said something that hurt someone''s feelings.', 'T');



INSERT INTO questionnaires VALUES (3, 'The following statements inquire about your thoughts and feelings in a variety of situations. For each item, indicate how well it describes you by choosing the appropriate letter on the scale. Please read each item carefully before responding and answer as honestly as you can.');

INSERT INTO questions VALUES (25, 3, 1, 'I sometimes find it difficult to see things from the "other guy''s" point of view.', '-');
INSERT INTO questions VALUES (26, 3, 2, 'I try to look at everybody''s side of a disagreement before I decide.', '+');
INSERT INTO questions VALUES (27, 3, 3, 'I sometimes try to understand my friends better by imagining how things look from their perspective.', '+');
INSERT INTO questions VALUES (28, 3, 4, 'If I''m sure I''m right about something, I don''t waste much time listening to other people''s arguments.', '-');
INSERT INTO questions VALUES (29, 3, 5, 'I believe that there are two sides to every question and try to look at both of them.', '+');
INSERT INTO questions VALUES (30, 3, 6, 'When I''m upset at someone, I usually try to "put myself in their shoes" for a while.', '+');
INSERT INTO questions VALUES (31, 3, 7, 'Before criticizing somebody, I try to imagine how I would feel if I were in their place.', '+');



INSERT INTO questionnaires VALUES (4, 'This questionnaire lists a number of personality traits that may or may not apply to you. Please choose a number for each pair of traits to indicate the extent to which you agree that they apply to you. You should rate the extent to which the pair of traits applies to you, even if one trait applies more strongly than the other.');

INSERT INTO questions VALUES (32, 4, 1, 'Extraverted, enthusiastic', 'E');
INSERT INTO questions VALUES (33, 4, 2, 'Critical, quarrelsome', '-A');
INSERT INTO questions VALUES (34, 4, 3, 'Dependable, self-disciplined', 'C');
INSERT INTO questions VALUES (35, 4, 4, 'Anxious, easily upset', 'N');
INSERT INTO questions VALUES (36, 4, 5, 'Open to new experiences, complex', 'O');
INSERT INTO questions VALUES (37, 4, 6, 'Reserved, quiet', '-E');
INSERT INTO questions VALUES (38, 4, 7, 'Sympathetic, warm', 'A');
INSERT INTO questions VALUES (39, 4, 8, 'Disorganized, careless', '-C');
INSERT INTO questions VALUES (40, 4, 9, 'Calm, emotionally stable', '-N');
INSERT INTO questions VALUES (41, 4, 10, 'Conventional, uncreative', '-O');



INSERT INTO questionnaires VALUES (5, 'In this last questionnaire, you will see a number of images, one at a time, each showing a person''s eyes, as well as four words for each image. For each set of eyes, choose the word which best describes what the person in the picture is thinking or feeling. You may feel that more than one word is applicable but please choose just one word, the word which you consider to be most suitable. Before making your choice, make sure that you have read all four words. You should try to do the task as quickly as possible but you will not be timed. If you really don''t know what a word means, hover it for a definition.');

INSERT INTO questions VALUES (42, 5, 1, 'playful;comforting;irritated;bored', '1');
INSERT INTO questions VALUES (43, 5, 2, 'terrified;upset;arrogant;annoyed', '2');
INSERT INTO questions VALUES (44, 5, 3, 'joking;flustered;desire;convinced', '3');
INSERT INTO questions VALUES (45, 5, 4, 'joking;insisting;amused;relaxed', '2');
INSERT INTO questions VALUES (46, 5, 5, 'irritated;sarcastic;worried;friendly', '3');
INSERT INTO questions VALUES (47, 5, 6, 'aghast;fantasizing;impatient;alarmed', '2');
INSERT INTO questions VALUES (48, 5, 7, 'apologetic;friendly;uneasy;dispirited', '3');
INSERT INTO questions VALUES (49, 5, 8, 'despondent;relieved;shy;excited', '1');
INSERT INTO questions VALUES (50, 5, 9, 'annoyed;hostile;horrified;preoccupied', '4');
INSERT INTO questions VALUES (51, 5, 10, 'cautious;insisting;bored;aghast', '1');
INSERT INTO questions VALUES (52, 5, 11, 'terrified;amused;regretful;flirtatious', '3');
INSERT INTO questions VALUES (53, 5, 12, 'indifferent;embarrassed;sceptical;dispirited', '3');
INSERT INTO questions VALUES (54, 5, 13, 'decisive;anticipating;threatening;shy', '2');
INSERT INTO questions VALUES (55, 5, 14, 'irritated;disappointed;depressed;accusing', '4');
INSERT INTO questions VALUES (56, 5, 15, 'contemplative;flustered;encouraging;amused', '1');
INSERT INTO questions VALUES (57, 5, 16, 'irritated;thoughtful;encouraging;sympathetic', '2');
INSERT INTO questions VALUES (58, 5, 17, 'doubtful;affectionate;playful;aghast', '1');
INSERT INTO questions VALUES (59, 5, 18, 'decisive;amused;aghast;bored', '1');
INSERT INTO questions VALUES (60, 5, 19, 'arrogant;grateful;sarcastic;tentative', '4');
INSERT INTO questions VALUES (61, 5, 20, 'dominant;friendly;guilty;horrified', '2');
INSERT INTO questions VALUES (62, 5, 21, 'embarrassed;fantasizing;confused;panicked', '2');
INSERT INTO questions VALUES (63, 5, 22, 'preoccupied;grateful;insisting;imploring', '1');
INSERT INTO questions VALUES (64, 5, 23, 'contented;apologetic;defiant;curious', '3');
INSERT INTO questions VALUES (65, 5, 24, 'pensive;irritated;excited;hostile', '1');
INSERT INTO questions VALUES (66, 5, 25, 'panicked;incredulous;despondent;interested', '4');
INSERT INTO questions VALUES (67, 5, 26, 'alarmed;shy;hostile;anxious', '3');
INSERT INTO questions VALUES (68, 5, 27, 'joking;cautious;arrogant;reassuring', '2');
INSERT INTO questions VALUES (69, 5, 28, 'interested;joking;affectionate;contented', '1');
INSERT INTO questions VALUES (70, 5, 29, 'impatient;aghast;irritated;reflective', '4');
INSERT INTO questions VALUES (71, 5, 30, 'grateful;flirtatious;hostile;disappointed', '2');
INSERT INTO questions VALUES (72, 5, 31, 'ashamed;confident;joking;dispirited', '2');
INSERT INTO questions VALUES (73, 5, 32, 'serious;ashamed;bewildered;alarmed', '1');
INSERT INTO questions VALUES (74, 5, 33, 'embarrassed;guilty;fantasizing;concerned', '4');
INSERT INTO questions VALUES (75, 5, 34, 'aghast;baffled;distrustful;terrified', '3');
INSERT INTO questions VALUES (76, 5, 35, 'puzzled;nervous;insisting;contemplative', '2');
INSERT INTO questions VALUES (77, 5, 36, 'ashamed;nervous;suspicious;indecisive', '3');

