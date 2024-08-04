"""@author: Mukesh, Maitreya, Conte, Aakash"""  # noqa: CPY001, D400, INP001

import numpy as np
from scipy import stats


class Dist:  # noqa: D101
    def __init__(self, dist_name, params=None, moments=None, data=None):  # noqa: ANN001, ANN204
        self.dist_name = dist_name
        self.params = params
        self.moments = moments
        self.data = data
        if (params is None) and (moments is None) and (data is None):
            raise RuntimeError(  # noqa: TRY003
                'Atleast one of parameters, moments, or data must be specified when creating a random variable'  # noqa: EM101
            )


class Uniform:  # noqa: D101
    # Method with in this uniform class
    def __init__(  # noqa: ANN204
        self,
        lower,  # noqa: ANN001
        upper,  # noqa: ANN001
    ):  # method receives instance as first argument automatically
        # the below are the instance variables
        self.lower = lower
        self.upper = upper

    # Method to generate random numbers
    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return (self.upper - self.lower) * np.random.rand(N) + self.lower

    # Method to compute log of the pdf at x
    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        if (x - self.upper) * (x - self.lower) <= 0:
            lp = np.log(1 / (self.upper - self.lower))
        else:
            lp = -np.inf
        return lp


class Halfnormal:  # noqa: D101
    def __init__(self, sig):  # noqa: ANN001, ANN204
        self.sig = sig

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.sig * np.abs(np.random.randn(N))

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        if x >= 0:
            lp = (
                -np.log(self.sig)
                + 0.5 * np.log(2 / np.pi)
                - ((x * x) / (2 * self.sig * self.sig))
            )
        else:
            lp = -np.inf
        return lp


class Normal:  # noqa: D101
    def __init__(self, mu, sig):  # noqa: ANN001, ANN204
        self.mu = mu
        self.sig = sig

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.sig * np.random.randn(N) + self.mu

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        lp = (
            -0.5 * np.log(2 * np.pi)
            - np.log(self.sig)
            - 0.5 * (((x - self.mu) / self.sig) ** 2)
        )
        return lp  # noqa: RET504


class TrunNormal:  # noqa: D101
    def __init__(self, mu, sig, a, b):  # noqa: ANN001, ANN204
        self.mu = mu
        self.sig = sig
        self.a = a
        self.b = b

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return stats.truncnorm(
            (self.a - self.mu) / self.sig,
            (self.b - self.mu) / self.sig,
            loc=self.mu,
            scale=self.sig,
        ).rvs(N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        lp = stats.truncnorm(
            (self.a - self.mu) / self.sig,
            (self.b - self.mu) / self.sig,
            loc=self.mu,
            scale=self.sig,
        ).logpdf(x)
        return lp  # noqa: RET504


class mvNormal:  # noqa: D101
    def __init__(self, mu, E):  # noqa: ANN001, ANN204, N803
        self.mu = mu
        self.E = E
        self.d = len(mu)
        self.logdetE = np.log(np.linalg.det(self.E))
        self.Einv = np.linalg.inv(E)

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return np.random.multivariate_normal(self.mu, self.E, N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        xc = x - self.mu
        return (
            -(0.5 * self.d * np.log(2 * np.pi))
            - (0.5 * self.logdetE)
            - (0.5 * np.transpose(xc) @ self.Einv @ xc)
        )


class InvGamma:  # noqa: D101
    def __init__(self, a, b):  # noqa: ANN001, ANN204
        self.a = a
        self.b = b
        self.dist = stats.invgamma(self.a, scale=self.b)

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.dist.rvs(size=N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        return self.dist.logpdf(x)


class BetaDist:  # noqa: D101
    def __init__(self, alpha, beta, lowerbound, upperbound):  # noqa: ANN001, ANN204
        self.alpha = alpha
        self.beta = beta
        self.lowerbound = lowerbound
        self.upperbound = upperbound
        self.dist = stats.beta(
            self.alpha, self.beta, self.lowerbound, self.upperbound
        )

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.dist.rvs(size=N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        return self.dist.logpdf(x)


class LogNormDist:  # noqa: D101
    def __init__(self, mu, sigma):  # noqa: ANN001, ANN204
        # self.sigma = np.sqrt(np.log(zeta**2/lamda**2 + 1))
        # self.mu = np.log(lamda) - 1/2*self.sigma**2
        self.s = sigma
        self.loc = 0
        self.scale = np.exp(mu)
        self.dist = stats.lognorm(s=self.s, loc=self.loc, scale=self.scale)

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.dist.rvs(size=N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        return self.dist.logpdf(x)


class GumbelDist:  # noqa: D101
    def __init__(self, alpha, beta):  # noqa: ANN001, ANN204
        self.alpha = alpha
        self.beta = beta
        self.dist = stats.gumbel_r(loc=self.beta, scale=(1 / self.alpha))

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.dist.rvs(size=N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        return self.dist.logpdf(x)


class WeibullDist:  # noqa: D101
    def __init__(self, shape, scale):  # noqa: ANN001, ANN204
        self.shape = shape
        self.scale = scale
        self.dist = stats.weibull_min(c=self.shape, scale=self.scale)

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.dist.rvs(size=N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        return self.dist.logpdf(x)


class ExponentialDist:  # noqa: D101
    def __init__(self, lamda):  # noqa: ANN001, ANN204
        self.lamda = lamda
        self.scale = 1 / self.lamda
        self.dist = stats.expon(scale=self.scale)

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.dist.rvs(size=N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        return self.dist.logpdf(x)


class TruncatedExponentialDist:  # noqa: D101
    def __init__(self, lamda, lower, upper):  # noqa: ANN001, ANN204
        self.lower = lower
        self.upper = upper
        self.lamda = lamda
        self.scale = 1 / self.lamda
        self.loc = self.lower
        self.b = (self.upper - self.lower) / self.scale
        self.dist = stats.truncexpon(b=self.b, loc=self.loc, scale=self.scale)

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.dist.rvs(size=N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        return self.dist.logpdf(x)


class GammaDist:  # noqa: D101
    def __init__(self, k, lamda):  # noqa: ANN001, ANN204
        self.k = k
        self.lamda = lamda
        self.alpha = k
        self.beta = lamda
        self.scale = 1 / self.beta
        self.dist = stats.gamma(a=self.alpha, scale=self.scale)

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.dist.rvs(size=N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        return self.dist.logpdf(x)


class ChiSquareDist:  # noqa: D101
    def __init__(self, k):  # noqa: ANN001, ANN204
        self.k = k
        self.dist = stats.chi2(k=self.k)

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.dist.rvs(size=N)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, D102
        return self.dist.logpdf(x)


class DiscreteDist:  # noqa: D101
    def __init__(self, values, weights):  # noqa: ANN001, ANN204
        self.values = values
        self.weights = weights
        self.probabilities = self.weights / np.sum(self.weights)
        self.log_probabilities = np.log(self.weights) - np.log(np.sum(self.weights))
        self.rng = np.random.default_rng()

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return self.rng.choice(self.values, N, p=self.probabilities)

    def U2X(self, u):  # noqa: ANN001, ANN201, N802, D102
        cumsum_prob = np.cumsum(self.probabilities)
        cumsum_prob = np.insert(cumsum_prob, 0, 0)
        cumsum_prob = cumsum_prob[:-1]
        x = np.zeros_like(u)
        for i, u_comp in enumerate(u):
            cdf_val = stats.norm.cdf(u_comp)
            x[i] = self.values[np.where(cumsum_prob <= cdf_val)[0][-1]]
        return x

    def log_pdf_eval(self, u):  # noqa: ANN001, ANN201, D102
        x = self.U2X(u)
        lp = np.zeros_like(x)
        for i, x_comp in enumerate(x):
            lp[i] = self.log_probabilities[np.where(self.values == x_comp)]
        return lp


class ConstantInteger:  # noqa: D101
    def __init__(self, value) -> None:  # noqa: ANN001
        self.value = value

    def generate_rns(self, N):  # noqa: ANN001, ANN201, N803, D102
        return np.array([self.value for _ in range(N)], dtype=int)

    def log_pdf_eval(self, x):  # noqa: ANN001, ANN201, ARG002, D102, PLR6301
        return 0.0
