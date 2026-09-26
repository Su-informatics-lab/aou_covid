
suppressPackageStartupMessages({library(survival)})
m <- read.csv("/home/jupyter/flu/07_matched_cohort.csv", stringsAsFactors=FALSE)
CH <- c("Myocardial_Infarction","Congestive_Heart_Failure","Peripheral_Vascular_Disease",
"Cerebrovascular_Disease","Dementia","Chronic_Pulmonary_Disease","Rheumatic_Disease",
"Peptic_Ulcer_Disease","Liver_Disease_Mild","Liver_Disease_Moderate_Severe",
"Diabetes_without_Chronic_Complications","Diabetes_with_Chronic_Complications",
"Hemiplegia_Paraplegia","Renal_Disease_Mild_Moderate","Renal_Disease_Severe","HIV",
"Metastatic_Solid_Tumor","Malignancy","AIDS")
rl <- function(x,r) relevel(factor(x), ref=r)
m$income<-rl(m$income,"35k_100k"); m$employment<-rl(m$employment,"Employed")
m$education<-rl(m$education,"GED_or_College"); m$housing<-rl(m$housing,"Own")
m$housing_stability<-rl(m$housing_stability,"Stable")
m$insurance_type<-rl(m$insurance_type,"Employer"); m$age_group<-rl(m$age_group,"18-44")
m$race<-rl(m$race,"White")
BASE <- paste(c("sex_at_birth","race","ethnicity","age_group",CH), collapse=" + ")
DOM <- c("insurance_type","income","employment","education","housing","housing_stability")
fit <- function(dat, rhs, tag){
  f <- as.formula(paste("Treatment ~", rhs, "+ strata(subclass)"))
  o <- try(clogit(f, data=dat, method="efron", cluster=person_id), silent=TRUE)
  if (inherits(o,"try-error")) { cat("FAIL",tag,":",attr(o,"condition")$message,"\n"); return(NULL) }
  ci <- summary(o)$conf.int; s <- summary(o)$coefficients
  data.frame(model=tag, term=rownames(ci), aor=round(ci[,1],3), lo=round(ci[,3],3),
             hi=round(ci[,4],3), p=signif(s[,ncol(s)],3), row.names=NULL)
}
out <- list()
for (per in c("ALL","1_pre","2_pandemic","3_post")) {
  dat <- if (per=="ALL") m else m[m$period==per,]
  for (dm in DOM) out[[length(out)+1]] <- fit(dat, paste(BASE,"+",dm), paste0(per,"|dom|",dm))
  out[[length(out)+1]] <- fit(dat, paste(BASE,"+",paste(DOM,collapse=" + ")), paste0(per,"|joint"))
}
res <- do.call(rbind,out); write.csv(res,"/home/jupyter/flu/08_models.csv",row.names=FALSE)
sel <- res[grepl("^(insurance_type|income|employment|education|housing)", res$term),]
fmt <- function(x) sprintf("%.2f (%.2f-%.2f)%s", x$aor, x$lo, x$hi,
        ifelse(x$p<0.001,"***",ifelse(x$p<0.01,"**",ifelse(x$p<0.05,"*",""))))
cat("\n===== POOLED: domain-specific vs joint =====\n")
dm <- sel[grepl("^ALL\\|dom", sel$model),]; jt <- sel[sel$model=="ALL|joint",]
dm <- dm[!duplicated(dm$term),]; jt <- jt[!duplicated(jt$term),]
mg <- merge(dm[,c("term","aor","lo","hi","p")], jt[,c("term","aor","lo","hi","p")], by="term", suffixes=c(".d",".j"))
for (i in seq_len(nrow(mg))) cat(sprintf("  %-42s dom %-22s joint %s\n", mg$term[i],
  fmt(data.frame(aor=mg$aor.d[i],lo=mg$lo.d[i],hi=mg$hi.d[i],p=mg$p.d[i])),
  fmt(data.frame(aor=mg$aor.j[i],lo=mg$lo.j[i],hi=mg$hi.j[i],p=mg$p.j[i]))))
