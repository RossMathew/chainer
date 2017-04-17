import unittest

import numpy

import chainer
from chainer import cuda
from chainer.functions import vae
from chainer import testing
from chainer.testing import attr
from chainer.testing import condition


@testing.parameterize(
    {'reduce': 'no'},
    {'reduce': 'sum'}
)
class TestGaussianKLDivergence(unittest.TestCase):

    def setUp(self):
        self.mean = numpy.random.uniform(-1, 1, (3,)).astype(numpy.float32)
        self.ln_var = numpy.random.uniform(-1, 1, (3,)).astype(numpy.float32)

        # Refer to Appendix B in the original paper
        # Auto-Encoding Variational Bayes (https://arxiv.org/abs/1312.6114)
        loss = -(1 + self.ln_var -
                 self.mean * self.mean -
                 numpy.exp(self.ln_var)) * 0.5
        if self.reduce == 'sum':
            self.expect = numpy.sum(loss)
        elif self.reduce == 'no':
            self.expect = loss

    def check_gaussian_kl_divergence(self, mean, ln_var):
        m = chainer.Variable(mean)
        v = chainer.Variable(ln_var)
        actual = vae.gaussian_kl_divergence(m, v, self.reduce)
        actual = cuda.to_cpu(actual.data)
        testing.assert_allclose(self.expect, actual)

    @condition.retry(3)
    def test_gaussian_kl_divergence_cpu(self):
        self.check_gaussian_kl_divergence(self.mean, self.ln_var)

    @attr.gpu
    @condition.retry(3)
    def test_gaussian_kl_divergence_gpu(self):
        self.check_gaussian_kl_divergence(cuda.to_gpu(self.mean),
                                          cuda.to_gpu(self.ln_var))


class TestGaussianNLLInvalidReductionOption(unittest.TestCase):

    def setUp(self):
        self.mean = numpy.random.uniform(-1, 1, (3,)).astype(numpy.float32)
        self.ln_var = numpy.random.uniform(-1, 1, (3,)).astype(numpy.float32)

    def check_invalid_option(self, xp):
        m = chainer.Variable(xp.asarray(self.mean))
        v = chainer.Variable(xp.asarray(self.ln_var))
        with self.assertRaises(ValueError):
            F.gaussian_kl_divergence(m, v, 'invalid_option')

    def test_invalid_option_cpu(self):
        self.check_invalid_option(numpy)

    @attr.gpu
    def test_invalid_option_gpu(self):
        self.check_invalid_option(cuda.cupy)


class TestBernoulliNLL(unittest.TestCase):

    def setUp(self):
        self.x = numpy.random.uniform(-1, 1, (3,)).astype(numpy.float32)
        self.y = numpy.random.uniform(-1, 1, (3,)).astype(numpy.float32)

        # Refer to Appendix C.1 in the original paper
        # Auto-Encoding Variational Bayes (https://arxiv.org/abs/1312.6114)
        p = 1 / (1 + numpy.exp(-self.y))
        self.expect = - (numpy.sum(self.x * numpy.log(p)) +
                         numpy.sum((1 - self.x) * numpy.log(1 - p)))

    def check_bernoulli_nll(self, x_data, y_data):
        x = chainer.Variable(x_data)
        y = chainer.Variable(y_data)
        actual = cuda.to_cpu(vae.bernoulli_nll(x, y).data)
        testing.assert_allclose(self.expect, actual)

    @condition.retry(3)
    def test_bernoulli_nll_cpu(self):
        self.check_bernoulli_nll(self.x, self.y)

    @attr.gpu
    @condition.retry(3)
    def test_bernoulli_nll_gpu(self):
        self.check_bernoulli_nll(cuda.to_gpu(self.x),
                                 cuda.to_gpu(self.y))


class TestGaussianNLL(unittest.TestCase):

    def setUp(self):
        self.x = numpy.random.uniform(-1, 1, (3,)).astype(numpy.float32)
        self.mean = numpy.random.uniform(-1, 1, (3,)).astype(numpy.float32)
        self.ln_var = numpy.random.uniform(-1, 1, (3,)).astype(numpy.float32)

        # Refer to Appendix C.2 in the original paper
        # Auto-Encoding Variational Bayes (https://arxiv.org/abs/1312.6114)
        D = self.x.size
        x_d = self.x - self.mean
        var = numpy.exp(self.ln_var)

        self.expect = (0.5 * D * numpy.log(2 * numpy.pi) +
                       0.5 * numpy.sum(self.ln_var) +
                       numpy.sum(x_d * x_d / var) * 0.5)

    def check_gaussian_nll(self, x_data, mean_data, ln_var_data):
        x = chainer.Variable(x_data)
        mean = chainer.Variable(mean_data)
        ln_var = chainer.Variable(ln_var_data)
        actual = cuda.to_cpu(vae.gaussian_nll(x, mean, ln_var).data)
        testing.assert_allclose(self.expect, actual)

    @condition.retry(3)
    def test_gaussian_nll_cpu(self):
        self.check_gaussian_nll(self.x, self.mean, self.ln_var)

    @attr.gpu
    @condition.retry(3)
    def test_gaussian_nll_gpu(self):
        self.check_gaussian_nll(cuda.to_gpu(self.x),
                                cuda.to_gpu(self.mean),
                                cuda.to_gpu(self.ln_var))


testing.run_module(__name__, __file__)
