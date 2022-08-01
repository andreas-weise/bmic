# this module contains configuration constants used throughout other modules



# paths within the project 
ASR_PATH = '../../data/meta/asr/'
MSG_PATH = '../../data/meta/woz_msgs/'
TSK_PATH = '../../data/meta/task_intervals/'
VAD_PATH = '../../data/meta/vad/'
WAV_PATH = '../../data/wav/'
SQL_PATH = '../sql/'

# corpus identifiers
CORPUS_ID_BMIC = 'BMIC'
CORPUS_ID_GC  = 'GC'
CORPUS_IDS = [CORPUS_ID_BMIC, CORPUS_ID_GC]

# external paths (corpus root directory and temporary file directory)
CORPUS_PATH_BMIC = '../../data/'
TMP_PATH = '../../tmp/'

# database filename
DB_FNAME_BMIC = '../../bmic.db'
DB_FNAME_GC = '../../gc.db'

# transcript filenames
TRANS_ASR_FNAME = 'transcript.txt' 
TRANS_FIN_FNAME = 'transcript_final.txt'

# praat and sql scripts
PRAAT_SCRIPT_FNAME = '../praat/extract_features.praat'
SQL_INIT_FNAME_BMIC = 'init_bmic.sql'
SQL_QR_FNAME = 'process_question_responses.sql'
SQL_CU_FNAME = 'cleanup.sql'
SQL_AT_FNAME = 'aux_tables.sql'
SQL_BT_FNAME_BMIC = 'big_table_bmic.sql'
SQL_BT_FNAME_GC = 'big_table_gc.sql'
SQL_SP_FNAME_BMIC = 'speaker_pairs_bmic.sql'
SQL_SP_FNAME_GC = 'speaker_pairs_gc.sql'
SQL_EXT_FNAME = './libsqlitefunctions'

# format of timestamps in log files
TS_FMT = '%H:%M:%S:%f'

# normalization types
NRM_SPK = 'SPEAKER'
NRM_SEX = 'SEX'
NRM_GND = 'GENDER'
NRM_RAW = 'RAW'
NRM_TYPES = [NRM_SPK, NRM_SEX, NRM_RAW]

# entrainment measure identifiers
MEA_GSIM = 'gsim'
MEA_GCON = 'gcon'
MEA_LSIM = 'lsim'
MEA_LCON = 'lcon'
MEA_SYN  = 'syn'
MEASURES = [MEA_GSIM, MEA_GCON, MEA_LSIM, MEA_LCON, MEA_SYN]

# how to group data for entrainment measurement
GRP_BY_SES_TYPE = 'ses_type'
GRP_BY_SES = 'ses'
GRP_BY_SES_SPK = 'ses_spk'
GRP_BY_TSK = 'tsk'
GRP_BY_TSK_SPK = 'tsk_spk'
GRP_BYS = [
    GRP_BY_SES_TYPE, 
    GRP_BY_SES, 
    GRP_BY_SES_SPK, 
    GRP_BY_TSK, 
    GRP_BY_TSK_SPK
]

# all features computed by praat and those actually analyzed
FEATURES_ALL = [
    'intensity_mean',
    'intensity_std',
    'intensity_min',
    'intensity_max',
    'pitch_mean',
    'pitch_std',
    'pitch_min',
    'pitch_max',
    'jitter',
    'shimmer',
    'nhr',
    'rate_syl',
    'rate_vcd'
]
FEATURES = [
    'intensity_mean',
    'intensity_max',
    'pitch_mean',
    'pitch_max',
    'jitter',
    'shimmer',
    'nhr',
    'rate_syl'
]


def check_corpus_id(corpus_id):
    assert corpus_id in CORPUS_IDS, 'unknown corpus id'


def check_mea_id(mea_id):
    assert mea_id in MEASURES, 'unknown entrainment measure'


def get_db_fname(corpus_id):
    check_corpus_id(corpus_id)
    return DB_FNAME_GC if corpus_id == CORPUS_ID_GC else DB_FNAME_BMIC


def get_bt_fname(corpus_id):
    check_corpus_id(corpus_id)
    return SQL_BT_FNAME_GC if corpus_id == CORPUS_ID_GC else SQL_BT_FNAME_BMIC


def check_grp_by(grp_by, supported=GRP_BYS):
    assert len(grp_by) > 0, 'at least one grp_by value needed'
    for g in grp_by:
        assert g in GRP_BYS, 'unknown grp_by value found'
        assert g in supported, 'unsupported grp_by value found'


# watson access credentials, loaded from external file
# with open('<INSERT_FILE_NAME>') as file:
#    lines = file.readlines()
#    API_KEY = lines[0].strip()
#    API_INS = lines[1].strip()
API_KEY = ''
API_INS = ''
API_URL = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com/'

