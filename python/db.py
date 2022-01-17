import pandas as pd
import sqlite3

import cfg
import fio

# this module contains functions for all interactions with the corpus database



################################################################################
#                            CONNECTION MAINTENANCE                            #
################################################################################

class DatabaseConnection(object):
    def __init__(self):
        self._conn = sqlite3.connect(cfg.DB_FNAME)
        self._c = self._conn.cursor()

    def __del__(self):
        self._conn.close()

    def execute(self, sql_stmt, params=tuple()):
        return self._c.execute(sql_stmt, params)

    def executemany(self, sql_stmt, params=tuple()):
        return self._c.executemany(sql_stmt, params)

    def executescript(self, sql_script):
        return self._c.executescript(sql_script)

    def getrowcount(self):
        return self._c.rowcount

    def commit(self):
        self._conn.commit()

    def get_conn(self):
        return self._conn

dbc = None


def connect():
    global dbc
    dbc = DatabaseConnection()


def close():
    global dbc
    del dbc
    dbc = None


def commit():
    dbc.commit()


def get_conn():
    return dbc.get_conn()



################################################################################
#                                  INSERTIONS                                  #
################################################################################

def ins_grp(grp_id, sex_seq, cfg_seq, games_first):
    sql_stmt = \
        'INSERT INTO groups (grp_id, sex_seq, cfg_seq, games_first)\n' \
        'VALUES(?,?,?,?);'
    dbc.execute(sql_stmt, (grp_id, sex_seq, cfg_seq, games_first))


def ins_spk(spk_id, mch_id):
    sql_stmt = \
        'INSERT INTO speakers (spk_id, subject_index)\n' \
        'VALUES (?,?);'
    dbc.execute(sql_stmt, (spk_id, mch_id))


def ins_ses(ses_id, grp_id, spk_id_a, spk_id_b, rnd, ses_type, cfg):
    sql_stmt = \
        'INSERT INTO sessions (ses_id, grp_id, spk_id_a, spk_id_b, rnd, ' \
                              'type, cfg)\n' \
        'VALUES (?,?,?,?,?,?,?);'
    params = (ses_id, grp_id, spk_id_a, spk_id_b, rnd, ses_type, cfg)
    dbc.execute(sql_stmt, params)


def ins_tsk(ses_id, task_index, a_or_b):
    sql_stmt = \
        'INSERT INTO tasks (ses_id, task_index, a_or_b)\n' \
        'VALUES (?,?,?);'
    dbc.execute(sql_stmt, (ses_id, task_index, a_or_b))


def ins_qre(que_id, spk_id, val, ts):
    sql_stmt = \
        'INSERT INTO question_responses (que_id, spk_id, val, ts)\n' \
        'VALUES (?,?,?,?);'
    dbc.execute(sql_stmt, (que_id, spk_id, val, ts))


def ins_tur(tur_id, tsk_id, turn_index_ses, speaker_role):
    sql_stmt = \
        'INSERT INTO turns (tur_id, tsk_id, turn_index_ses, speaker_role)\n' \
        'VALUES (?,?,?,?);'
    dbc.execute(sql_stmt, (tur_id, tsk_id, turn_index_ses, speaker_role))


def ins_chu(chu_id, tur_id, chunk_index, start_time, end_time, words):
    sql_stmt = \
        'INSERT INTO chunks (chu_id, tur_id, chunk_index, start_time, ' \
                            'end_time, words)\n' \
        'VALUES (?,?,?,?,?,?);'
    params = (chu_id, tur_id, chunk_index, start_time, end_time, words)
    dbc.execute(sql_stmt, params)



################################################################################
#                           SETTERS (SIMPLE UPDATES)                           #
################################################################################

def set_ses_status(ses_id, status):
    sql_stmt = \
        'UPDATE sessions\n' \
        'SET    status = ?\n' \
        'WHERE  ses_id = ?;'
    dbc.execute(sql_stmt, (status, ses_id,))


def set_ses_time(ses_id, t):
    sql_stmt = \
        'UPDATE sessions\n' \
        'SET    init_time = ?\n' \
        'WHERE  ses_id = ?;'
    ts = t[:2] + ':' + t[2:4] + ':' + t[4:]
    dbc.execute(sql_stmt, (ts, ses_id,))


def set_grp_date(grp_id, d):
    sql_stmt = \
        'UPDATE groups\n' \
        'SET    record_date = ?\n' \
        'WHERE  grp_id = ?;'
    ds = d[:4] + '-' + d[4:6] + '-' + d[6:]
    dbc.execute(sql_stmt, (ds, grp_id,))
    

def set_ratings(ses_id, ratings1, ratings2):
    # each ratingsX is a pair, two ratings given by the respective speaker
    sql_stmt = \
        'UPDATE sessions\n' \
        'SET    spk_b_likeable = ?,\n' \
        '       spk_a_smoothness = ?,\n' \
        '       spk_a_likeable = ?,\n' \
        '       spk_b_smoothness = ?\n' \
        'WHERE  ses_id = ?;'
    dbc.execute(sql_stmt, ratings1 + ratings2 + [ses_id])


def set_scores(ses_id, scores):
    sql_stmt = \
        'UPDATE tasks\n' \
        'SET    score = ?\n' \
        'WHERE  ses_id = ?\n' \
        'AND    task_index = ?;'
    params = [(score, ses_id, i+1) for i, score in enumerate(scores)]
    dbc.executemany(sql_stmt, params)


def set_turn_indices():
    subselect = \
        'SELECT MAX(tur2.turn_index_ses) ' \
        'FROM   turns tur2 ' \
        'JOIN   tasks tsk1 ' \
        'ON     turns.tsk_id == tsk1.tsk_id ' \
        'JOIN   tasks tsk2 ' \
        'ON     tur2.tsk_id == tsk2.tsk_id ' \
        'WHERE  tsk1.ses_id == tsk2.ses_id ' \
        'AND    tsk1.task_index == tsk2.task_index + 1 '
    sql_stmt = \
        'UPDATE turns ' \
        'SET    turn_index = turn_index_ses - IFNULL((' + subselect + '), 0);'
    dbc.execute(sql_stmt)


def set_features(chu_id, features):
    sql_stmt = \
        'UPDATE chunks\n' \
        'SET    pitch_min = ?,\n' \
        '       pitch_max = ?,\n' \
        '       pitch_mean = ?,\n' \
        '       pitch_std = ?,\n' \
        '       rate_syl = ?,\n' \
        '       rate_vcd = ?,\n' \
        '       intensity_min = ?,\n' \
        '       intensity_max = ?,\n' \
        '       intensity_mean = ?,\n' \
        '       intensity_std = ?,\n' \
        '       jitter = ?,\n' \
        '       shimmer = ?,\n' \
        '       nhr = ?\n' \
        'WHERE  chu_id == ?;'
    dbc.execute(sql_stmt, 
                (features['f0_min'],
                 features['f0_max'],
                 features['f0_mean'],
                 features['f0_std'],
                 features['rate_syl'],
                 features['vcd2tot_frames'],
                 features['int_min'],
                 features['int_max'],
                 features['int_mean'],
                 features['int_std'],
                 features['jitter'],
                 features['shimmer'],
                 features['nhr'],
                 chu_id))
        


################################################################################
#                           GETTERS (SIMPLE SELECTS)                           #
################################################################################

def get_tsk_id(ses_id, task_index):
    sql_stmt = \
        'SELECT tsk_id\n' \
        'FROM   tasks\n' \
        'WHERE  ses_id == ?\n' \
        'AND    task_index == ?;'
    return int(dbc.execute(sql_stmt, (ses_id, task_index)).fetchall()[0][0])


def get_ses_id(tsk_id):
    ''' returns ses_id for given tsk_id '''
    sql_stmt = \
        'SELECT ses_id\n' \
        'FROM   tasks\n' \
        'WHERE  tsk_id == ?;'
    return int(dbc.execute(sql_stmt, (tsk_id,)).fetchall()[0][0])


def get_tsk_ids():
    sql_stmt = \
        'SELECT tsk_id\n' \
        'FROM   tasks\n' \
        'ORDER BY tsk_id;'
    return [int(v[0]) for v in dbc.execute(sql_stmt).fetchall()]


def get_ses_ids():
    sql_stmt = \
        'SELECT ses_id\n' \
        'FROM   sessions\n' \
        'ORDER BY ses_id;'
    return [int(v[0]) for v in dbc.execute(sql_stmt).fetchall()]


def get_tsk_ses_ids(tsk_or_ses):
    return get_tsk_ids() if tsk_or_ses == 'tsk' else get_ses_ids()


def get_a_or_b(tsk_or_ses, tsk_ses_id, spk_id):
    ''' returns whether given speaker is A or B in given task/session '''
    ses_id = tsk_ses_id if tsk_or_ses == 'ses' else get_ses_id(tsk_ses_id)
    sql_stmt = \
        'SELECT CASE\n' \
        '           WHEN spk_id_a == ?\n' \
        '           THEN "A"\n' \
        '           WHEN spk_id_b == ?\n' \
        '           THEN "B"\n' \
        '           ELSE ""\n' \
        '       END\n' \
        'FROM   sessions\n' \
        'WHERE  ses_id == ?;'
    return dbc.execute(sql_stmt, (spk_id, spk_id, ses_id)).fetchall()[0][0]


def get_role(tsk_id, spk_a_or_b):
    sql_stmt = \
        'SELECT a_or_b\n' \
        'FROM   tasks\n' \
        'WHERE  tsk_id == ?;'
    dsc_a_or_b = dbc.execute(sql_stmt, (tsk_id,)).fetchall()[0][0]
    return 'd' if spk_a_or_b == dsc_a_or_b else 'f'


def get_que_id(qai_id, seq):
    sql_stmt = \
        'SELECT que_id\n' \
        'FROM   questions\n' \
        'WHERE  qai_id == ?\n' \
        'AND    seq == ?;'
    return dbc.execute(sql_stmt, (qai_id, seq)).fetchall()[0][0]


def get_tur_duration(ses_id, turn_index_ses):
    sql_stmt = \
        'SELECT SUM(chu.end_time - chu.start_time),\n' \
        '       CASE\n' \
        '           WHEN tur.speaker_role == "d" AND tsk.a_or_b == "A"\n' \
        '           THEN "A"\n' \
        '           WHEN tur.speaker_role == "f" AND tsk.a_or_b == "B"\n' \
        '           THEN "A"\n' \
        '           ELSE "B"\n' \
        '       END\n' \
        'FROM   chunks chu\n' \
        'JOIN   turns tur\n' \
        'ON     chu.tur_id == tur.tur_id\n' \
        'JOIN   tasks tsk\n' \
        'ON     tur.tsk_id == tsk.tsk_id\n' \
        'WHERE  tsk.ses_id == ?\n' \
        'AND    tur.turn_index_ses == ?;'
    dur, a_or_b = dbc.execute(sql_stmt, (ses_id, turn_index_ses)).fetchall()[0]
    return round(float(dur), 2), a_or_b


def get_tur_cnt(ses_id):
    sql_stmt = \
        'SELECT COUNT(tur_id)\n' \
        'FROM   turns tur\n' \
        'JOIN   tasks tsk\n' \
        'ON     tur.tsk_id == tsk.tsk_id\n' \
        'WHERE  tsk.ses_id == ?;'
    return int(dbc.execute(sql_stmt, (ses_id,)).fetchall()[0][0])


def get_tur_id(ses_id, turn_index_ses):
    ''' gets id of a turn of given session with given turn_index in it '''
    sql_stmt = \
        'SELECT tur.tur_id\n' \
        'FROM   turns tur\n' \
        'JOIN   tasks tsk\n' \
        'ON     tur.tsk_id == tsk.tsk_id\n' \
        'WHERE  tsk.ses_id == ?\n' \
        'AND    tur.turn_index_ses = ?;'
    return dbc.execute(sql_stmt, (ses_id, turn_index_ses)).fetchall()[0][0]


def get_tur_spk(ses_id, turn_index):
    sql_stmt = \
        'SELECT CASE\n' \
        '           WHEN tur.speaker_role == "d" AND tsk.a_or_b == "A"\n' \
        '           THEN "A"\n' \
        '           WHEN tur.speaker_role == "f" AND tsk.a_or_b == "B"\n' \
        '           THEN "A"\n' \
        '           ELSE "B"\n' \
        '       END,\n' \
        '       CASE\n' \
        '           WHEN tur.speaker_role == "d" AND tsk.a_or_b == "A"\n' \
        '           THEN ses.spk_id_a\n' \
        '           WHEN tur.speaker_role == "f" AND tsk.a_or_b == "B"\n' \
        '           THEN ses.spk_id_a\n' \
        '           ELSE ses.spk_id_b\n' \
        '       END\n' \
        'FROM   turns tur \n' \
        'JOIN   tasks tsk\n' \
        'ON     tur.tsk_id == tsk.tsk_id\n' \
        'JOIN   sessions ses\n' \
        'ON     tsk.ses_id == ses.ses_id\n' \
        'WHERE  ses.ses_id == ? \n' \
        'AND    tur.turn_index_ses == ?;'
    a_or_b, spk_id = dbc.execute(sql_stmt, (ses_id, turn_index)).fetchall()[0]
    return a_or_b, int(spk_id)


def get_next_ann_index(annotator, ses_id):
    ''' gets index for new annotation for given annotator & session '''
    # use COUNT instead of MAX so it works the first time as well
    sql_stmt = \
        'SELECT COUNT(DISTINCT ann_index)\n' \
        'FROM   turn_annotations tan\n' \
        'JOIN   turns tur\n' \
        'ON     tan.tur_id == tur.tur_id\n' \
        'JOIN   tasks tsk\n' \
        'ON     tur.tsk_id == tsk.tsk_id\n' \
        'WHERE  tan.annotator == ?\n' \
        'AND    tsk.ses_id == ?;'
    return dbc.execute(sql_stmt, (annotator, ses_id)).fetchall()[0][0] + 1


def get_words(tsk_or_ses, tsk_ses_id):
    ''' gets words for all chunks of given task/session in order '''
    assert tsk_or_ses in ['tsk', 'ses'], 'unknown tsk_or_ses value'
    sql_stmt = \
        'SELECT tur.tur_id,\n' \
        '       CASE\n' \
        '           WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"\n' \
        '           THEN "A"\n' \
        '           WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"\n' \
        '           THEN "A"\n' \
        '           ELSE "B"\n' \
        '       END a_or_b,\n' \
        '       chu.words\n' \
        'FROM   chunks chu\n' \
        'JOIN   turns tur\n' \
        'ON     chu.tur_id == tur.tur_id\n' \
        'JOIN   tasks tsk\n' \
        'ON     tur.tsk_id == tsk.tsk_id\n' \
        'WHERE  tsk.' + tsk_or_ses + '_id == ?\n' \
        'ORDER BY tsk.ses_id,\n' \
        '         tsk.task_index,\n' \
        '         tur.turn_index,\n' \
        '         chu.chunk_index;'
    return dbc.execute(sql_stmt, (tsk_ses_id,)).fetchall()



################################################################################
#                                    OTHER                                     #
################################################################################

def delete_all():
    dbc.execute('DELETE FROM question_responses;')
    dbc.execute('DELETE FROM tasks;')
    dbc.execute('DELETE FROM sessions;')
    dbc.execute('DELETE FROM speakers;')
    dbc.execute('DELETE FROM groups;')


def executescript(path, fname):
    dbc.executescript(''.join(fio.readlines(path, fname)))


def pd_read_sql_query(sql_stmt='', sql_fname=''):
    ''' runs given sql query and returns pandas dataframe of result 

    establishes and closes db connection for each call

    args:
        sql_stmt: sql statement to execute (only run if no filename given)
        sql_fname: filename (in cfg.SQL_PATH) from where to load sql statement
    returns:
        pandas dataframe with query result set 
    '''
    assert len(sql_stmt) > 0 or len(sql_fname) > 0, 'need sql query or filename'
    if len(sql_fname) > 0:
        sql_stmt = '\n'.join(fio.readlines(cfg.SQL_PATH, sql_fname))
    df = pd.read_sql_query(sql_stmt, get_conn())
    return df


def find_chunks(ses_id, a_or_b):
    ''' yields all chunks of a given speaker in a given session '''
    sql_stmt = \
        'SELECT chu.chu_id,\n' \
        '       chu.words,\n' \
        '       chu.start_time,\n' \
        '       chu.end_time\n' \
        'FROM   chunks chu\n' \
        'JOIN   turns tur\n' \
        'ON     chu.tur_id == tur.tur_id\n' \
        'JOIN   tasks tsk\n' \
        'ON     tur.tsk_id == tsk.tsk_id\n' \
        'WHERE  tsk.ses_id == ?\n' \
        'AND    CASE\n' \
        '           WHEN tur.speaker_role == "d" AND tsk.a_or_b == "A"\n' \
        '           THEN "A"\n' \
        '           WHEN tur.speaker_role == "f" AND tsk.a_or_b == "B"\n' \
        '           THEN "A"\n' \
        '           ELSE "B"\n' \
        '       END == ?\n'
    res = dbc.execute(sql_stmt, (ses_id, a_or_b)).fetchall()
    for chu_id, words, start, end in res:
        yield(chu_id, words, start, end)


def find_sessions(status, op='==', grp_id=None):
    ''' loads meta-data for all sessions with certain status '''
    op = op if op in ['==', '>=', '<=', '>', '<', '!='] else '=='
    sql_stmt1 = \
        'SELECT ses.ses_id,\n' \
        '       ses.rnd,\n' \
        '       ses.type,\n' \
        '       spk_a.subject_index,\n' \
        '       spk_b.subject_index\n' \
        'FROM   sessions ses\n' \
        'JOIN   speakers spk_a\n' \
        'ON     ses.spk_id_a == spk_a.spk_id\n' \
        'JOIN   speakers spk_b\n' \
        'ON     ses.spk_id_b == spk_b.spk_id\n' \
        'WHERE  ses.grp_id == ?\n' \
        'AND    ses.status ' + op + ' ?;'
    
    if grp_id is not None: # consider only single grp_id
        grp_ids = [grp_id]
    else: # do not limit grp_id
        sql_stmt2 = 'SELECT grp_id FROM groups ORDER BY grp_id;'
        grp_ids = [v[0] for v in dbc.execute(sql_stmt2).fetchall()]
    for grp_id in grp_ids:
        sessions = dbc.execute(sql_stmt1, (grp_id, status)).fetchall()
        for ses_id, rnd, ses_type, mch_id1, mch_id2 in sessions:
            is_woz = mch_id2 == 0
            p1, fn1 = fio.get_ses_pfn(grp_id, mch_id1, rnd, ses_type, is_woz)
            if is_woz:
                p2, fn2 = (None, None)
            else:
                p2, fn2 = fio.get_ses_pfn(grp_id, mch_id2, rnd, ses_type, False)
            yield grp_id, ses_id, ses_type, rnd, \
                  ((mch_id1, p1, fn1), (mch_id2, p2, fn2))


def set_words(grp_id, mch_id, rnd, start, end, words_fin, words_asr):
    ''' sets transcriptions for chunk of given speaker with given timestamps '''
    sql_stmt = \
        'UPDATE chunks\n' \
        'SET    words = ?,\n' \
        '       words_asr1 = ?\n' \
        'WHERE  chu_id == (\n' \
        '           SELECT chu.chu_id\n' \
        '           FROM   chunks chu\n' \
        '           JOIN   turns tur\n' \
        '           ON     chu.tur_id == tur.tur_id\n' \
        '           JOIN   tasks tsk\n' \
        '           ON     tur.tsk_id == tsk.tsk_id\n' \
        '           JOIN   sessions ses\n' \
        '           ON     tsk.ses_id == ses.ses_id\n' \
        '           JOIN   speakers spk_a\n' \
        '           ON     ses.spk_id_a == spk_a.spk_id\n' \
        '           JOIN   speakers spk_b\n' \
        '           ON     ses.spk_id_b == spk_b.spk_id\n' \
        '           WHERE  ses.grp_id == ?\n' \
        '           AND    CASE\n' \
        '                      WHEN tur.speaker_role == "d"\n' \
        '                      AND  tsk.a_or_b == "A"\n' \
        '                      THEN spk_a.subject_index\n' \
        '                      WHEN tur.speaker_role == "f"\n' \
        '                      AND  tsk.a_or_b == "B"\n' \
        '                      THEN spk_a.subject_index\n' \
        '                      ELSE spk_b.subject_index\n' \
        '                  END == ?\n' \
        '           AND    ses.rnd == ?\n' \
        '           AND    chu.start_time == ?\n' \
        '           AND    chu.end_time == ?\n' \
        ');'
    params = (words_fin, words_asr, grp_id, mch_id, rnd, start, end)
    dbc.execute(sql_stmt, params)
    if dbc.getrowcount() > 1:
        raise ValueError('multiple chunks found for grp %d, mch %d, rnd %d, ' \
                         'start %f, end %f' % (grp_id, mch_id, rnd, start, end))
    elif dbc.getrowcount() == 0:
        raise ValueError('no chunks found for grp %d, mch %d, rnd %d, ' \
                         'start %f, end %f' % (grp_id, mch_id, rnd, start, end))


def store_annotations(annotator, ses_id, anns):
    sql_stmt = \
        'INSERT INTO turn_annotations(' \
        'tur_id, annotator, ann_index, ann_unix_ts, ' \
        'outlier_intensity, outlier_pitch, outlier_speech_rate, ' \
        'outlier_creaky, outlier_breathy, valence, arousal, turn_flagged) ' \
        'VALUES (?,?,?,?,?,?,?,?,?,?,?,?);'
    ann_index = get_next_ann_index(annotator, ses_id)
    for key, (unix_ts, ann) in anns.items():
        tur_id = get_tur_id(ses_id, key + 1)
        if 'emotions' not in ann:
            valence = None
            arousal = None
        else:
            valence = ','.join([str(va['v']) for va in ann['emotions']])
            arousal = ','.join([str(va['a']) for va in ann['emotions']])
        turn_flagged = int(ann['turnFlag']) if 'turnFlag' in ann else None
        params = (tur_id, annotator, ann_index, unix_ts, ann['intensity'],
                  ann['pitch'], ann['rate'], ann['creaky'], ann['breathy'],
                  valence, arousal, turn_flagged)
        dbc.execute(sql_stmt, params)
    
    
    
    















