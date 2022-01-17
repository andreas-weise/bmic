import collections
import json
import os
import re
import sqlite3
import subprocess

import cfg
import db
import fio

# this module contains functions for voice activity detection and 
# automatic speech recognition in all collected audio files



################################################################################
#                        NON-PUBLIC AUXILIARY FUNCTIONS                        #
################################################################################

def _run_smile(wav_path, wav_fname):
    ''' runs opensmile to identify sounding frames for given audio '''
    sound_threshold = 0.000001
    frame_size = 0.01
    frame_step = 0.01
    csv_fname = wav_fname[:-3] + 'csv'
    # get energy values for all frames in the given wav file
    subprocess.check_call(
        ['SMILExtract', 
         '-C', '../smile/energy.conf', 
         '-I', wav_path + wav_fname, 
         '-csvoutput', cfg.TMP_PATH + csv_fname])
    # read csv and store timestamps and silence vs. sound in list
    frames = []
    with open(cfg.TMP_PATH + csv_fname) as file:
        for i, line in enumerate(file):
            frames += [(round(i * frame_step, 2), 
                        round(i * frame_step + frame_size, 2),
                        float(line) > sound_threshold)]
    os.remove(cfg.TMP_PATH + csv_fname)
    return frames


def _run_praat_prepend_silence(wav_path, wav_fname, sil_dur):
    ''' runs a praat script to prepend silence to a wav file '''
    # (initial silence was observed to improve asr accuracy)
    subprocess.check_call([
        'praat', '--run', '../praat/prepend_silence.praat',
        wav_path + wav_fname, wav_path + wav_fname, str(sil_dur)])


def _run_watson(cut_path, cut_fname, json_path, json_fname, dur):
    ''' runs watson asr on given audio slice '''
    # send segment to watson
    subprocess.check_call(
        ['curl', 
         '-X', 'POST', 
         '-u', 'apikey:' + cfg.API_KEY,
         '--header', 'Content-Type: audio/wav',
         '--data-binary', '@' + cut_path + cut_fname,
         cfg.API_URL + cfg.API_INS + 'v1/recognize?timestamps=true',
        '-o', json_path + json_fname])
    # process response
    with open(json_path + json_fname) as response:
        obj = json.loads(response.read())
    try:
        trans = obj['results'][0]['alternatives'][0]['transcript']
        trans = trans[:-1]
        ts = obj['results'][0]['alternatives'][0]['timestamps']
    except IndexError:
        trans = ''
        ts = [['', 0.0, dur]]
    os.remove(json_path + json_fname)
    return trans, ts


def _get_intervals(frames):
    ''' aggregates short frames into intervals of silence/sound '''
    # ring buffer algorithm adapted from 
    # https://github.com/wiseman/py-webrtcvad/blob/master/example.py
    get_label = lambda is_sounding: \
        'sounding' if is_sounding else 'silent'
    buf = collections.deque(maxlen=20)
    in_sound_interval = False
    intervals = [[0.0, 0.0, get_label(False)]]
    for frame in frames:
        if not in_sound_interval:
            buf.append(frame)
            # number of sounding frames in buffer
            cnt_snd = len([f for f in buf if f[2]])
            # position of last silent frame in buffer (0 if none)
            max_sil = max([i + 1 for i, f in enumerate(buf) 
                           if not f[2]] + [0])
            # position of first sounding frame in buffer
            # (or buf.maxlen+1 if there are none)
            min_snd = min([i + 1 for i, f in enumerate(buf) 
                           if f[2]] + [buf.maxlen+1])
            
            if (cnt_snd >= 0.7 * buf.maxlen) \
            or (len(buf) - max_sil > 4):
                # most frames in buffer or last five are sounding
                # -> switch state
                in_sound_interval = True
                if cnt_snd != len(buf):
                    intervals[-1][1] = buf[min_snd-1][0]
                elif len(intervals) == 1:
                    # audio begins with sounding interval, 
                    # remove empty initial silent interval
                    intervals = []
                intervals += [[buf[min_snd-1][0],
                               buf[-1][1],
                               get_label(True)]]
                buf.clear()
        else:
            buf.append(frame)
            # number of silent frames in buffer
            cnt_sil = len([f for f in buf if not f[2]])
            # position of last sounding frame in buffer (0 if none)
            max_snd = max([i + 1 for i, f in enumerate(buf) 
                           if f[2]] + [0])
            # switch state if last 5 in buffer are silent 
            if len(buf) - max_snd > 4:
                in_sound_interval = False
                if cnt_sil != len(buf):
                    intervals[-1][1] = buf[max_snd-1][1]
                    intervals += [[buf[max_snd-1][1],
                                   buf[-1][1],
                                   get_label(False)]]
                else:
                    intervals += [[buf[0][0],
                                   buf[-1][1],
                                   get_label(False)]]
                buf.clear()
    intervals[-1][1] = frames[-1][1]
    return intervals


def _preprocess_words(words):
    ''' preprocesses transcriptions to make them consistent '''
    words = words.lower()
    # fixing missing space in a few WOZ prompts 
    words = words.replace('thelawnmower', 'the lawnmower')
    words = words.replace('thenun', 'the nun')
    # make different spellings of the same thing consistent
    #     bigram vs. unigram (based on all bigrams that also appear as unigrams)
    words = words.replace('lawn mower', 'lawnmower')
    words = words.replace('nevermind', 'never mind')
    words = words.replace('right most', 'rightmost')
    words = words.replace('left most', 'leftmost')
    words = words.replace('bit coin', 'bitcoin')
    words = words.replace('ear lobe', 'earlobe')
    words = words.replace('alright', 'all right')
    #     punctuation differences
    words = words.replace('uh huh', 'uh-huh')
    words = words.replace("'cause", 'cause')
    words = words.replace("'til", 'til')
    #     transcription cannot consistently reflect duration
    words = words.replace('hmm', 'hm')
    return words



################################################################################
#                               PUBLIC FUNCTIONS                               #
################################################################################s

def vad(grp_id, mch_id, rnd, wav_path, wav_fname):
    ''' runs simple, energy-based vad for given machine's round '''
    vad_path, vad_fname = fio.get_vad_pfn(wav_fname)
    frames = _run_smile(wav_path, wav_fname)    
    intervals = _get_intervals(frames)
    fio.write_textgrid_file(vad_path, vad_fname, intervals)
    return sum([s[1] - s[0] for s in intervals if s[2] == 'sounding'])


def asr(grp_id, mch_id, rnd, wav_path, wav_fname):
    ''' runs watson asr for given machine's round '''
    # manually corrected vad file with sounding intervals to transcribe
    vad_path, vad_fname = fio.get_vad_pfn(wav_fname, 'corrected/')
    # directory to store cut wav files
    cut_path = '%s%d_%d_%d/' % (cfg.WAV_PATH, grp_id, mch_id, rnd)
    os.mkdir(cut_path)
    # print the vad filename and check the file for label errors
    print(vad_path + vad_fname)
    if not fio.check_vad_textgrid_file(vad_path, vad_fname):
        msg = 'vad file has errors; please fix them and rerun this'
        raise ValueError(msg)
    
    in_intervals = fio.read_textgrid_file(vad_path, vad_fname)
    out_intervals = []
    out_alignments = []
    asr_total_time = 0.0
    i = 0
    for xmin, xmax, text in in_intervals:
        if text == 'silent':
            # no transcription needed for silent intervals
            out_intervals += [[xmin, xmax, '<silence>']]
            out_alignments += [[xmin, xmax, '<silence>']]
            continue
        # enumerate manually because only non-empty intervals count
        i += 1 
        cut_fname = str(i) + '.wav'
        # extract audio segment from input wav file
        subprocess.check_call(
            ['sox', wav_path + wav_fname, cut_path + cut_fname, 
             'trim', str(xmin), '=' + str(xmax)])
        # prepend silence (improves transcription accuracy)
        sil_dur = 0.1
        _run_praat_prepend_silence(cut_path, cut_fname, sil_dur)
        # get asr transcript from watson
        json_fname = wav_fname[:-4] + '_' + str(i) + '.json'
        dur = xmax - xmin + sil_dur
        trans, ts = _run_watson(
            cut_path, cut_fname, cfg.TMP_PATH, json_fname, dur)
        asr_total_time += dur
        # store interval, without and with alignment (timestamps)
        out_intervals += [[xmin, xmax, trans]]
        out_alignments += [[round(xmin + max(0.0, v[1] - sil_dur), 2), 
                            round(xmin + max(0.0, v[2] - sil_dur), 2), 
                            v[0]] 
                           for v in ts]
        out_alignments[-1][1] = xmax
    fio.write_textgrid_file(
        cfg.ASR_PATH, wav_fname[:-3] + 'TextGrid', out_intervals)
    fio.write_transcript_file(cut_path, 'transcript.txt', out_intervals)
    fio.write_textgrid_file(
        cfg.ASR_PATH, wav_fname[:-4] + '_aligned.TextGrid', out_alignments)
    return asr_total_time


def do_all(func):
    ''' runs given function for all sessions of certain status '''
    if func == vad:
        status = 1
    elif func == asr:
        status = 3
    else:
        raise ValueError('unsupported function for do_all')

    total_time = 0.0
    for grp_id, ses_id, ses_type, rnd, mch_pair in db.find_sessions(status):
        for mch_id, wav_path, wav_fname in mch_pair:
            if mch_id == 0:
                continue
            total_time += func(grp_id, mch_id, rnd, wav_path, wav_fname)
            print(grp_id, mch_id, rnd, 'done')
        db.set_ses_status(ses_id, status+1)
    print(total_time)


def load_transcriptions():
    ''' loads asr and final transcriptions into the database for all chunks '''
    # loop through all folders in the wav directory
    for dname in os.listdir(cfg.WAV_PATH):
        # filter for grp_mch_rnd format (i.e., exclude "ses..." folders etc.)
        if not re.match('\d_\d_\d', dname):
            continue
        grp_id, mch_id, rnd = map(int, dname.split('_'))
        path = cfg.WAV_PATH + dname + '/'
        # read automatic and final, twice manually corrected, transcripts
        lines_asr = fio.readlines(path, cfg.TRANS_ASR_FNAME)
        lines_fin = fio.readlines(path, cfg.TRANS_FIN_FNAME)
        
        # sanity check the data
        if len(lines_asr) != len(lines_fin):
            err_str = 'Mismatched line count for ASR and final ' \
                'transcriptions for ' + dname
            raise ValueError(err_str)

        # loop through transcripts for all chunks
        for i, line in enumerate(lines_asr):
            ts1_asr, ts2_asr, words_asr = line.split('\t')
            ts1_fin, ts2_fin, words_fin = lines_fin[i].split('\t')
            # sanity check the data
            if ts1_asr != ts1_fin or ts2_asr != ts2_fin:
                err_str = 'Mismatched timestamps for ASR and final ' \
                    'transcriptions for line ' + i + ' in ' + dname
                raise ValueError(err_str)
            
            # update words_asr and words for chunk corresponding to this line
            db.set_words(grp_id, mch_id, rnd, 
                         float(ts1_asr), float(ts2_asr),
                         _preprocess_words(words_fin), words_asr)




