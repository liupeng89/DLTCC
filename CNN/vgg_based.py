# Based on the VGG-19 model
import sys
sys.path.append("/Users/liupeng/Documents/python/DeepLearning2TCC/DataSet")
import tensorflow as tf
import numpy as np

from functools import reduce
import input_data

IMAGE_WIDTH = 50
IMAGE_HEIGHT = 50


class Vgg19(object):
    # npy_path_dict  {"train":{"data":"", "target":""}, "test":{"data":"", "target":""}}
    def __init__(self, npy_path_dict=None, trainable=True, dropout=0.8):
        if npy_path_dict is not None:
            # load train data set and test data set
            self.data_dict = input_data.read_data_sets(npy_path_dict, validation_size=40)
        else:
            self.data_dict = None

        self.var_dict = {}
        self.trainable = trainable
        self.dropout = dropout

    # Build models
    def build(self, images, train_mode=None):
        """
        load variable from npy to build the VGG

        :param images:  images [batch, height, width, 3] values scaled [0, 1]
        :param train_mode: a bool tensor, usually a placeholder: if True, dropout will be turned on
        """
        images_reshape = tf.reshape(images, [-1, IMAGE_WIDTH, IMAGE_HEIGHT, 1])
        print("image_reshape:", images_reshape.shape)

        # conv 1
        with tf.name_scope("conv1"):
            self.conv1_1 = self.conv_layer(images_reshape, 1, 16, "conv1_1")
            self.conv1_2 = self.conv_layer(self.conv1_1, 16, 16, "conv1_2")
            self.pool1 = self.max_pool(self.conv1_2, "pool1")


        # conv 2
        with tf.name_scope("conv2"):
            self.conv2_1 = self.conv_layer(self.pool1, 16, 32, "conv2_1")
            self.conv2_2 = self.conv_layer(self.conv2_1, 32, 32, "conv2_2")
            self.pool2 = self.max_pool(self.conv2_2, "pool2")

        # conv 3
        with tf.name_scope("conv3"):
            self.conv3_1 = self.conv_layer(self.pool2, 32, 64, "conv3_1")
            self.conv3_2 = self.conv_layer(self.conv3_1, 64, 64, "conv3_2")
            self.conv3_3 = self.conv_layer(self.conv3_2, 64, 64, "conv3_3")
            self.conv3_4 = self.conv_layer(self.conv3_3, 64, 64, "conv3_4")
            self.pool3 = self.max_pool(self.conv3_4, "pool3")

        # conv 4
        with tf.name_scope("conv4"):
            self.conv4_1 = self.conv_layer(self.pool3, 64, 128, "conv4_1")
            self.conv4_2 = self.conv_layer(self.conv4_1, 128, 128, "conv4_2")
            self.conv4_3 = self.conv_layer(self.conv4_2, 128, 128, "conv4_3")
            self.conv4_4 = self.conv_layer(self.conv4_3, 128, 128, "conv4_4")
            self.pool4 = self.max_pool(self.conv4_4, "pool4")

        # conv 5
        with tf.name_scope("conv5"):
            self.conv5_1 = self.conv_layer(self.conv4_4, 128, 256, "conv5_1")
            self.conv5_2 = self.conv_layer(self.conv5_1, 256, 256, "conv5_2")
            self.conv5_3 = self.conv_layer(self.conv5_2, 256, 256, "conv5_3")
            self.conv5_4 = self.conv_layer(self.conv5_3, 256, 256, "conv5_4")
            self.pool5 = self.max_pool(self.conv5_4, "pool5")

        # fc 6
        with tf.name_scope("fc6"):
            self.fc6 = self.fc_layer(self.pool5, 54080, 4096, "fc6")
            self.relu6 = tf.nn.relu(self.fc6)
            if train_mode is not None:
                self.relu6 = tf.cond(train_mode, lambda: tf.nn.dropout(self.relu6, self.dropout), lambda: self.relu6)
            elif self.trainable:
                self.relu6 = tf.nn.dropout(self.relu6, self.dropout)

        # fc 7
        with tf.name_scope("fc7"):
            self.fc7 = self.fc_layer(self.relu6, 4096, 4096, "fc7")
            self.relu7 = tf.nn.relu(self.fc7)
            if train_mode is not None:
                self.relu7 = tf.cond(train_mode, lambda: tf.nn.dropout(self.relu7, self.dropout), lambda: self.relu7)
            elif self.trainable:
                self.relu7 = tf.nn.dropout(self.relu7, self.dropout)

        # fc 8
        with tf.name_scope("fc8"):
            self.fc8 = self.fc_layer(self.relu7, 4096, 2500, "fc8")

        # probability
        with tf.name_scope("prob"):
            self.prob = tf.nn.softmax(self.fc8, name="prob")

    # layer configuration
    def avg_pool(self, bottom, name):
        return tf.nn.avg_pool(bottom, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding="SAME", name=name)

    def max_pool(self, bottom, name):
        return tf.nn.max_pool(bottom, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding="SAME", name=name)

    # conv layer
    def conv_layer(self, bottom, in_channels, out_channels, name):
        with tf.variable_scope(name):
            filter_size = 3
            filt, conv_biases = self.get_conv_var(filter_size, in_channels, out_channels, name)

            strides = [1, 1, 1, 1]
            conv = tf.nn.conv2d(bottom, filt, strides=strides, padding="SAME")
            bias = tf.nn.bias_add(conv, conv_biases)
            relu = tf.nn.relu(bias)

            return relu

    def fc_layer(self, bottom, in_size, out_size, name):
        with tf.variable_scope(name):
            weights, biases = self.get_fc_var(in_size, out_size, name)

            x = tf.reshape(bottom, [-1, in_size])
            fc = tf.nn.bias_add(tf.matmul(x, weights), biases)

            return fc

    def get_conv_var(self, filter_size, in_channels, out_channels, name):
        filter_shape = [filter_size, filter_size, in_channels, out_channels]
        initial_value = tf.truncated_normal(filter_shape, 0.0, 0.001)
        filters = self.get_var(initial_value, name, 1, name + "_filters")
        # filters = tf.truncated_normal(filter_shape, 0.0, 0.001)

        biases_shape = [out_channels]
        initial_value = tf.truncated_normal(biases_shape, 0.0, 0.001)
        biases = self.get_var(initial_value, name, 1, name + "_biases")
        # biases = tf.truncated_normal(biases_shape, 0.0, 0.001)

        return filters, biases

    def get_fc_var(self, in_size, out_size, name):
        weigths_shape = [in_size, out_size]
        initial_value = tf.truncated_normal(weigths_shape, 0.0, 0.001)
        weights = self.get_var(initial_value, name, 0, name + "_weights")

        biases_shape = [out_size]
        initial_value = tf.truncated_normal(biases_shape, 0.0, 0.001)
        biases = self.get_var(initial_value, name, 1, name + "_biases")

        return weights, biases

    def get_var(self, initial_value, name, idx, var_name):
        if self.data_dict is not None and name in self.data_dict:
            value = self.data_dict[name][idx]
        else:
            value = initial_value

        if self.trainable:
            var = tf.Variable(value, name=var_name)
        else:
            var = tf.constant(value, dtype=tf.float32, name=var_name)

        self.var_dict[(name, idx)] = var

        # print var_name, var.get_shape().as_list()
        assert var.get_shape() == initial_value.get_shape()

        return var

    def save_npy(self, sess, npy_path='./vgg19-save.npy'):
        assert isinstance(sess, tf.Session)

        data_dict = {}

        for (name, idx), var in list(self.var_dict.items()):
            var_out = sess.run(var)
            if name not in data_dict:
                data_dict[name] = {}
            data_dict[name][idx] = var_out

        # save the npy file
        np.save(npy_path, data_dict)
        print("vgg19 npy file saved!", npy_path)
        return npy_path

    def get_var_count(self):
        count = 0

        for v in list(self.var_dict.values()):
            count += reduce(lambda x, y: x * y, v.get_shape().as_list())
        return count
