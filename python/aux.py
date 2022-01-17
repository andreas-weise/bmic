from datetime import datetime
from datetime import timedelta
import hyphenate
import nltk
import pandas as pd

import cfg

cmu_dict = nltk.corpus.cmudict.dict()

# this module contains some auxiliary functions used throughout other modules



def round_ts(ts):
    ''' rounds timestamp to two decimals (in str or float, out str) '''
    # use string format rounding to cut off rounding errors
    # return str so formatting choices are made only here
    # (other places only print %s, not %.2f etc.)
    return '%.2f' % float(ts)


def get_ts(line):
    return datetime.strptime(line.split('\t')[0], cfg.TS_FMT)


def get_ts_offset(ts_start, line):
    return round_ts((get_ts(line) - ts_start) / timedelta(seconds=1))


def get_spk_id(grp_id, mch_id):
    return (4 * (grp_id-1) + mch_id) if mch_id != 'W' else 0


def get_ses_id(grp_id, rnd, pair):
    return 14 * (grp_id-1) + 2 * (rnd-1) + pair


def has_games_first(grp_id):
    return 1 if grp_id % 2 == 1 else 0


def is_first_game_round(grp_id, rnd):
    return (has_games_first(grp_id) and rnd==1) \
        or (not has_games_first(grp_id) and rnd==3)


def count_syllables(in_str):
    ''' counts the number of syllables in a given string '''
    syll_count = 0
    for word in in_str.split(' '):
        ### PREPROCESSING
        # remove whitespace and convert to lowercase for dictionary lookup
        word = word.strip().lower()
        # '-' marks incomplete words; remove it
        if len(word) > 0 and word[-1] == '-':
            word = word[:-1]
        # remove trailing "'s" if word with it is not in dictionary
        # (does not change syllable count) 
        if len(word) > 1 and word[-2:] == "'s" and word not in cmu_dict:
            word = word[:-2]

        ### SPECIAL CASES
        # there are no syllables in an empty string
        if len(word) == 0:
            syll_count += 0
        # annotators are instructed to transcribe unintelligible speech with one
        # '?' per syllable (this is the only punctuation they are asked to use)
        elif '?' in word:
            syll_count += sum([1 if c == '?' else 0 for c in word])
        # standard method does not work for 'm&m', handle it separately
        # (word shows up often because it is one of the images in B-MIC)
        elif word in ['m&m', 'm&ms']:
            syll_count += 3
        ### STANDARD METHOD (dictionary lookup; fallback: automatic hyphenation)
        elif word in cmu_dict:
            # word is in the dictionary, extract number of vowels in primary
            # pronunciation as syllable count; vowels are recognizable by their 
            # stress markers (final digit), for example:
            #     cmu_dict["natural"][0] = ['N', 'AE1', 'CH', 'ER0', 'AH0', 'L']
            syll_count += sum([1 for p in cmu_dict[word][0] if p[-1].isdigit()])
        else:
            # fall back to the hyphenate library for a best guess (imperfect)
            syll_count += len(hyphenate.hyphenate_word(word))
    return syll_count


def get_df(data, index_names):
    ''' creates pandas dataframe from given data with given index names '''
    df = pd.DataFrame(data)
    df.index.set_names(index_names, inplace=True)
    return df
