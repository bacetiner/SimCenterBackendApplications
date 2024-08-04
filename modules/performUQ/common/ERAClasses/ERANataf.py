# import of modules  # noqa: CPY001, D100, INP001
import numpy as np
from scipy import optimize, stats

realmin = np.finfo(np.double).tiny

"""
---------------------------------------------------------------------------
Nataf Transformation of random variables
---------------------------------------------------------------------------
Developed by:
Sebastian Geyer
Felipe Uribe
Max Ehre
Iason Papaioannou
Daniel Straub

Assistant Developers:
Luca Sardi
Fong-Lin Wu
Alexander von Ramm
Matthias Willer
Peter Kaplan
Ivan Pavlov

Engineering Risk Analysis Group
Technische Universitat Munchen
www.bgu.tum.de/era
---------------------------------------------------------------------------
Changelog

New Version 2023-05:
* Fix bug: return Jacobian dU/dX when calling X2U & dX/dU when calling U2X
New Version 2021-03:
* General update to match the current MATLAB version
* Consistent shape of the input and output arrays (also consistent with 
  scipy.stats standards)
* Adding additional error messages for discrete marginals in X2U and
  incorrect correlation matrix inputs
* Renaming the methods 'jointpdf' and 'jointcdf' to 'pdf' and 'cdf'
Version 2019-11:
* Minor check for improvement
Version 2019-01:
* Fixing of bug regarding dimensionality in random method
* Optimization and fixing of minor bugs
* Fixing of bugs in the transformation X to U and vice versa
* Alternative calculation of the Nataf joint CDF in high dimensions
---------------------------------------------------------------------------
* This software performs the Nataf transformation of random variables.
* It is possible to generate random numbers according to their Nataf
joint pdf and to evaluate this pdf.
* The inverse Nataf transformation is also defined as a function.
* It requires the use of Objects of the class ERADist which is also
published on the homepage of the ERA Group of TUM.
---------------------------------------------------------------------------
References:
1. Liu, Pei-Ling and Armen Der Kiureghian (1986) - Multivariate distribution
models with prescribed marginals and covariances.
Probabilistic Engineering Mechanics 1(2), 105-112
---------------------------------------------------------------------------
"""  # noqa: W291


# %%
class ERANataf:
    """Generation of joint distribution objects.
    Construction of the joint distribution object with

    Obj = ERANataf(M,Correlation)

    'M' must be an list or array of ERADist objects defining the marginal
    distributions that together define the joint distribution.

    'Correlation' must be a correlation matrix with shape [d,d], where d is
    the number of marginal distributions (dimensions) of the joint
    distribution. The matrix describes the dependency between the different
    marginal distributions. According to the general definition of a
    correlation matrix, the input matrix must be symmetric, the matrix entries
    on the diagonal must be equal to one, all other entries (correlation
    coefficients) can have values between -1 and 1.
    """  # noqa: D205, D400

    def __init__(self, M, Correlation):  # noqa: ANN001, ANN204, C901, N803
        """Constructor method, for more details have a look at the
        class description.
        """  # noqa: D205, D401
        self.Marginals = np.array(M, ndmin=1)
        self.Marginals = self.Marginals.ravel()
        self.Rho_X = np.array(Correlation, ndmin=2)
        n_dist = len(M)

        #  check if all distributions have finite moments
        for i in range(n_dist):
            if not (
                np.isfinite(self.Marginals[i].mean())
                and np.isfinite(self.Marginals[i].std())
            ):
                raise RuntimeError(  # noqa: DOC501, TRY003
                    'The marginal distributions need to have '  # noqa: EM101
                    'finite mean and variance'
                )

        # Check if input for correlation matrix fulfills requirements
        try:
            np.linalg.cholesky(self.Rho_X)
        except np.linalg.LinAlgError:
            raise RuntimeError(  # noqa: B904, DOC501, TRY003
                'The given correlation matrix is not positive definite'  # noqa: EM101
                '--> Nataf transformation is not applicable.'
            )
        if not np.all(self.Rho_X - self.Rho_X.T == 0):
            raise RuntimeError(  # noqa: DOC501, TRY003
                'The given correlation matrix is not symmetric '  # noqa: EM101
                '--> Nataf transformation is not applicable.'
            )
        if not np.all(np.diag(self.Rho_X) == 1):
            raise RuntimeError(  # noqa: DOC501, TRY003
                'Not all diagonal entries of the given correlation matrix are equal to one '  # noqa: EM101
                '--> Nataf transformation is not applicable.'
            )

        """
        Calculation of the transformed correlation matrix. This is achieved
        by a quadratic two-dimensional Gauss-Legendre integration
        """

        n = 1024
        zmax = 8
        zmin = -zmax
        points, weights = np.polynomial.legendre.leggauss(n)
        points = -(0.5 * (points + 1) * (zmax - zmin) + zmin)
        weights = weights * (0.5 * (zmax - zmin))  # noqa: PLR6104

        xi = np.tile(points, [n, 1])
        xi = xi.flatten(order='F')
        eta = np.tile(points, n)

        first = np.tile(weights, n)
        first = np.reshape(first, [n, n])
        second = np.transpose(first)

        weights2d = first * second
        w2d = weights2d.flatten()

        #  check is X the identity
        self.Rho_Z = np.identity(n=n_dist)
        if np.linalg.norm(self.Rho_X - np.identity(n=n_dist)) > 10 ** (-5):  # noqa: PLR1702
            for i in range(n_dist):
                for j in range(i + 1, n_dist):
                    if self.Rho_X[i, j] == 0:
                        continue

                    elif (  # noqa: RET507
                        (
                            (self.Marginals[i].Name == 'standardnormal')
                            and (self.Marginals[j].Name == 'standardnormal')
                        )
                        or (
                            (self.Marginals[i].Name == 'normal')
                            and (self.Marginals[j].Name == 'normal')
                        )
                    ):
                        self.Rho_Z[i, j] = self.Rho_X[i, j]
                        self.Rho_Z[j, i] = self.Rho_X[j, i]
                        continue

                    elif (self.Marginals[i].Name == 'normal') and (
                        self.Marginals[j].Name == 'lognormal'
                    ):
                        Vj = self.Marginals[j].std() / self.Marginals[j].mean()  # noqa: N806
                        self.Rho_Z[i, j] = (
                            self.Rho_X[i, j] * Vj / np.sqrt(np.log(1 + Vj**2))
                        )
                        self.Rho_Z[j, i] = self.Rho_Z[i, j]
                        continue

                    elif (self.Marginals[i].Name == 'lognormal') and (
                        self.Marginals[j].Name == 'normal'
                    ):
                        Vi = self.Marginals[i].std() / self.Marginals[i].mean()  # noqa: N806
                        self.Rho_Z[i, j] = (
                            self.Rho_X[i, j] * Vi / np.sqrt(np.log(1 + Vi**2))
                        )
                        self.Rho_Z[j, i] = self.Rho_Z[i, j]
                        continue

                    elif (self.Marginals[i].Name == 'lognormal') and (
                        self.Marginals[j].Name == 'lognormal'
                    ):
                        Vi = self.Marginals[i].std() / self.Marginals[i].mean()  # noqa: N806
                        Vj = self.Marginals[j].std() / self.Marginals[j].mean()  # noqa: N806
                        self.Rho_Z[i, j] = np.log(
                            1 + self.Rho_X[i, j] * Vi * Vj
                        ) / np.sqrt(np.log(1 + Vi**2) * np.log(1 + Vj**2))
                        self.Rho_Z[j, i] = self.Rho_Z[i, j]
                        continue

                    #  solving Nataf
                    tmp_f_xi = (
                        self.Marginals[j].icdf(stats.norm.cdf(eta))
                        - self.Marginals[j].mean()
                    ) / self.Marginals[j].std()
                    tmp_f_eta = (
                        self.Marginals[i].icdf(stats.norm.cdf(xi))
                        - self.Marginals[i].mean()
                    ) / self.Marginals[i].std()
                    coef = tmp_f_xi * tmp_f_eta * w2d

                    def fun(rho0):  # noqa: ANN001, ANN202
                        return (
                            coef * self.bivariateNormalPdf(xi, eta, rho0)  # noqa: B023
                        ).sum() - self.Rho_X[i, j]  # noqa: B023

                    x0, r = optimize.brentq(
                        f=fun,
                        a=-1 + np.finfo(float).eps,
                        b=1 - np.finfo(float).eps,
                        full_output=True,
                    )
                    if r.converged == 1:
                        self.Rho_Z[i, j] = x0
                        self.Rho_Z[j, i] = self.Rho_Z[i, j]
                    else:
                        sol = optimize.fsolve(
                            func=fun, x0=self.Rho_X[i, j], full_output=True
                        )
                        if sol[2] == 1:
                            self.Rho_Z[i, j] = sol[0]
                            self.Rho_Z[j, i] = self.Rho_Z[i, j]
                        else:
                            sol = optimize.fsolve(
                                func=fun, x0=-self.Rho_X[i, j], full_output=True
                            )
                            if sol[2] == 1:
                                self.Rho_Z[i, j] = sol[0]
                                self.Rho_Z[j, i] = self.Rho_Z[i, j]
                            else:
                                for i in range(10):  # noqa: B007, PLW2901
                                    init = 2 * np.random.rand() - 1
                                    sol = optimize.fsolve(
                                        func=fun, x0=init, full_output=True
                                    )
                                    if sol[2] == 1:
                                        break
                                if sol[2] == 1:
                                    self.Rho_Z[i, j] = sol[0]
                                    self.Rho_Z[j, i] = self.Rho_Z[i, j]
                                else:
                                    raise RuntimeError(  # noqa: DOC501, TRY003
                                        'brentq and fsolve coul'  # noqa: EM101
                                        'd not converge to a '
                                        'solution of the Nataf '
                                        'integral equation'
                                    )
        try:
            self.A = np.linalg.cholesky(self.Rho_Z)
        except np.linalg.LinAlgError:
            raise RuntimeError(  # noqa: B904, DOC501, TRY003
                'Transformed correlation matrix is not positive'  # noqa: EM101
                ' definite --> Nataf transformation is not '
                'applicable.'
            )

    # %%
    """
    This function performs the transformation from X to U by taking
    the inverse standard normal cdf of the cdf of every value. Then it
    performs the transformation from Z to U. A is the lower triangular
    matrix of the cholesky decomposition of Rho_Z and U is the resulting
    independent standard normal vector. Afterwards it calculates the
    Jacobian of this Transformation if it is needed.
    """

    def X2U(self, X, Jacobian=False):  # noqa: ANN001, ANN201, FBT002, N802, N803
        """Carries out the transformation from physical space X to
        standard normal space U.
        X must be a [n,d]-shaped array (n = number of data points,
        d = dimensions).
        The Jacobian of the transformation of the first given data
        point is only given as an output in case that the input
        argument Jacobian=True .
        """  # noqa: D205
        n_dim = len(self.Marginals)
        X = np.array(X, ndmin=2)  # noqa: N806

        # check if all marginal distributions are continuous
        for i in range(n_dim):
            if self.Marginals[i].Name in [  # noqa: PLR6201
                'binomial',
                'geometric',
                'negativebinomial',
                'poisson',
            ]:
                raise RuntimeError(  # noqa: DOC501, TRY003
                    'At least one of the marginal distributions is a discrete distribution,'  # noqa: EM101
                    'the transformation X2U is therefore not possible.'
                )

        # check of the dimensions of input X
        if X.ndim > 2:  # noqa: PLR2004
            raise RuntimeError('X must have not more than two dimensions. ')  # noqa: DOC501, EM101, TRY003
        if np.shape(X)[1] == 1 and n_dim != 1:
            # in case that only one point X is given, he can be defined either as row or column vector
            X = X.T  # noqa: N806
        if np.shape(X)[1] != n_dim:
            raise RuntimeError(  # noqa: DOC501, TRY003
                'X must be an array of size [n,d], where d is the'  # noqa: EM101
                ' number of dimensions of the joint distribution.'
            )

        Z = np.zeros(np.flip(X.shape))  # noqa: N806
        for i in range(n_dim):
            Z[i, :] = stats.norm.ppf(self.Marginals[i].cdf(X[:, i]))
        U = np.linalg.solve(self.A, Z.squeeze()).T  # noqa: N806

        if Jacobian:
            diag = np.zeros([n_dim, n_dim])
            for i in range(n_dim):
                diag[i, i] = self.Marginals[i].pdf(X[0, i]) / stats.norm.pdf(Z[i, 0])
            Jac = np.linalg.solve(self.A, diag)  # noqa: N806
            return np.squeeze(U), Jac
        else:  # noqa: RET505
            return np.squeeze(U)

    # %%
    def U2X(self, U, Jacobian=False):  # noqa: ANN001, ANN201, FBT002, N802, N803
        """Carries out the transformation from standard normal space U
        to physical space X.
        U must be a [n,d]-shaped array (n = number of data points,
        d = dimensions).
        The Jacobian of the transformation of the first given data
        point is only given as an output in case that the input
        argument Jacobian=True .
        """  # noqa: D205
        n_dim = len(self.Marginals)
        U = np.array(U, ndmin=2)  # noqa: N806

        # check of the dimensions of input U
        if U.ndim > 2:  # noqa: PLR2004
            raise RuntimeError('U must have not more than two dimensions. ')  # noqa: DOC501, EM101, TRY003
        if np.shape(U)[1] == 1 and n_dim != 1:
            # in case that only one point U is given, he can be defined either as row or column vector
            U = U.T  # noqa: N806
        if np.shape(U)[1] != n_dim:
            raise RuntimeError(  # noqa: DOC501, TRY003
                'U must be an array of size [n,d], where d is the'  # noqa: EM101
                ' number of dimensions of the joint distribution.'
            )
        else:  # noqa: RET506
            U = U.T  # noqa: N806
        Z = self.A @ U  # noqa: N806

        X = np.zeros(np.flip(U.shape))  # noqa: N806
        for i in range(n_dim):
            X[:, i] = self.Marginals[i].icdf(stats.norm.cdf(Z[i, :]))

        if Jacobian:
            diag = np.zeros([n_dim, n_dim])
            for i in range(n_dim):
                diag[i, i] = stats.norm.pdf(Z[i, 0]) / self.Marginals[i].pdf(X[0, i])
            Jac = np.dot(diag, self.A)  # noqa: N806
            return np.squeeze(X), Jac
        else:  # noqa: RET505
            return np.squeeze(X)

    # %%
    def random(self, n=1):  # noqa: ANN001, ANN201
        """Creates n samples of the joint distribution.
        Every row in the output array corresponds to one sample.
        """  # noqa: D205, D401
        n = int(n)
        n_dim = np.size(self.Marginals)
        U = np.random.randn(n_dim, n)  # noqa: N806
        Z = np.dot(self.A, U)  # noqa: N806
        jr = np.zeros([n, n_dim])
        for i in range(n_dim):
            jr[:, i] = self.Marginals[i].icdf(stats.norm.cdf(Z[i, :]))

        return np.squeeze(jr)

    # %%
    def pdf(self, X):  # noqa: ANN001, ANN201, C901, N803
        """Computes the joint PDF.
        X must be a [n,d]-shaped array (n = number of data points,
        d = dimensions).
        """  # noqa: D205, D401
        n_dim = len(self.Marginals)
        X = np.array(X, ndmin=2)  # noqa: N806

        # check if all marginal distributions are continuous
        for i in range(n_dim):
            if self.Marginals[i].Name in [  # noqa: PLR6201
                'binomial',
                'geometric',
                'negativebinomial',
                'poisson',
            ]:
                raise RuntimeError(  # noqa: DOC501, TRY003
                    'At least one of the marginal distributions is a discrete distribution,'  # noqa: EM101
                    'the transformation X2U is therefore not possible.'
                )

        # check of the dimensions of input X
        if X.ndim > 2:  # noqa: PLR2004
            raise RuntimeError('X must have not more than two dimensions.')  # noqa: DOC501, EM101, TRY003
        if np.shape(X)[1] == 1 and n_dim != 1:
            # in case that only one point X is given, he can be defined either as row or column vector
            X = X.T  # noqa: N806
        if np.shape(X)[1] != n_dim:
            raise RuntimeError(  # noqa: DOC501, TRY003
                'X must be an array of size [n,d], where d is the'  # noqa: EM101
                ' number of dimensions of the joint distribution.'
            )

        n_X = np.shape(X)[0]  # noqa: N806
        U = np.zeros([n_X, n_dim])  # noqa: N806
        phi = np.zeros([n_dim, n_X])
        f = np.zeros([n_dim, n_X])
        mu = np.zeros(n_dim)
        for i in range(n_dim):
            U[:, i] = stats.norm.ppf(self.Marginals[i].cdf(X[:, i]))
            phi[i, :] = stats.norm.pdf(U[:, i])
            f[i, :] = self.Marginals[i].pdf(X[:, i])
        phi_n = stats.multivariate_normal.pdf(U, mu, self.Rho_Z)
        jointpdf = np.zeros(n_X)
        for i in range(n_X):
            try:
                jointpdf[i] = (
                    np.prod(f[:, i]) / (np.prod(phi[:, i]) + realmin)
                ) * phi_n[i]
            except IndexError:  # noqa: PERF203
                # In case of n=1, phi_n is a scalar.
                jointpdf[i] = (
                    np.prod(f[:, i]) / (np.prod(phi[:, i]) + realmin)
                ) * phi_n
            except ZeroDivisionError:
                jointpdf[i] = 0

        if np.size(jointpdf) == 1:
            return jointpdf[0]
        else:  # noqa: RET505
            return jointpdf

    # %%
    def cdf(self, X):  # noqa: ANN001, ANN201, N803
        """Computes the joint CDF.
        X must be a [n,d]-shaped array (n = number of data points,
        d = dimensions).
        The CDF computation is based on the multivariate normal cdf.
        In scipy the multivariate normal cdf is computed by Monte Carlo
        sampling, the output of this method is therefore also a
        stochastic quantity.
        """  # noqa: D205, D401
        n_dim = len(self.Marginals)
        X = np.array(X, ndmin=2)  # noqa: N806

        # check of the dimensions of input X
        if X.ndim > 2:  # noqa: PLR2004
            raise RuntimeError('X must have not more than two dimensions. ')  # noqa: DOC501, EM101, TRY003
        if np.shape(X)[1] == 1 and n_dim != 1:
            # in case that only one point X is given, he can be defined either as row or column vector
            X = X.T  # noqa: N806
        if np.shape(X)[1] != n_dim:
            raise RuntimeError(  # noqa: DOC501, TRY003
                'X must be an array of size [n,d], where d is the'  # noqa: EM101
                ' number of dimensions of the joint distribution.'
            )
        n_X = np.shape(X)[0]  # noqa: N806
        U = np.zeros([n_X, n_dim])  # noqa: N806
        for i in range(n_dim):
            U[:, i] = stats.norm.ppf(self.Marginals[i].cdf(X[:, i]))
        mu = np.zeros(n_dim)
        jointcdf = stats.multivariate_normal.cdf(
            U, mean=mu, cov=np.matrix(self.Rho_Z)
        )

        return jointcdf  # noqa: RET504

    # %%
    @staticmethod
    def bivariateNormalPdf(x1, x2, rho):  # noqa: ANN001, ANN205, N802, D102
        return (
            1
            / (2 * np.pi * np.sqrt(1 - rho**2))
            * np.exp(-1 / (2 * (1 - rho**2)) * (x1**2 - 2 * rho * x1 * x2 + x2**2))
        )
