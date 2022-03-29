# Processing and analysis of B-MIC

The Brooklyn Multi-Interaction Corpus (B-MIC) was designed for the analysis of entrainment - the adaptation of speakers to their interlocutors to become more similar with regards to the words they use, how they say them, and so on - and variations in this behavior across speakers and contexts. Each subject interacts with three others in pairwise conversation, as well as with a dialogue interface realized through the Wizard of Oz paradigm, so we can observe which aspects of their behavior are consistent and which vary across interlocutors. The corpus includes two different registers of dialogue - conversational and task-oriented - so we can analyze how entrainment behavior differs based on dialogue context, with all other factors held constant.

This repository contains code for the initial processing of the audio and log files as well as for entrainment analysis. The corpus itself is not included but available on request. 

An analysis regarding the influence of personality traits on entrainment, with full results, can be found in jupyter/7_lme.ipynb.

## Directory Overview

<ul>
    <li>jupyter: a sequence of Jupyter notebooks that invoke all SQL/python code to process and analyze the corpus</li>
    <li>praat: Praat scripts for feature extraction and other auxiliary tasks</li>
    <li>python: modules for data processing and analysis invoked from the Jupyter notebooks; file overview:
        <ul>
            <li>ap.py: implementation of five acoustic-prosodic entrainment measures</li>
            <li>aux.py: auxiliary functions</li>
            <li>cfg.py: configuration constants; if you received the corpus data (separately), configure the correct paths here</li>
            <li>db.py: interaction with the corpus database</li>
            <li>fio.py: file i/o</li>
            <li>lme.py: functions for linear mixed effects analysis of the influence of personality</li>
            <li>logs.py: processing of corpus log files (not logging of the processing itself)</li>
            <li>vad_asr: voice activity detection and automatic speech recognition</li>
        </ul>
    </li>
    <li>R: contains single R file with functions for linear mixed effects analysis of the influence of personality</li>
    <li>smile: openSMILE script used for energy level measurements as part of voice activity detection</li>
    <li>sql: core sql scripts that initialize the database and are used during processing/analysis; file overview:
        <ul>
            <li>aux_tables.sql: creates chunk_pairs table with turn exchanges and non-adjacent IPU pairs for local entrainment measures</li>
            <li>big_table.sql: SELECT to flatten normalized, hierarchical schema into one wide, unnormalized table for analysis</li>
            <li>cleanup.sql: auxiliary script for cleanup after feature extraction</li>
            <li>init.sql: creates and documents the hierarchical database schema</li>
            <li>process_question_responses.sql: processes subject responses to demographic and psychological questionnaires</li>
            <li>speaker_pairs.sql: SELECT to determine partner and non-partner pairs of speakers for analysis</li>
        </ul>
    </li>
</ul>
