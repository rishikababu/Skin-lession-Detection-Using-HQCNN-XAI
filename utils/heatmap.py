import tensorflow as tf
import numpy as np
import cv2

def generate_heatmap(img, model, last_conv_layer_name):

    img_tensor = tf.convert_to_tensor(np.expand_dims(img, axis=0), dtype=tf.float32)

    submodel = model.layers[1]

    # 🔥 Clean rebuild of model graph
    inputs = tf.keras.Input(shape=(64, 64, 3))
    x = inputs

    for layer in submodel.layers:
        x = layer(x)
        if layer.name == last_conv_layer_name:
            conv_output = x

    outputs = x

    grad_model = tf.keras.models.Model(
        inputs=inputs,
        outputs=[conv_output, outputs]
    )

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_tensor)
        class_index = tf.argmax(predictions[0])
        loss = predictions[:, class_index]

    grads = tape.gradient(loss, conv_outputs)

    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    conv_outputs = conv_outputs[0]
    heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)

    heatmap = np.maximum(heatmap.numpy(), 0)
    if np.max(heatmap) != 0:
        heatmap /= np.max(heatmap)

    heatmap = cv2.resize(heatmap, (64, 64))
    heatmap = np.uint8(255 * heatmap)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    return heatmap

def overlay_heatmap(original_img, heatmap, alpha=0.4):
    original_img = cv2.resize(original_img, (64, 64))

    if original_img.max() <= 1.0:
        original_img = np.uint8(original_img * 255)

    overlay = cv2.addWeighted(original_img, 1 - alpha, heatmap, alpha, 0)

    return overlay