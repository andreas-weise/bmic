import json
import nltk
import os
import shutil
import subprocess

import aux
import cfg
import db

# this module contains functions for all file i/o



################################################################################
#                            GET PATH AND FILE NAMES                           #
################################################################################

def _get_fname_prefix(grp_id, mch_id, rnd):
    ''' returns file name prefix for given interaction '''
    fname_prefix = 'g%d_m%d_r%d' % (grp_id, mch_id, rnd)
    fname_prefix += 'b' if aux.is_first_game_round(grp_id, rnd) else ''
    return fname_prefix


def _get_base_path(grp_id, mch_id, ses_type, is_woz):
    ''' returns root path for given subject's session(s) of given type '''
    subdir = 'switchboard' if ses_type == 'CONV' \
        else 'objects' + ('_woz' if is_woz else '')
    return '%sGroup%d/Machine%d/%s/' % \
        (cfg.CORPUS_PATH_BMIC, grp_id, mch_id, subdir)


def get_grp_dir_indices():
    ''' returns all group numbers found in the corpus root directory '''
    return [int(subdir[5:]) 
            for subdir in os.listdir(cfg.CORPUS_PATH) if subdir[:5] == 'Group']


def get_ses_pfn(grp_id, mch_id, rnd, ses_type, is_woz, wav_or_log='wav'):
    ''' returns wav or log file name (with path) for given session '''
    wav_or_log = 'wav' if wav_or_log == 'wav' else 'log'
    # file names contain prefix identifying group, machine, and round plus 
    # recording timestamp; search for file with correct prefix in correct path
    path = _get_base_path(grp_id, mch_id, ses_type, is_woz) + wav_or_log + 's/'
    fname_prefix = _get_fname_prefix(grp_id, mch_id, rnd)
    # machines record outgoing and incoming audio; for wav, use the outgoing 
    # audio because incoming is missing in a few cases due to technical issues
    fname = [fname for fname in os.listdir(path)
             if fname_prefix in fname 
             and ('out' in fname or wav_or_log == 'log')][0]
    return path, fname


def get_tur_pfn(ses_id, turn_index, wav_or_txt='wav', suf=''):
    ''' returns path and file name for audio/text of given turn in given ses '''
    path = cfg.WAV_PATH + 'ses' + str(ses_id) + '/'
    fname = str(turn_index) + suf + '.' \
          + ('wav' if wav_or_txt == 'wav' else 'txt')
    return path, fname


def get_vad_pfn(wav_fname, subdir=''):
    ''' returns path and file name for VAD textgrid file based on wav file '''
    # use same prefix and timestamp as for wav file (see above)
    # (makes matching easier for manual VAD correction)
    return cfg.VAD_PATH + subdir, wav_fname[:-3] + 'TextGrid'



################################################################################
#                                 WRITE FILES                                  #
################################################################################

def _write(path, fname, out_str, append=False):
    ''' writes given string to given file, appending or overwriting '''
    with open(path + fname, 'a' if append else 'w') as file:
        file.write(out_str)


def write_woz_msgs_file(ses_id, msgs):
    ''' writes wizard of oz messages for given session to default dir '''
    out_str = '\n'.join(['%s\t%s' % (aux.round_ts(msg[0]), msg[1]) 
                         for msg in msgs])
    _write(cfg.MSG_PATH, 'ses_%d.txt' % ses_id, out_str)


def write_tsk_interval_file(ses_id, intervals):
    ''' writes timestamps for tasks of given session to default dir '''
    out_str = '\n'.join(['%s\t%s' % (aux.round_ts(i[0]), aux.round_ts(i[1]))
                         for i in intervals])
    _write(cfg.TSK_PATH, 'ses_%d.txt' % ses_id, out_str)


def write_transcript_file(path, fname, intervals):
    ''' writes given transcipt to given path and filename '''
    out_str = '\n'.join(['%s\t%s\t%s' 
                         % (aux.round_ts(i[0]), aux.round_ts(i[1]), i[2])
                         for i in intervals if i[2] != '<silence>'])
    _write(path, fname, out_str)


def write_textgrid_file(path, fname, intervals):
    ''' writes intervals in given file using praat text grid format '''
    fnc = lambda i, xmin, xmax, text: \
        '        intervals[%d]:\n' \
        '            xmin = %s\n' \
        '            xmax = %s\n' \
        '            text = "%s"' % \
        (i, aux.round_ts(xmin), aux.round_ts(xmax), text)
    out_str = \
        'File type = "ooTextFile"\n' \
        'Object class = "TextGrid"\n' \
        '\n' \
        'xmin = 0\n' \
        'xmax = ' + str(intervals[-1][1]) + '\n' \
        'tiers? <exists> \n' \
        'size = 1 \n' \
        'item []: \n' \
        '    item [1]:\n' \
        '        class = "IntervalTier" \n' \
        '        name = "silences" \n' \
        '        xmin = 0 \n' \
        '        xmax = ' + aux.round_ts(intervals[-1][1]) + '\n' \
        '        intervals: size = ' + str(len(intervals)) + '\n' + \
        ('\n'.join([fnc(i+1, *s) for i, s in enumerate(intervals)]))
    _write(path, fname, out_str)


def init_tur_file(ses_id, turn_index, wav_or_txt='wav', suf=''):
    ''' initializes empty file for audio/text of given turn in given ses '''
    path, fname = get_tur_pfn(ses_id, turn_index, wav_or_txt, suf)
    # make sure path exists
    if not os.path.exists(path):
        os.mkdir(path)
    # create empty file of appropriate type
    if wav_or_txt == 'wav':
        subprocess.check_call([
            'sox', cfg.WAV_PATH + 'sil.wav', path + fname, 'trim', '0', '0.01'])
    else:
        _write(path, fname, '')


def concat_wavs(in_fname1, in_fname2):
    ''' concatenates a second audio file to the end of a first one '''
    con_fname = cfg.TMP_PATH + 'concat.wav'
    # concatenate files: create new file, replace original 1st file by new one
    subprocess.check_call(['sox', in_fname1, in_fname2, con_fname])
    os.remove(in_fname1)
    shutil.move(con_fname, in_fname1)


def append_silence(path, tur_fname, duration):
    ''' appends up to 1 sec of silence to audio of given turn in given ses '''
    dur = min(1.0, duration)
    # file names for sox commands
    out_fname = path + tur_fname
    sil_fname = cfg.WAV_PATH + 'sil.wav'
    tmp_fname = cfg.TMP_PATH + 'tmp_sil.wav'
    # prepare appropriate amount of silence, append, clean up
    subprocess.check_call(['sox', sil_fname, tmp_fname, 'trim', '0', str(dur)])
    concat_wavs(out_fname, tmp_fname)
    os.remove(tmp_fname)


def concat_turns(ses_id, turn_index_ctr, turn_index_start, turn_index_end, suf):
    ''' concatenates turns in given index range for annotation audio samples '''
    path, fname = get_tur_pfn(ses_id, turn_index_ctr, suf=suf)
    a_or_b_ctr = db.get_tur_spk(ses_id, turn_index_ctr)[0]
    init_tur_file(ses_id, turn_index_ctr, suf=suf)
    for i in range(turn_index_start+1, turn_index_end):
        if not os.path.exists(''.join(get_tur_pfn(ses_id, i))):
            continue # no audio exists for woz turns, ignore those
        a_or_b_i = db.get_tur_spk(ses_id, i)[0]
        if a_or_b_ctr == a_or_b_i:
            # only audio from same speaker
            concat_wavs(path + fname, ''.join(get_tur_pfn(ses_id, i)))
            append_silence(path, fname, 0.25)


def append_newline(ses_id, turn_index):
    ''' appends newline character to text of given turn in given ses '''
    path, fname = get_tur_pfn(ses_id, turn_index, 'txt')
    _write(path, fname, '\n', append=True)


def append_chunk_audio(ses_id, turn_index, in_path, in_fname, start, end):
    ''' appends section of session audio to audio of given turn in given ses '''
    out_path, out_fname = get_tur_pfn(ses_id, turn_index)
    in_fname = in_path + in_fname
    out_fname = out_path + out_fname
    cut_fname = cfg.TMP_PATH + str(ses_id) + '_' + str(turn_index) + '_cut.wav'
    # extract chunk audio, append, clean up
    subprocess.check_call([
        'sox', in_fname, cut_fname, 'trim', str(start), '=' + str(end)])
    concat_wavs(out_fname, cut_fname)
    os.remove(cut_fname)


def append_line(ses_id, turn_index, line):
    ''' appends line to text of given turn in given ses '''
    path, fname = get_tur_pfn(ses_id, turn_index, 'txt')
    _write(path, fname, line, append=True)


def write_tur_list(ses_id):
    ''' writes json file with data for psiturk annotation scripts '''
    path, _ = get_tur_pfn(ses_id, 1)
    fname = 'list.json'
    if os.path.exists(path + fname):
        os.remove(path + fname)
    data = os.listdir(path)
    data.sort(key=lambda x: int(x.split('.')[0]))
    data = [(fn, db.get_tur_duration(ses_id, fn[:-4])[0]) if fn[-3:] == 'wav' 
            else '\n'.join(readlines(path, fn)) 
            for fn in data]
    with open(path + fname, 'w') as file:
        json.dump(data, file)



################################################################################
#                                  READ FILES                                  #
################################################################################

def readlines(path, fname):
    ''' yields all lines in given file '''
    with open(path + fname) as file:
        return file.readlines()


def read_tsk_interval_file(ses_id):
    lines = readlines(cfg.TSK_PATH, 'ses_%d.txt' % ses_id)
    return [[float(v) for v in line.split('\t')] for line in lines]


def read_textgrid_file(path, fname):
    ''' reads praat text grid file into list of intervals '''
    intervals = []
    with open(path + fname) as file:
        for line in file:
            if 'xmin = ' in line:
                xmin = float(aux.round_ts(line.split('=')[1][1:]))
            elif 'xmax = ' in line:
                xmax = float(aux.round_ts(line.split('=')[1][1:]))
            elif 'text = "' in line:
                intervals += [[xmin, xmax, line.split('"')[1]]]
    return intervals


def read_transcript_file(path, fname):
    ''' reads timestamped transcript as written by write_transcript_file''' 
    intervals = []
    return [[float(v) if i < 2 else v.replace('\n', '')
             for i, v in enumerate(line.split('\t'))]
            for line in readlines(path, fname)]


def read_woz_msg_file(ses_id):
    ''' returns woz messages for given session as list of intervals '''
    # first loop to extract messages from file
    intervals_tmp = []
    with open(cfg.MSG_PATH + 'ses_%d.txt' % ses_id) as file:
        for line in file:
            ts, msg = line.split('\t')
            # treat messages as a short interval (they have no actual duration)
            intervals_tmp += [
                [float(aux.round_ts(ts)), 
                 float(aux.round_ts(float(ts)+0.01)), 
                 msg.strip()]]
    # second loop to insert pause intervals between messages
    # (note: 'silent' is never used as a message)
    intervals = []
    start = 0.0
    for i, interval in enumerate(intervals_tmp):
        intervals += [[start, interval[0], 'silent']]
        intervals += [interval]
        start = interval[1]
    return intervals


def read_questionnaire_file(grp_id, mch_id):
    ''' returns lines of questionnaire log (unparsed) for given subject '''
    path = '%sGroup%d/Machine%d/questionnaires/logs/' \
        % (cfg.CORPUS_PATH, grp_id, mch_id)
    fname = os.listdir(path)[0]
    return readlines(path, fname)


def read_log_file(grp_id, mch_id, rnd, ses_type, is_woz):
    path, fname = get_ses_pfn(grp_id, mch_id, rnd, ses_type, is_woz, 'log')
    # extract group record date and session init time from filename
    d, t = fname.split('.')[0].split('_')[3:]
    return readlines(path, fname), d, t



################################################################################
#                                     OTHER                                    #
################################################################################

def check_vad_textgrid_file(path, fname):
    ''' checks textgrid for back and forth of "silent" and "sounding" labels 

        finds common errors that may occur during manual vad correction '''
    all_good = True
    intervals = read_textgrid_file(path, fname)
    for i in range(len(intervals)-1):
        if intervals[i][2] not in ['silent', 'sounding']:
            print('typo in label', intervals[i])
            all_good = False
        if intervals[i][2] == intervals[i+1][2]:
            print('same label twice', intervals[i], intervals[i+1])
            all_good = False
    return all_good


def extract_features(in_path, in_fname, ses_id, chu_id, words, start, end):
    ''' runs praat script for feature extraction on given chunk '''
    # determine tmp filenames
    cut_fname = '%d_%d.wav' % (ses_id, chu_id)
    out_fname = '%d_%d.txt' % (ses_id, chu_id)
    # extract audio and features
    subprocess.check_call(['sox', 
                           in_path + in_fname, 
                           cfg.TMP_PATH + cut_fname, 
                           'trim', str(start), '=' + str(end)])
    subprocess.check_call(['praat', '--run', 
                           cfg.PRAAT_SCRIPT_FNAME,
                           cfg.TMP_PATH + cut_fname, 
                           cfg.TMP_PATH + out_fname])
    # process output
    features = {}
    for line in readlines(cfg.TMP_PATH, out_fname):
        key, val = line.replace('\n', '').split(',')
        try:
            val = float(val)
        except:
            val = None
        features[key] = val
    features['rate_syl'] = aux.count_syllables(words) / (end - start)
    # clean up
    os.remove(cfg.TMP_PATH + cut_fname)
    os.remove(cfg.TMP_PATH + out_fname)
    
    return features





