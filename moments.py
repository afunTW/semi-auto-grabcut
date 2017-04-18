import os
import sys
import cv2
import mahotas
import pickle
import logging
import numpy as np
import matplotlib.pyplot as plt

from pprint import pprint
from sklearn.cluster import KMeans
from scipy.cluster.hierarchy import dendrogram
from scipy.cluster.hierarchy import linkage
from scipy.cluster.hierarchy import cophenet
from scipy.spatial.distance import pdist


saved_dir = ''
image_path = os.path.abspath('demo')
moment_path = os.path.abspath('zernike_moments.p')

moths = [
    os.path.join(image_path, img)
    for img in os.listdir(image_path)
    if os.path.isfile(os.path.join(image_path, img))
]

def get_moments(image):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (1200, 800))
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.threshold(img, 254, 255, cv2.THRESH_BINARY)[1]
    img[690:, 650:] = 255
    img = cv2.dilate(img, None, iterations=4)
    img = cv2.erode(img, None, iterations=2)
    return mahotas.features.zernike_moments(img, img.shape[1]/2, degree=8).tolist()

def get_all_moments(moment_file=None):
    global moths

    if moment_file and os.path.isfile(moment_file):
        with open(moment_file, 'rb') as f:
            logging.info('Read the file %s' % moment_file)
            shape_features = pickle.load(f)
            if len(shape_features) == len(moths):
                return shape_features

    shape_features = {}
    for moth in moths:
        logging.info('Calculating moment of %s' % moth)
        shape_features[moth] = get_moments(cv2.imread(moth))

    outfile = moment_file or './zernike_moments.p'
    outfile = os.path.abspath(outfile)
    with open(outfile, 'wb') as f:
        pickle.dump(shape_features, f)
        logging.info('Save moment file to %s' % outfile)

    return shape_features

def concat_images(imga, imgb):
    """
    Combines two color image ndarrays side-by-side.
    """
    ha,wa = imga.shape[:2]
    hb,wb = imgb.shape[:2]
    max_height = np.max([ha, hb])
    total_width = wa+wb
    new_img = np.zeros(shape=(max_height, total_width, 3), dtype=np.uint8)
    new_img[:ha,:wa]=imga
    new_img[:hb,wa:wa+wb]=imgb
    return new_img

def concat_n_images(image_path_list):
    """
    Combines N color images from a list of image paths.
    """
    output = None
    for i, img_path in enumerate(image_path_list):
        img = plt.imread(img_path)[:,:,:3]
        if i==0:
            output = img
        else:
            output = concat_images(output, img)
    return output

def kmeans_clustering(n_clusters, n_init):
    global saved_dir, moth

    cluster_map_path = os.path.join(saved_dir, 'cluster_map.p')
    saved_img_path = os.path.join(saved_dir, 'kmeans.png')

    shape_features = get_all_moments(moment_path)
    estimator = KMeans(n_clusters=n_clusters, n_init=n_init)

    estimator.fit_predict(list(shape_features.values()))
    labels = estimator.labels_
    centers = estimator.cluster_centers_
    mapping = {
            i: {
                'center': None,
                'neighbor': [],
                'min_dist': None
            } for i in set(labels)
        }

    # mapping
    for i, moth in enumerate(list(shape_features.keys())):
        dist = pdist(
                    np.array([shape_features[moth], centers[labels[i]]]),
                    'euclidean'
                )[0]

        if not mapping[labels[i]]['center']:
            mapping[labels[i]]['center'] = moth
            mapping[labels[i]]['min_dist'] = dist
        elif dist < mapping[labels[i]]['min_dist']:
            mapping[labels[i]]['neighbor'].append(mapping[labels[i]]['center'])
            mapping[labels[i]]['center'] = moth
            mapping[labels[i]]['min_dist'] = dist
        else:
            mapping[labels[i]]['neighbor'].append(moth)

    with open(cluster_map_path, 'wb') as f:
        pickle.dump(mapping, f)
        logging.info('Save clustering result in %s' % cluster_map_path)

    for k, imgs in mapping.items():
        output = concat_n_images(imgs['neighbor'] + [imgs['center']])
        plt.subplot(n_clusters, 1, k+1)
        plt.imshow(output)
        plt.axis('off')
    plt.savefig(saved_img_path, dpi=1000)
    logging.info('Save k-means result to %s' % saved_img_path)

def main():
    try:
        kmeans_clustering(n_clusters=5, n_init=10)
    except Exception as e:
        logging.exception(e)

if __name__ == '__main__':

    global saved_dir

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [ %(levelname)8s ] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )

    saved_dir = os.path.abspath('./kmeans')
    if not os.path.exists(saved_dir):
        os.makedirs(saved_dir)
        logging.info('Create directory %s' % saved_dir)

    main()