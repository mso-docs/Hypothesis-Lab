# Statistical methodology

For a prior Beta(α,β) and k successes in n eligible independent trials, conjugacy gives Beta(α+k, β+n−k). The posterior mean is (α+k)/(α+β+n). The interval is the equal-tailed 95% credible interval computed using SciPy's beta quantile function.

Sequential updates pool independent batches and must equal the pooled update regardless of order. Trial dependence, changing event definitions, overlapping studies, or heterogeneous probabilities violate this demonstration's assumptions.

For simple hypotheses H0:p=p0 and H1:p=p1, the log Bayes factor is k log(p1/p0)+(n−k) log((1−p1)/(1−p0)). The binomial coefficient cancels. This is evidence between fixed event probabilities, not a causal effect or a posterior probability of the natural-language scientific claim.

The likelihood curve is normalized over p for display and labeled accordingly. It is not a probability distribution for p until combined with a specified prior.

All demo observations are synthetic. Literature extracts remain qualitative unless a researcher separately validates quantitative observations and sampling assumptions. The system does not convert support labels into likelihood ratios.
