import math
import pandas as pd

import ap
import cfg
import db

extra_cols = [
    'task_index', 'speaker_role', 'start_time', 'duration', 
    'score_z', 'prev_score_z', 'spk_id', 'sex', 'words',
    'tipi_o_hl', 'tipi_c_hl', 'tipi_e_hl', 'tipi_a_hl', 'tipi_n_hl', 
    'iri_pt_hl', 'mc_sds_hl', 'rmi_hl'
]

extra_cols_paired = [c + '_paired' for c in extra_cols]


def _remove_fea_outliers(df_bt):
    # mean and std for each feature for *all* chunks
    df_means = df_bt[cfg.FEATURES].mean()
    df_stds = df_bt[cfg.FEATURES].std()
    # mean and std for each feature per speaker 
    df_spk_means = df_bt[cfg.FEATURES + ['spk_id']].groupby('spk_id').mean()
    df_spk_stds = df_bt[cfg.FEATURES + ['spk_id']].groupby('spk_id').std()
    # filter out anything except actual turn exchanges
    df_bt = df_bt[df_bt['p_or_x']=='p']
    # add columns for speaker and partner mean/std for all features
    df_bt = df_bt.join(df_spk_means, on='spk_id', rsuffix='_spk_mn')
    df_bt = df_bt.join(df_spk_stds, on='spk_id', rsuffix='_spk_std')
    df_bt = df_bt.join(df_spk_means, on='spk_id_paired', rsuffix='_prd_mn')
    df_bt = df_bt.join(df_spk_stds, on='spk_id_paired', rsuffix='_prd_std')
    print("turn exchanges before removing feature outliers:", len(df_bt))
    # filter out any row in which either chunk is an outlier for any feature
    for f in cfg.FEATURES:
        # overall outliers
        df_bt = df_bt[(df_bt[f] >= df_means[f]-3*df_stds[f])&
                      (df_bt[f] <= df_means[f]+3*df_stds[f])]
        df_bt = df_bt[(df_bt[f + '_paired'] >= df_means[f]-3*df_stds[f])&
                      (df_bt[f + '_paired'] <= df_means[f]+3*df_stds[f])]
        # speaker outliers
        df_bt = df_bt[(df_bt[f] 
                       >= df_bt[f + '_spk_mn']-3*df_bt[f + '_spk_std'])&
                      (df_bt[f] 
                       <= df_bt[f + '_spk_mn']+3*df_bt[f + '_spk_std'])]
        df_bt = df_bt[(df_bt[f + '_paired'] 
                       >= df_bt[f + '_prd_mn']-3*df_bt[f + '_prd_std'])&
                      (df_bt[f + '_paired'] 
                       <= df_bt[f + '_prd_mn']+3*df_bt[f + '_prd_std'])]
    print("after:", len(df_bt))
    return df_bt


def load_samples():
    db.connect()
    df_bt = ap.load_data(cfg.NRM_RAW, extra_cols)
    db.close()
    df_bt = _remove_fea_outliers(df_bt)
    # unpair turn-final and turn-initial chunks, list them in separate rows
    cols1 = ['chu_id'] + cfg.FEATURES + extra_cols
    df_samples = df_bt[cols1 + ['ses_type']].copy()
    df_samples['final'] = False
    cols2 = [c + '_paired' for c in cols1]
    df_tmp = df_bt[cols2 + ['ses_type']].copy()
    df_tmp = df_tmp.rename(columns={c + '_paired': c for c in cols1})
    df_tmp['final'] = True
    df_tmp = df_tmp.astype(df_samples.dtypes)
    df_samples = pd.concat([df_samples, df_tmp])
    # split game and conv sessions for separate feature prediction
    df_samples_games = df_samples[df_samples['ses_type']=='GAME'].copy()
    df_samples_convs = df_samples[df_samples['ses_type']=='CONV'].copy()
    return df_samples, df_samples_games, df_samples_convs


def get_residuals_old(df, pred_int, pred_pit, pred_rat, pred_shi, ses_type):
    df['intensity_mean_pred'] = pred_int
    df['pitch_mean_pred'] = pred_pit
    df['rate_syl_pred'] = pred_rat
    df['shimmer_pred'] = pred_shi
    res_cols = ['residuals', 'residuals_paired']

    features_subset = [
        'intensity_mean', 
        'pitch_mean', 
        'rate_syl', 
        'shimmer'
    ]
    
    # index of df contains each value twice; join chunk pairs again 
    # before computing residuals for more convenient joins below
    df = df[df['final'] == False].join(df[df['final'] == True], 
                                       rsuffix='_paired')
    
    # compute residuals and collect them in single dataframe
    df_out = pd.DataFrame(
        None, columns=res_cols + extra_cols + extra_cols_paired)
    for f in features_subset:
        for suff in ['', '_paired']:
            # for current feature and turn-initial/-final chunks,
            # compute z-score normalized residuals
            residuals = df[f + suff] - df[f + '_pred' + suff]
            residuals = (residuals - residuals.mean()) / residuals.std()
            residuals.name = f + '_residuals' + suff
            df = df.join(residuals)
        # add residuals for current feature to overall dataframe
        f_cols = [f + '_residuals', f + '_residuals_paired']
        df_sub = df[f_cols + extra_cols + extra_cols_paired].copy()
        df_sub['feature'] = f
        df_sub['ses_type'] = ses_type
        df_sub.rename(columns={f + '_' + c: c for c in res_cols}, 
                      inplace=True)
        df_out = pd.concat([df_out, df_sub])
    return df_out


def get_residuals(df, pred_int, pred_pit, pred_rat, pred_shi, ses_type, nrm):
    assert nrm in ['all', 'spk'], 'unknown residual normalization type'
    df['intensity_mean_pred'] = pred_int
    df['pitch_mean_pred'] = pred_pit
    df['rate_syl_pred'] = pred_rat
    df['shimmer_pred'] = pred_shi
    res_cols = ['residuals', 'residuals_paired']
    features_subset = [
        'intensity_mean', 
        'pitch_mean', 
        'rate_syl', 
        'shimmer'
    ]

    # df contains running index with each value twice;
    # add "final" column to differentiate
    df = df.set_index(['final'], append=True)

    # compute z-score normalized residuals for all features
    for f in features_subset:
        col = f + '_residuals'
        # compute residuals
        residuals = df[f] - df[f + '_pred']
        residuals.name = col
        df = df.join(residuals)
        # z-score normalize overall or per speaker
        if nrm == 'all':
            df[col] = (df[col] - df[col].mean()) / df[col].std()
        else: # nrm == 'spk'
            df = df.join(df.groupby(['spk_id'])[col].mean(),
                         on='spk_id', rsuffix='_mn')
            df = df.join(df.groupby(['spk_id'])[col].std(), 
                         on='spk_id', rsuffix='_std')
            df[col] = (df[col] - df[col + '_mn']) / df[col + '_std']
    df.reset_index(level=1, inplace=True)
    df = df[df['final'] == False].join(df[df['final'] == True], 
                                       rsuffix='_paired')
    # collect residuals for all features in single column in new dataframe
    df_out = pd.DataFrame(
        None, columns=res_cols + extra_cols + extra_cols_paired)
    for f in features_subset:
        # add residuals for current feature to overall dataframe
        f_cols = [f + '_residuals', f + '_residuals_paired']
        df_sub = df[f_cols + extra_cols + extra_cols_paired].copy()
        df_sub['feature'] = f
        df_sub['ses_type'] = ses_type
        df_sub.rename(columns={f + '_' + c: c for c in res_cols}, 
                      inplace=True)
        df_out = pd.concat([df_out, df_sub])
    return df_out


def remove_res_outliers(df, df_samples):
    df_outliers = pd.DataFrame(columns=['feature', 'hi_lo', 'final'])
    for suff in ['', '_paired']:
        for hi_lo in ['hi', 'lo']:
            if hi_lo == 'hi':
                fltr = df['residuals' + suff] >= 3
            else:
                fltr = df['residuals' + suff] <= -3
            df_tmp = df[fltr][['feature']]
            df_tmp['hi_lo'] = hi_lo
            df_tmp['final'] = suff == '_paired'
            df_outliers = pd.concat([df_outliers, df_tmp])
    df_tmp = df_samples.loc[set(df_outliers.index)].join(
        df_outliers, rsuffix='_outlier')
    df_outliers = df_tmp[
        df_tmp['final'] == df_tmp['final_outlier']].copy()
    df_outliers['value'] = df_outliers.apply(
        lambda x: x[x['feature']], axis=1)
    loc_cols = ['chu_id', 'final', 'feature', 'value', 'hi_lo', 
                'words', 'duration'] 
    df_outliers = df_outliers.loc[:,loc_cols]
    incl = sorted(list(set(df.index) - set(df_outliers.index)))
    df_final_samples = df_samples.loc[incl].copy()
    print("ipus before removing residual outliers:", len(df_samples))
    print("after:", len(df_final_samples))
    return df_final_samples, df_outliers


def _rename_vars(x, col):
    out_str = x[col] if x[col] is not None else ''
    out_str = out_str.replace('.', ':')
    out_str = out_str.replace('df$residuals_paired', 'TFR')
    out_str = out_str.replace('df$sex1', 'speaker.sex')
    out_str = out_str.replace('df$sex_paired1', 'partner.sex')
    out_str = out_str.replace('df$tipi_o_hl1', 'speaker.tipi_o')
    out_str = out_str.replace('df$tipi_c_hl1', 'speaker.tipi_c')
    out_str = out_str.replace('df$tipi_e_hl1', 'speaker.tipi_e')
    out_str = out_str.replace('df$tipi_a_hl1', 'speaker.tipi_a')
    out_str = out_str.replace('df$tipi_n_hl1', 'speaker.tipi_n')
    out_str = out_str.replace('df$mc_sds_hl1', 'speaker.mc_sds')
    out_str = out_str.replace('df$iri_pt_hl1', 'speaker.iri_pt')
    out_str = out_str.replace('df$rmi_hl1', 'speaker.tom')
    out_str = out_str.replace('df$tipi_o_hl_paired1', 'partner.tipi_o')
    out_str = out_str.replace('df$tipi_c_hl_paired1', 'partner.tipi_c')
    out_str = out_str.replace('df$tipi_e_hl_paired1', 'partner.tipi_e')
    out_str = out_str.replace('df$tipi_a_hl_paired1', 'partner.tipi_a')
    out_str = out_str.replace('df$tipi_n_hl_paired1', 'partner.tipi_n')
    out_str = out_str.replace('df$mc_sds_hl_paired1', 'partner.mc_sds')
    out_str = out_str.replace('df$iri_pt_hl_paired1', 'partner.iri_pt')
    out_str = out_str.replace('df$rmi_hl_paired1', 'partner.tom')
    out_str = out_str.replace('df$speaker_role1', 'speaker.role')
    out_str = out_str.replace('df$speaker_role_paired1', 'partner.role')
    out_str = out_str.replace('df$score_z', 'task.score')
    out_str = out_str.replace('df$prev_score_z', 'task.prev_score')
    out_str = out_str.replace('df$ses_type1', 'session.type')
    out_str = out_str.replace('(Intercept)', '1')
    out_str = out_str.replace('df:feature', 'feature')
    out_str = out_str.replace('df$feature', 'feature')
    out_str = out_str.replace('df:spk_id_paired', 'partner.id')
    out_str = out_str.replace('df$spk_id_paired', 'partner.id')
    out_str = out_str.replace('df:spk_id', 'speaker.id')
    out_str = out_str.replace('df$spk_id', 'speaker.id')
    out_str = out_str.replace('df$sex_paired', 'partner.sex')
    out_str = out_str.replace('df$sex', 'speaker.sex')
    out_str = out_str.replace('df$tipi_o_hl_paired', 'partner.tipi_o')
    out_str = out_str.replace('df$tipi_c_hl_paired', 'partner.tipi_c')
    out_str = out_str.replace('df$tipi_e_hl_paired', 'partner.tipi_e')
    out_str = out_str.replace('df$tipi_a_hl_paired', 'partner.tipi_a')
    out_str = out_str.replace('df$tipi_n_hl_paired', 'partner.tipi_n')
    out_str = out_str.replace('df$mc_sds_hl_paired', 'partner.mc_sds')
    out_str = out_str.replace('df$iri_pt_hl_paired', 'partner.iri_pt')
    out_str = out_str.replace('df$rmi_hl_paired', 'partner.tom')
    out_str = out_str.replace('df$tipi_o_hl', 'speaker.tipi_o')
    out_str = out_str.replace('df$tipi_c_hl', 'speaker.tipi_c')
    out_str = out_str.replace('df$tipi_e_hl', 'speaker.tipi_e')
    out_str = out_str.replace('df$tipi_a_hl', 'speaker.tipi_a')
    out_str = out_str.replace('df$tipi_n_hl', 'speaker.tipi_n')
    out_str = out_str.replace('df$mc_sds_hl', 'speaker.mc_sds')
    out_str = out_str.replace('df$iri_pt_hl', 'speaker.iri_pt')
    out_str = out_str.replace('df$rmi_hl', 'speaker.tom')
    out_str = out_str.replace('df$speaker_role_paired', 'partner.role')
    out_str = out_str.replace('df$speaker_role', 'speaker.role')
    out_str = out_str.replace('df$ses_type', 'session.type')
    out_str = out_str.replace(':1', '')
    return out_str


def _get_rnd_term(x):
    if x['grp'] == 'Residual':
        out_str = 'Residual'
    else:
        out_str = '(' + ('0+' if x['var1'] != '1' else '')
        out_str += x['var1'] + '|' + x['grp'] + ')'
    return out_str


def _process_res_fix_df(df_res_fix, suff):
    df_res_fix = df_res_fix.rename(
        columns= {
            'Estimate': '$est', 
            'Std. Error': '$SE', 
            'df': '$df', 
            't value': '$t', 
            'Pr(>|t|)': '$p'
    })
    df_res_fix = df_res_fix.rename(
        columns={c: c + '_{' + suff + '}$' for c in df_res_fix.columns})
    return df_res_fix


def process_res_fix_dfs(
        df_res_fix_game, df_res_fix_conv, df_res_fix_both, fix_fx_terms):
    df_res_fix_game = _process_res_fix_df(df_res_fix_game, 'G')
    df_res_fix_conv = _process_res_fix_df(df_res_fix_conv, 'C')
    df_res_fix_both = _process_res_fix_df(df_res_fix_both, 'B')
    df_res_fix = df_res_fix_game.join(
        df_res_fix_conv, how='outer').join(
        df_res_fix_both, how='outer')
    df_res_fix = df_res_fix.reset_index()
    df_res_fix['term'] = df_res_fix.apply(_rename_vars, args=('index',), axis=1)
    df_res_fix.drop(['index'], axis=1, inplace=True)
    df_res_fix.set_index(['term'], inplace=True)
    # empty column for visual separation in the joint table
    df_res_fix['-'] = ' '
    return df_res_fix.reindex([_rename_vars(v, 0) for v in fix_fx_terms])


def _process_res_rnd_df(df_res_rnd, res_comp, suff):
    df_res_rnd.rename(columns={'sdcor': '$SD_{' + suff + '}$'}, inplace=True)
    df_res_rnd['grp'] = df_res_rnd.apply(_rename_vars, args=('grp',), axis=1)
    df_res_rnd['var1'] = df_res_rnd.apply(_rename_vars, args=('var1',), axis=1)
    df_res_rnd['term'] = df_res_rnd.apply(_get_rnd_term, axis=1)
    df_res_rnd.drop(['grp', 'var1', 'var2', 'vcov'], axis=1, inplace=True)
    dct = {}
    for term, res in res_comp:
        dct[_rename_vars(term, 0)] = {'$AIC_{'+suff+'}$': res[1][1]-res[1][0], 
                                      '$chi2_{'+suff+'}$': res[5][1], 
                                      '$p_{'+suff+'}$': res[7][1]}
    return df_res_rnd.set_index(['term']).join(pd.DataFrame(dct).transpose())


def process_rnd_dfs(
        df_res_rnd_game, df_res_rnd_conv, df_res_rnd_both, 
        res_comp_game, res_comp_conv, res_comp_both, rnd_fx_terms):
    df_res_rnd_game = _process_res_rnd_df(df_res_rnd_game, res_comp_game, 'G')
    df_res_rnd_conv = _process_res_rnd_df(df_res_rnd_conv, res_comp_conv, 'C')
    df_res_rnd_both = _process_res_rnd_df(df_res_rnd_both, res_comp_both, 'B')
    df_res_rnd = df_res_rnd_game.join(
        df_res_rnd_conv, how='outer').join(
        df_res_rnd_both, how='outer')
    # empty column for visual separation in the joint table
    df_res_rnd['-'] = ' '
    return df_res_rnd.reindex([_rename_vars(v, 0) for v in rnd_fx_terms])


def float_format(num):
    if math.isnan(num):
        out_str = 'n/a'
    elif abs(num) < 0.001:
        out_str = '{:.1e}'.format(num)
    elif abs(num) < 0.01:
        out_str = '{:.4f}'.format(num)
    elif abs(num) < 0.1:
        out_str = '{:.3f}'.format(num)
    elif abs(num) < 1:
        out_str = '{:.2f}'.format(num)
    else:
        out_str = '{:.1f}'.format(num)
    return out_str


