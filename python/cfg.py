# this module contains configuration constants used throughout other modules



# paths within the project 
ASR_PATH = '../../data/meta/asr/'
MSG_PATH = '../../data/meta/woz_msgs/'
TSK_PATH = '../../data/meta/task_intervals/'
VAD_PATH = '../../data/meta/vad/'
WAV_PATH = '../../data/wav/'
SQL_PATH = '../sql/'

# external paths (corpus root directory and temporary file directory)
CORPUS_PATH = '../../data/'
TMP_PATH = '../../tmp/'

# database filename
DB_FNAME = '../../bgc.db'

# transcript filenames
TRANS_ASR_FNAME = 'transcript.txt' 
TRANS_FIN_FNAME = 'transcript_final.txt'

# praat and sql scripts
PRAAT_SCRIPT_FNAME = '../praat/extract_features.praat'
SQL_INIT_FNAME = 'init.sql'
SQL_QR_FNAME = 'process_question_responses.sql'
SQL_CU_FNAME = 'cleanup.sql'
SQL_AT_FNAME = 'aux_tables.sql'
SQL_BT_FNAME = 'big_table.sql'
SQL_SP_FNAME = 'speaker_pairs.sql'

# format of timestamps in log files
TS_FMT = '%H:%M:%S:%f'

# normalization types
NRM_SPK = 'SPEAKER'
NRM_SEX = 'SEX'
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

# watson access credentials, loaded from external file
# with open('<INSERT_FILE_NAME>') as file:
#    lines = file.readlines()
#    API_KEY = lines[0].strip()
#    API_INS = lines[1].strip()
API_KEY = ''
API_INS = ''
API_URL = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com/'

