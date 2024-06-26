import argparse
import numpy as np
import os

# debug flag for tensorflow model
parser = argparse.ArgumentParser()
parser.add_argument('--debug-tf', type=str, default='false')
args = parser.parse_args()

debug_mode = args.debug_tf.lower() == 'true'
if debug_mode:
    print('DEBUG MODE FOR TENSORFLOW MODEL')

# # Clear cache directory
#os.environ["TFHUB_CACHE_DIR"] = "/nonexistent/directory"

model = None
if not debug_mode:
    import tensorflow as tf
    from tensorflow.keras.saving import load_model
    import tensorflow_hub as hub
    try:
        model = load_model("assets/models/17_effv2b0_ft_alt2_lr1e-4_d80p_6e.h5", custom_objects={'KerasLayer':hub.KerasLayer}) if not debug_mode else None
    except:
        os.environ["TFHUB_CACHE_DIR"] = "/nonexistent/directory"
        model = load_model("assets/models/17_effv2b0_ft_alt2_lr1e-4_d80p_6e.h5", custom_objects={'KerasLayer':hub.KerasLayer}) if not debug_mode else None

class_names = ['2C', '2D', '2H', '2S', '3C', '3D', '3H', '3S', '4C', '4D', '4H', '4S', '5C', '5D', '5H', '5S', '6C', '6D', '6H', '6S', '7C', '7D', '7H', '7S', '8C', '8D', '8H', '8S', '9C', '9D', '9H', '9S', 'AC', 'AD', 'AH', 'AS', 'JC', 'JD', 'JH', 'JS', 'KC', 'KD', 'KH', 'KS', 'QC', 'QD', 'QH', 'QS', 'TC', 'TD', 'TH', 'TS']


def classify_card(img):
    if debug_mode:
        return '2C'
    img = img / 255.
    img = np.array(img)
    img = img.reshape((1,224,224,3))
    pred_probs = model.predict(img)
    pred_class = class_names[pred_probs.argmax()]
    pred_prob = max(pred_probs[0])
    pred_prob = str(round(pred_prob * 100, 2)) + "%"
    return pred_class