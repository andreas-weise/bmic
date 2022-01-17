from os import listdir
import sqlite3

import aux
import db
import fio

# this module contains functions to processes session logs and survey responses



################################################################################
#                               MODULE VARIABLES                               #
################################################################################

# partners for each session type, speaker, and round
# (including 'W'izard of Oz and 'Q'uestionnaires)
_partners = [
    [ # sessions with conversations first (games_first == 0)
        [], # empty and None entries to make index 1-based
        [None, 3, 4, 2, 3, 4, 'W', 'Q'],
        [None, 4, 3, 1, 4, 3, 'Q', 'W'],
        [None, 1, 2, 4, 1, 2, 'W', 'Q'],
        [None, 2, 1, 3, 2, 1, 'Q', 'W']
    ],
    [ # sessions with games_first == 1
        [], # empty and None entries to make index 1-based
        [None, 2, 3, 4, 'W', 'Q', 3, 4],
        [None, 1, 4, 3, 'Q', 'W', 4, 3],
        [None, 4, 1, 2, 'W', 'Q', 1, 2],
        [None, 3, 2, 1 ,'Q', 'W', 2, 1]
    ]
]


# initial roles of speakers in game sessions
_first_roles = [
    [ # sessions with conversations first (games_first == 0)
        [], # empty and first None entries to make index 1-based
        [None, None, None, 'd', 'f', 'd', 'f', None],
        [None, None, None, 'f', 'd', 'd', None, 'f'],
        [None, None, None, 'f', 'd', 'f', 'd', None],
        [None, None, None, 'd', 'f', 'f', None, 'd']
    ],
    [ # sessions with games first (games_first == 1)
        [], # empty and first None entries to make index 1-based
        [None, 'd', 'f', 'd', 'f', None, None, None],
        [None, 'f', 'd', 'd', None, 'f', None, None],
        [None, 'f', 'd', 'f', 'd', None, None, None],
        [None, 'd', 'f', 'f', None, 'd', None, None]
    ]
]



################################################################################
#                        NON-PUBLIC AUXILIARY FUNCTIONS                        #
################################################################################

def _insert_tasks(ses_id, ses_type, a_or_b):
    if ses_type == 'CONV':
        db.ins_tsk(ses_id, 1, 'A')
    else:
        for i in range(1, 15):
            db.ins_tsk(ses_id, i, a_or_b)
            a_or_b = 'A' if a_or_b == 'B' else 'B'


def _insert_sessions_tasks(grp_id, cfg_seq, games_first):
    for rnd in range(1, 8):
        # for each round, there are two sessions, either between two 
        # pairs of subjects or between two pairs of a subject and WOZ
        
        # determine speaker pairs for both sessions; 
        # always use subject 1 as 1st speaker in 1st pair unless 
        # they did questionnaires in this round
        mch_id_1a = 1 if _partners[games_first][1][rnd] != 'Q' else 4
        spk_id_1a = aux.get_spk_id(grp_id, mch_id_1a)
        # determine partner based on list
        mch_id_1b = _partners[games_first][mch_id_1a][rnd]
        spk_id_1b = aux.get_spk_id(grp_id, mch_id_1b)
        # always use subject 2 as 1st speaker in 2nd pair unless 
        # they were subject 1's partner or did questionnaires
        mch_id_2a = 2 if mch_id_1b != 2 \
                    and _partners[games_first][2][rnd] != 'Q' else 3
        spk_id_2a = aux.get_spk_id(grp_id, mch_id_2a)
        # determine partner based on list
        mch_id_2b = _partners[games_first][mch_id_2a][rnd]
        spk_id_2b = aux.get_spk_id(grp_id, mch_id_2b)
        
        # determine meta-data for sessions
        ses_type = 'GAME' if games_first and rnd < 6 \
            else 'GAME' if not games_first and rnd > 2 \
            else 'CONV'
        cfg = cfg_seq[rnd-1]
        ses_id1 = aux.get_ses_id(grp_id, rnd, 1)
        ses_id2 = aux.get_ses_id(grp_id, rnd, 2)
        
        # create two db records
        db.ins_ses(ses_id1, grp_id, spk_id_1a, spk_id_1b, rnd, ses_type, cfg)
        db.ins_ses(ses_id2, grp_id, spk_id_2a, spk_id_2b, rnd, ses_type, cfg)

        a_or_b1 = \
            'A' if _first_roles[games_first][mch_id_1a][rnd] == 'd' else 'B'
        a_or_b2 = \
            'A' if _first_roles[games_first][mch_id_2a][rnd] == 'd' else 'B'
        _insert_tasks(ses_id1, ses_type, a_or_b1)
        _insert_tasks(ses_id2, ses_type, a_or_b2)


def _extract_ratings(lines):
    return [int(lines[-2][-2]), int(lines[-1][-2])]


def _extract_scores(lines):
    return [int(line.split('\t')[2].split()[0]) 
            for line in lines if 'RESULTS' in line]


def _extract_woz_msgs(lines):
    ts_start = aux.get_ts(lines[1])
    return [(aux.get_ts_offset(ts_start, line), line.split('\t')[2].strip())
            for line in lines if 'WOZ_MSG' in line]


def _extract_task_intervals(lines):
    ts_start = aux.get_ts(lines[1])
    intervals = []
    start = 0.0
    turn = 0
    for line in lines:
        turn += 1 if 'NEXT_TURN' in line else 0
        if ('NEXT_TURN' in line and turn > 1) or 'END_GAME' in line:
            end = float(aux.round_ts(aux.get_ts_offset(ts_start, line)))
            intervals += [[start, end]]
            start = end
    return intervals



################################################################################
#                               PUBLIC FUNCTIONS                               #
################################################################################

def insert_group_sessions_tasks(grp_id):
    ''' inserts a group and the associated sessions and tasks '''
    sex_seq = 'MFMF' if grp_id < 7 else 'FMFM'
    cfg_seq = 'DBFAA21' if grp_id % 4 == 1 \
        else '21DBFAA' if grp_id % 4 == 2 \
        else 'AFBDD12' if grp_id % 4 == 3 \
        else '12AFBDD'
    games_first = aux.has_games_first(grp_id)
    db.ins_grp(grp_id, sex_seq, cfg_seq, games_first)
    _insert_sessions_tasks(grp_id, cfg_seq, games_first)


def process_question_log(grp_id, mch_id):
    ''' parses question log for given subject and stores responses ''' 
    lines = fio.read_questionnaire_file(grp_id, mch_id)
    ts_start = aux.get_ts(lines[1])
    spk_id = aux.get_spk_id(grp_id, mch_id)
    db.ins_spk(spk_id, mch_id)
        
    for line in lines[1:]:
        line = line.replace(' ', '\t').replace('\n', '')
        items = line.split('\t')
        ts = aux.get_ts_offset(ts_start, line)
        qai_id = int(items[2][1])
        que_seq = items[2][3:-1]
        if qai_id == 1 and que_seq[0] == '5':
            que_seq = 5 + int(que_seq[-1])
        else:
            que_seq = int(que_seq)
        val = ' '.join(items[3:])
        
        que_id = db.get_que_id(qai_id, que_seq)
        db.ins_qre(que_id, spk_id, val, ts)


def process_session_logs(grp_id):
    ''' parses logs for all sessions of given group 

    extracts timestamps, interaction/partner ratings, woz messages, and scores  
    '''
    for grp_id, ses_id, ses_type, rnd, mch_pair \
    in db.find_sessions(0, grp_id=grp_id):
        # unpack mch_pair
        ((mch_id1, _, _), (mch_id2, _, _)) = mch_pair
        is_woz = mch_id2 == 0
        lines1, d, t = fio.read_log_file(grp_id, mch_id1, rnd, ses_type, is_woz)
        if is_woz:
            fio.write_woz_msgs_file(ses_id, _extract_woz_msgs(lines1))
        else:
            lines2, _, _ = fio.read_log_file(
                grp_id, mch_id2, rnd, ses_type, False)
            ratings1 = _extract_ratings(lines1)
            ratings2 = _extract_ratings(lines2)
            db.set_ratings(ses_id, ratings1, ratings2)
            
        if ses_type == 'GAME':
            db.set_scores(ses_id, _extract_scores(lines1))
        fio.write_tsk_interval_file(ses_id, _extract_task_intervals(lines1))
        db.set_ses_time(ses_id, t)
        db.set_ses_status(ses_id, 1)
    db.set_grp_date(grp_id, d)
    


