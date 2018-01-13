"""Some of the tests using CUDNN requires a special GPU instruction called dp4a which exists
only on P4 graphics cards for low bit inner products."""
import mxnet as mx
import numpy as np
from mxnet.test_utils import *

ctx = mx.gpu(0)
dtype = np.int8
dtype_ = np.float32
n = 4


# def test_quantized_lrn():
#     n = 5
#     x_ = np.random.uniform(low=-100, high=100, size=(1,1,n,n))
#     x = nd.array(x_, ctx=ctx, dtype=dtype)
#     y = nd.quantized_lrn(x, nsize=3)
#
#
# def test_quantized_conv2d():
#     x_ = np.random.uniform(low=-100, high=100, size=(4, 5, 5, 4))
#     k_ = np.random.uniform(low=-100, high=100, size=(4, 3, 3, 4))
#     x = nd.array(x_, ctx=ctx, dtype=dtype)
#     k = nd.array(k_, ctx=ctx, dtype=dtype)
#     min0x = nd.array([-1.0], ctx=ctx, dtype=np.float32)
#     max0x = nd.array([1.0], ctx=ctx, dtype=np.float32)
#     min0k = nd.array([-1.0], ctx=ctx, dtype=np.float32)
#     max0k = nd.array([1.0], ctx=ctx, dtype=np.float32)
#     y, min1, max1 = nd.quantized_conv2d(x, k, min0x, max0x, min0k, max0k,
#             stride=[1, 1], pad=[1, 1])
#     y_ = y.asnumpy().astype(np.int32)
#
#
# def test_quantized_relu():
#     a_ = np.random.uniform(low=-100, high=100, size=(n,n))
#     a = nd.array(a_, ctx=ctx, dtype=dtype)
#     min0 = nd.array([-1.0], ctx=ctx, dtype=np.float32)
#     max0 = nd.array([1.0], ctx=ctx, dtype=np.float32)
#     b, min1, max1 = nd.quantized_relu(a, min0, max0)
#
#
# def test_quantized_max_pool():
#     a_ = np.random.uniform(low=-128, high=127, size=(1, 1, n, n))
#     a = nd.array(a_, ctx=ctx, dtype=dtype)
#     min0 = nd.array([-1.0], ctx=ctx, dtype=np.float32)
#     max0 = nd.array([1.0], ctx=ctx, dtype=np.float32)
#     b, min1, max1 = nd.quantized_max_pool(a, min0, max0, kernel=[2, 2])
#
#
# def test_quantized_matmul():
#     m = 1
#     n = 2
#     k = 3
#     a_ = np.random.uniform(low=-100, high=100, size=(m,n))
#     a = nd.array(a_, ctx=ctx, dtype=dtype)
#     b_ = np.random.uniform(low=-100, high=100, size=(n,k))
#     b = nd.array(b_, ctx=ctx, dtype=dtype)
#     min0a = nd.array([-1.0], ctx=ctx, dtype=np.float32)
#     max0a = nd.array([1.0], ctx=ctx, dtype=np.float32)
#     min0b = nd.array([-1.0], ctx=ctx, dtype=np.float32)
#     max0b = nd.array([1.0], ctx=ctx, dtype=np.float32)
#     c, min1, max1 = nd.quantized_matmul(a, b, min0a, max0a, min0b, max0b)
#
#
# def test_matmul():
#     m = 3
#     n = 2
#     k = 4
#
#     A = mx.sym.Variable('A')
#     B = mx.sym.Variable('B')
#     C = mx.sym.matmul(A, B, name='C')
#     # (m, n) * (n, k) = (m, k) [C = A * B]
#
#     a  = nd.uniform(low=-1.0, high=1.0, shape=(m, n), ctx=ctx, dtype=dtype_)
#     b  = nd.uniform(low=-1.0, high=1.0, shape=(n, k), ctx=ctx, dtype=dtype_)
#     dc = nd.uniform(low=-1.0, high=1.0, shape=(m, k), ctx=ctx, dtype=dtype_)
#     da = nd.zeros(shape=(m, n), ctx=ctx, dtype=dtype_)
#     db = nd.zeros(shape=(n, k), ctx=ctx, dtype=dtype_)
#     executor = C.bind(ctx, {'A': a, 'B': b}, {'A': da, 'B': db})
#     out = executor.forward(is_train=True)
#     executor.backward(out_grads=dc)
#     # (m, n) = (m, k) * (k, n) [dA = dC * B.T]
#     da_ = np.dot(dc.asnumpy(), b.asnumpy().T)
#     # (n, k) = (n, m) * (m, k) [dB = A.T * dC]
#     db_ = np.dot(a.asnumpy().T, dc.asnumpy())
#     # assert(da_, da)
#     # assert(db_, db)


def test_quantize_float32_to_int8():
    shape = rand_shape_nd(4)
    data = rand_ndarray(shape, 'default', dtype='float32')
    min_range = mx.nd.min(data)
    max_range = mx.nd.max(data)
    qdata, min_val, max_val = mx.nd.contrib.quantize(data, min_range, max_range, out_type='int8')
    data_np = data.asnumpy()
    min_range = min_range.asscalar()
    max_range = max_range.asscalar()
    real_range = np.maximum(np.abs(min_range), np.abs(max_range))
    quantized_range = 127.0
    scale = quantized_range / real_range
    assert qdata.dtype == np.int8
    assert min_val.dtype == np.float32
    assert max_val.dtype == np.float32
    assert same(min_val.asscalar(), -real_range)
    assert same(max_val.asscalar(), real_range)
    qdata_np = (np.sign(data_np) * np.minimum(np.abs(data_np) * scale + 0.5, quantized_range)).astype(np.int8)
    assert same(qdata.asnumpy(), qdata_np)


def test_dequantize_int8_to_float32():
    shape = rand_shape_nd(4)
    qdata_np = np.random.uniform(low=-127, high=127, size=shape).astype(dtype=np.int8)
    qdata = mx.nd.array(qdata_np, dtype=np.int8)
    real_range = 402.3347
    min_range = mx.nd.array([-real_range], dtype=np.float32)
    max_range = mx.nd.array([real_range], dtype=np.float32)
    data = mx.nd.contrib.dequantize(qdata, min_range, max_range, out_type='float32')
    quantized_range = 127.0
    scale = real_range / quantized_range
    assert data.dtype == np.float32
    data_np = qdata_np * scale
    assert_almost_equal(data.asnumpy(), data_np)


def test_quantized_conv():
    if mx.current_context().device_type != 'gpu':
        return

    def check_quantized_conv(data_shape, kernel, num_filter, pad, stride, no_bias):
        with mx.Context('gpu', 0):
            # run fp32 conv
            data = mx.sym.Variable(name='data', shape=data_shape, dtype='float32')
            conv2d = mx.sym.Convolution(data=data, kernel=kernel, num_filter=num_filter, pad=pad, stride=stride,
                                        no_bias=no_bias, cudnn_off=False, name='conv2d')
            arg_shapes, _, _ = conv2d.infer_shape(data=data_shape)
            arg_names = conv2d.list_arguments()
            conv_exe_fp32 = conv2d.simple_bind(ctx=mx.current_context(), grad_req='null')
            conv_exe_fp32.arg_dict[arg_names[0]][:] = mx.nd.random.uniform(low=-127.0, high=127.0,
                                                                           shape=data_shape).astype('int32')
            conv_exe_fp32.arg_dict[arg_names[1]][:] = mx.nd.random.uniform(low=-127.0, high=127.0,
                                                                           shape=arg_shapes[1]).astype('int32')
            if not no_bias:
                conv_exe_fp32.arg_dict[arg_names[2]][:] = mx.nd.random.uniform(low=-127.0, high=127.0,
                                                                               shape=arg_shapes[2]).astype('int32')
            output = conv_exe_fp32.forward()[0]

            # run quantized conv
            qdata = mx.sym.Variable(name='qdata', shape=data_shape, dtype='int8')
            qweight = mx.sym.Variable(name='qweight')
            min_data = mx.sym.Variable(name='min_data')
            max_data = mx.sym.Variable(name='max_data')
            min_weight = mx.sym.Variable(name='min_weight')
            max_weight = mx.sym.Variable(name='max_weight')
            quantized_conv2d = mx.sym.contrib.quantized_conv(data=qdata, weight=qweight, min_data=min_data,
                                                             max_data=max_data, min_weight=min_weight,
                                                             max_weight=max_weight, kernel=kernel,
                                                             num_filter=num_filter, pad=pad, stride=stride,
                                                             no_bias=no_bias)
            conv_exe_int8 = quantized_conv2d.simple_bind(ctx=mx.current_context(), grad_req='null')
            qarg_names = quantized_conv2d.list_arguments()
            conv_exe_int8.arg_dict[qarg_names[0]][:] = conv_exe_fp32.arg_dict[arg_names[0]].astype('int8')
            conv_exe_int8.arg_dict[qarg_names[1]][:] = conv_exe_fp32.arg_dict[arg_names[1]].astype('int8')
            quantized_range = 127.0
            if no_bias:
                conv_exe_int8.arg_dict[qarg_names[2]][:] = -quantized_range
                conv_exe_int8.arg_dict[qarg_names[3]][:] = quantized_range
                conv_exe_int8.arg_dict[qarg_names[4]][:] = -quantized_range
                conv_exe_int8.arg_dict[qarg_names[5]][:] = quantized_range
            else:
                conv_exe_int8.arg_dict[qarg_names[2]][:] = conv_exe_fp32.arg_dict[arg_names[2]].astype('int8')
                conv_exe_int8.arg_dict[qarg_names[3]][:] = -quantized_range
                conv_exe_int8.arg_dict[qarg_names[4]][:] = quantized_range
                conv_exe_int8.arg_dict[qarg_names[5]][:] = -quantized_range
                conv_exe_int8.arg_dict[qarg_names[6]][:] = quantized_range
                conv_exe_int8.arg_dict[qarg_names[7]][:] = -quantized_range
                conv_exe_int8.arg_dict[qarg_names[8]][:] = quantized_range
            qoutput, min_range, max_range = conv_exe_int8.forward()

            if no_bias:
                assert_almost_equal(output.asnumpy(), qoutput.asnumpy())
            else:
                # with adding bias, accuracy loss should not be greater than one
                diff = mx.nd.abs(output - qoutput.astype(output.dtype))
                cond = mx.nd.lesser(2, diff).sum().asscalar()
                assert cond == 0

    check_quantized_conv((3, 4, 28, 28), (3, 3), 128, (1, 1), (1, 1), True)
    check_quantized_conv((3, 4, 28, 28), (3, 3), 128, (1, 1), (1, 1), False)


def test_quantized_pooling():
    if mx.current_context().device_type != 'gpu':
        return

    def check_quantized_pooling(data_shape, kernel, pool_type, pad, stride, global_pool):
        with mx.Context('gpu', 0):
            data = mx.sym.Variable(name='data', shape=data_shape, dtype='float32')
            pooling_fp32 = mx.sym.Pooling(data=data, kernel=kernel, pad=pad, stride=stride,
                                          pool_type=pool_type, global_pool=global_pool, cudnn_off=False)
            arg_shapes, _, _ = pooling_fp32.infer_shape(data=data_shape)
            arg_names = pooling_fp32.list_arguments()
            pooling_fp32_exe = pooling_fp32.simple_bind(ctx=mx.current_context(), grad_req='null')
            pooling_fp32_exe.arg_dict[arg_names[0]][:] = mx.nd.random.uniform(low=-127.0, high=127.0,
                                                                              shape=data_shape).astype('int32')
            output = pooling_fp32_exe.forward()[0]

            qdata = mx.sym.Variable(name='qdata', shape=data_shape, dtype='int8')
            min_data = mx.sym.Variable(name='min_data')
            max_data = mx.sym.Variable(name='max_data')
            quantized_pooling = mx.sym.contrib.quantized_pooling(data=qdata, min_data=min_data,
                                                                 max_data=max_data, kernel=kernel,
                                                                 pad=pad, stride=stride, pool_type=pool_type,
                                                                 global_pool=global_pool)
            pooling_int8_exe = quantized_pooling.simple_bind(ctx=mx.current_context(), grad_req='null')
            qarg_names = quantized_pooling.list_arguments()
            pooling_int8_exe.arg_dict[qarg_names[0]][:] = pooling_fp32_exe.arg_dict[arg_names[0]].astype('int8')
            quantized_range = 127.0
            pooling_int8_exe.arg_dict[qarg_names[1]][:] = -quantized_range
            pooling_int8_exe.arg_dict[qarg_names[2]][:] = quantized_range
            qoutput, min_range, max_range = pooling_int8_exe.forward()

            if pool_type == 'max':
                assert_almost_equal(output.asnumpy(), qoutput.asnumpy())
            elif pool_type == 'avg':  # for avg pooling, fp32 and int8 may be different due to rounding errors
                diff = mx.nd.abs(output - qoutput.astype(output.dtype))
                cond = mx.nd.lesser(2, diff).sum().asscalar()
                assert cond == 0

    check_quantized_pooling((3, 4, 56, 56), (3, 3), 'max', (0, 0), (2, 2), False)
    check_quantized_pooling((3, 4, 56, 56), (3, 3), 'max', (0, 0), (2, 2), True)
    check_quantized_pooling((3, 512, 7, 7), (7, 7), 'avg', (0, 0), (1, 1), False)
    check_quantized_pooling((3, 512, 7, 7), (7, 7), 'avg', (0, 0), (1, 1), True)


def test_quantized_fc():
    if mx.current_context().device_type != 'gpu':
        return

    def check_quantized_fc(data_shape, num_hidden, no_bias, flatten=True):
        with mx.Context('gpu', 0):
            data = mx.sym.Variable(name='data', shape=data_shape, dtype='float32')
            fc_fp32 = mx.sym.FullyConnected(data=data, num_hidden=num_hidden, no_bias=no_bias, flatten=flatten)
            arg_shapes, _, _ = fc_fp32.infer_shape(data=data_shape)
            arg_names = fc_fp32.list_arguments()
            fc_fp32_exe = fc_fp32.simple_bind(ctx=mx.current_context(), grad_req='null')
            fc_fp32_exe.arg_dict[arg_names[0]][:] = mx.nd.random.uniform(low=-127.0, high=127.0,
                                                                         shape=data_shape).astype('int32')
            fc_fp32_exe.arg_dict[arg_names[1]][:] = mx.nd.random.uniform(low=-127.0, high=127.0,
                                                                         shape=arg_shapes[1]).astype('int32')
            if not no_bias:
                fc_fp32_exe.arg_dict[arg_names[2]][:] = mx.nd.random.uniform(low=-127.0, high=127.0,
                                                                             shape=arg_shapes[2]).astype('int32')
            output = fc_fp32_exe.forward()[0]

            qdata = mx.sym.Variable(name='qdata', shape=data_shape, dtype='int8')
            fc_int8 = mx.sym.contrib.quantized_fully_connected(data=qdata, num_hidden=num_hidden,
                                                               no_bias=no_bias, flatten=flatten)
            fc_int8_exe = fc_int8.simple_bind(ctx=mx.current_context(), grad_req='null')
            qarg_names = fc_int8.list_arguments()
            fc_int8_exe.arg_dict[qarg_names[0]][:] = fc_fp32_exe.arg_dict[arg_names[0]].astype('int8')
            fc_int8_exe.arg_dict[qarg_names[1]][:] = fc_fp32_exe.arg_dict[arg_names[1]].astype('int8')
            quantized_range = 127.0
            if no_bias:
                fc_int8_exe.arg_dict[qarg_names[2]][:] = -quantized_range
                fc_int8_exe.arg_dict[qarg_names[3]][:] = quantized_range
                fc_int8_exe.arg_dict[qarg_names[4]][:] = -quantized_range
                fc_int8_exe.arg_dict[qarg_names[5]][:] = quantized_range
            else:
                fc_int8_exe.arg_dict[qarg_names[2]][:] = fc_fp32_exe.arg_dict[arg_names[2]].astype('int8')
                fc_int8_exe.arg_dict[qarg_names[3]][:] = -quantized_range
                fc_int8_exe.arg_dict[qarg_names[4]][:] = quantized_range
                fc_int8_exe.arg_dict[qarg_names[5]][:] = -quantized_range
                fc_int8_exe.arg_dict[qarg_names[6]][:] = quantized_range
                fc_int8_exe.arg_dict[qarg_names[7]][:] = -quantized_range
                fc_int8_exe.arg_dict[qarg_names[8]][:] = quantized_range
            qoutput, min_range, max_range = fc_int8_exe.forward()

            if no_bias:
                assert_almost_equal(output.asnumpy(), qoutput.asnumpy())
            else:
                # with adding bias, accuracy loss should not be greater than one
                diff = mx.nd.abs(output - qoutput.astype(output.dtype))
                cond = mx.nd.lesser(2, diff).sum().asscalar()
                assert cond == 0

    check_quantized_fc((32, 512, 2, 2), 100, True)
    check_quantized_fc((32, 111, 2, 2), 100, True)
    check_quantized_fc((32, 512, 2, 2), 100, False)
    check_quantized_fc((32, 111, 2, 2), 100, False)


def test_quantized_flatten():
    def check_quantized_flatten(shape):
        qdata = mx.nd.random.uniform(low=-127, high=127, shape=shape).astype('int8')
        min_data = mx.nd.array([-1023.343], dtype='float32')
        max_data = mx.nd.array([2343.324275], dtype='float32')
        qoutput, min_output, max_output = mx.nd.contrib.quantized_flatten(qdata, min_data, max_data)
        assert qoutput.ndim == 2
        assert qoutput.shape[0] == qdata.shape[0]
        assert qoutput.shape[1] == np.prod(qdata.shape[1:])
        assert same(qdata.asnumpy().flatten(), qoutput.asnumpy().flatten())
        assert same(min_data.asnumpy(), min_output.asnumpy())
        assert same(max_data.asnumpy(), max_output.asnumpy())

    check_quantized_flatten((10,))
    check_quantized_flatten((10, 15))
    check_quantized_flatten((10, 15, 18))
    check_quantized_flatten((3, 4, 23, 23))


def test_calibrate_quantized_sym():
    data = mx.sym.Variable('data')
    conv = mx.sym.Convolution(data=data, num_filter=1, kernel=(1, 1), no_bias=True)
    qnet = mx.quantization._quantize_symbol(conv)
    requantize_op_name = 'requantize_convolution0'
    th_dict = {'convolution0_output': (-11.3902, 20.3902304)}
    cqnet = mx.quantization._calibrate_quantized_sym(qnet, th_dict)
    attr_dict = cqnet.attr_dict()
    assert requantize_op_name in attr_dict
    lhs = float(attr_dict[requantize_op_name]['min_calib_range'])
    rhs = th_dict['convolution0_output'][0]
    assert (lhs - rhs) < 0.0001
    lhs = float(attr_dict[requantize_op_name]['max_calib_range'])
    rhs = th_dict['convolution0_output'][1]
    assert (lhs - rhs) < 0.0001


if __name__ == "__main__":
    set_default_context(mx.gpu(0))
    # test_quantized_conv()
    # test_quantized_pooling()
    test_quantized_fc()
    test_quantized_flatten()
    # import nose
    # nose.runmodule()
