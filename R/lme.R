library(lme4)
library(lmerTest)
library(MuMIn)
library(sets)


rnd_fx_terms <- list(
    "(1|df$feature)",
    "(1|df$spk_id)",
    "(1|df$spk_id_paired)",
    "(0+df$residuals_paired|df$feature)",
    "(0+df$residuals_paired|df$spk_id)",
    "(0+df$residuals_paired|df$spk_id_paired)",
    "(1|df$feature:df$spk_id)",
    "(1|df$feature:df$spk_id_paired)",
    "(0+df$residuals_paired|df$feature:df$spk_id)",
    "(0+df$residuals_paired|df$feature:df$spk_id_paired)"
)


fix_fx_terms_fea <- list(
    "1",
    "df$final",
    "df$duration",
    "df$start_time",
    "df$sex",
    "df$tipi_o_hl",
    "df$tipi_c_hl",
    "df$tipi_e_hl",
    "df$tipi_a_hl",
    "df$tipi_n_hl",
    "df$mc_sds_hl",
    "df$iri_pt_hl",
    "df$rmi_hl",
    "df$speaker_role",
    "df$score_z",
    "df$prev_score_z",
    "df$ses_type"
)


fix_fx_terms_ent <- list (
    "1",
    "df$residuals_paired",
    "df$residuals_paired:df$sex",
    "df$residuals_paired:df$sex_paired",
    "df$residuals_paired:df$tipi_o_hl",
    "df$residuals_paired:df$tipi_c_hl",
    "df$residuals_paired:df$tipi_e_hl",
    "df$residuals_paired:df$tipi_a_hl",
    "df$residuals_paired:df$tipi_n_hl",
    "df$residuals_paired:df$mc_sds_hl",
    "df$residuals_paired:df$iri_pt_hl",
    "df$residuals_paired:df$rmi_hl",
    "df$residuals_paired:df$tipi_o_hl_paired",
    "df$residuals_paired:df$tipi_c_hl_paired",
    "df$residuals_paired:df$tipi_e_hl_paired",
    "df$residuals_paired:df$tipi_a_hl_paired",
    "df$residuals_paired:df$tipi_n_hl_paired",
    "df$residuals_paired:df$mc_sds_hl_paired",
    "df$residuals_paired:df$iri_pt_hl_paired",
    "df$residuals_paired:df$rmi_hl_paired",
    "df$residuals_paired:df$speaker_role",
    "df$residuals_paired:df$speaker_role_paired",
    "df$residuals_paired:df$score_z",
    "df$residuals_paired:df$prev_score_z",
    "df$residuals_paired:df$ses_type"
)


sum_code <- function(df, col, ref, n=2) {
    if(col %in% colnames(df)) {
        df[[col]] <- as.factor(df[[col]])
        df[[col]] <- relevel(df[[col]], ref)
        contrasts(df[[col]]) <- contr.sum(n)
    }
    return(df)
}


make_factor <- function(df, col) {
    if(col %in% colnames(df)) {
        df[[col]] <- as.factor(df[[col]])
    }
    return(df)
}


prep_data <- function(df) {
    df <- sum_code(df, "final", "TRUE")
    if(length(which(df$ses_type=="CONV")) > 0 &&
       length(which(df$ses_type=="GAME")) > 0)
        df <- sum_code(df, "ses_type", "CONV")
    df <- sum_code(df, "speaker_role", "d")
    df <- sum_code(df, "speaker_role_paired", "d")
    df <- sum_code(df, "sex", "f")
    df <- sum_code(df, "sex_paired", "f")
    trait_cols <- list("tipi_o_hl", "tipi_o_hl_paired",
                       "tipi_c_hl", "tipi_c_hl_paired",
                       "tipi_e_hl", "tipi_e_hl_paired",
                       "tipi_a_hl", "tipi_a_hl_paired",
                       "tipi_n_hl", "tipi_n_hl_paired",
                       "mc_sds_hl", "mc_sds_hl_paired",
                       "iri_pt_hl", "iri_pt_hl_paired",
                       "rmi_hl",    "rmi_hl_paired")
    for (trait_col in trait_cols)
        df <- sum_code(df, trait_col, "h")
    df <- make_factor(df, "feature")
    df <- make_factor(df, "spk_id")
    df <- make_factor(df, "spk_id_paired")
    return(df)
}


get_fea_formula <- function(dep_var, ses_type) {
    frm <- dep_var
    op <- " ~ "
    for (i in 1:13) {
        frm <- paste(frm, op, fix_fx_terms_fea[i])
        op <- " + "
    }
    if(ses_type == "GAME")
        for (i in 14:16)
            frm <- paste(frm, " + ", fix_fx_terms_fea[i])
    if(ses_type == "BOTH")
        frm <- paste(frm, " + ", fix_fx_terms_fea[17])
    frm <- paste(frm, " + (1|df$spk_id)")
    return(formula(frm))
}

get_feature_pred <- function(dep_var, ses_type) {
    frm <- get_fea_formula(dep_var, ses_type)
    print(frm)
    m <- lmer(frm)
    print(summary(m))
    print(MuMIn::r.squaredGLMM(m))
    return(predict(m))
}


get_ent_formula <- function(rnd_fx_ids, ses_type) {
    frm <- "df$residuals"
    op <- " ~ "
    for (i in 1:20) {
        frm <- paste(frm, op, fix_fx_terms_ent[i])
        op <- " + "
    }
    if(ses_type == "GAME")
        for (i in 21:24)
            frm <- paste(frm, " + ", fix_fx_terms_ent[i])
    if(ses_type == "BOTH")
        frm <- paste(frm, " + ", fix_fx_terms_ent[25])
    for (id in rnd_fx_ids)
        frm <- paste(frm, " + ", rnd_fx_terms[id])
    return(formula(frm))
}


get_ent_model <- function(
        rnd_fx_ids, ses_type, print_formula, print_summary, print_r2) {
    frm <- get_ent_formula(rnd_fx_ids, ses_type)
    m = lmer(frm)
    if(print_formula)
        print(frm)
    if(print_summary)
        print(summary(m))
    if(print_r2)
        print(MuMIn::r.squaredGLMM(m))
    return(m)
}


run_model_comp <- function(m0, rnd_fx_ids, ses_type) {
    out <- list()
    if(length(rnd_fx_ids) > 1)
        for (i in 1:length(rnd_fx_ids)) {
            m_sub <- get_ent_model(
                rnd_fx_ids[-i], ses_type, FALSE, FALSE, FALSE)
            rnd_term <- rnd_fx_terms[[rnd_fx_ids[[i]]]]
            res <- as.data.frame(anova(m0, m_sub))
            print(rnd_term)
            print(res)
            out <- append(out, list(pair(rnd_term, res)))
        }
    else
        print('no model comparison, needs at least two random effects!')
    return(out)
}


run_models <- function(rnd_fx_ids, ses_type) {
    df <<- prep_data(df)
    # main model computation, with print
    m0 <- get_ent_model(rnd_fx_ids, ses_type, FALSE, TRUE, TRUE)
    # results for random and fixed effects 
    df_res_rnd <- as.data.frame(VarCorr(m0))
    df_res_fix <- as.data.frame(coef(summary(m0)))
    # model comparison to get p-values for random effects
    res_comp <- run_model_comp(m0, rnd_fx_ids, ses_type)
    return(triple(df_res_rnd, df_res_fix, res_comp))
}


