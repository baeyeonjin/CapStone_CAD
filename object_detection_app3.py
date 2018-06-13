import os
import cv2
import time
import argparse
import multiprocessing
import numpy as np
import tensorflow as tf
import serial
from utils.app_utils import FPS, WebcamVideoStream
from multiprocessing import Queue, Pool
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

CWD_PATH = os.getcwd()
count = 0
score = 0
classes = 0

#arduino connection
allPort=['/dev/ttyACM0','/dev/ttyACM1','/dev/ttyACM2','/dev/ttyAMA0','/dev/ttyAMA1','/dev/ttyAMA2']
for port in allPort:
    try:
        print("Connect to " + port)
        ard = serial.Serial(port)
        break
    except:
        print("Fail Connect to " + port)
        
        
# Path to frozen detection graph. This is the actual model that is used for the object detection.
MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017'
PATH_TO_CKPT = os.path.join(CWD_PATH, 'object_detection', MODEL_NAME, 'frozen_inference_graph.pb')
# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join(CWD_PATH, 'object_detection', 'data', 'object_detection.pbtxt')

NUM_CLASSES = 90

# Loading label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                            use_display_name=True)
category_index = label_map_util.create_category_index(categories)


def detect_objects(image_np, sess, detection_graph):
    global score
    global classes
    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
    image_np_expanded = np.expand_dims(image_np, axis=0)
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

    # Each box represents a part of the image where a particular object was detected.
    boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

    # Each score represent how level of confidence for each of the objects.
    # Score is shown on the result image, together with the class label.
    scores = detection_graph.get_tensor_by_name('detection_scores:0')
    classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    # Actual detection.
    (boxes, scores, classes, num_detections) = sess.run(
        [boxes, scores, classes, num_detections],
        feed_dict={image_tensor: image_np_expanded})

    # Visualization of the results of a detection.
    score=np.squeeze(scores)
    classes = np.squeeze(classes).astype(np.int32)
    vis_util.visualize_boxes_and_labels_on_image_array(
        image_np,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=8)
    return image_np


def worker(input_q, output_q):
    # Load a (frozen) Tensorflow model into memory.
    global count
    global ard
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

        sess = tf.Session(graph=detection_graph)


    fps = FPS().start()
    while True:
        fps.update()
        frame = input_q.get()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output_q.put(detect_objects(frame_rgb, sess, detection_graph))
        if ( (classes[0]==17 and score[0]>=0.80) or (classes[0]==88 and score[0]>=0.80)):
#cat 라벨 id 17번 person 1번
            cv2.imwrite("frame%d.jpg" % count, frame)
            ard.write([0]) #아두이노에 0값을 전달
            obj = ard.readline() # 아두이노가 보낸 신호를 읽어옴
            kg = obj.decode().strip('\r\n')
            print(kg) # 무게
            count+=1
    fps.stop()
    sess.close()

def Rotate(src, degrees):
    if degrees == 90:
        dst = cv2.transpose(src) # 행렬 변경 
        dst = cv2.flip(dst, 1)   # 뒤집기

    elif degrees == 180:
        dst = cv2.flip(src, 0)   # 뒤집기

    elif degrees == 270:
        dst = cv2.transpose(src) # 행렬 변경
        dst = cv2.flip(dst, 0)   # 뒤집기
    else:
        dst = null
    return dst


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', '--source', dest='video_source', type=int,
                        default=0, help='Device index of the camera.')
    parser.add_argument('-wd', '--width', dest='width', type=int,
                        default=600, help='Width of the frames in the video stream.')
    parser.add_argument('-ht', '--height', dest='height', type=int,
                        default=360, help='Height of the frames in the video stream.')
    parser.add_argument('-num-w', '--num-workers', dest='num_workers', type=int,
                        default=2, help='Number of workers.')
    parser.add_argument('-q-size', '--queue-size', dest='queue_size', type=int,
                        default=5, help='Size of the queue.')
    args = parser.parse_args()

    logger = multiprocessing.log_to_stderr()
    logger.setLevel(multiprocessing.SUBDEBUG)

    input_q = Queue(maxsize=args.queue_size)
    output_q = Queue(maxsize=args.queue_size)
    pool = Pool(args.num_workers, worker, (input_q, output_q))

    video_capture = WebcamVideoStream(src=args.video_source,
                                      width=args.width,
                                      height=args.height).start()
    fps = FPS().start()

    while True:  # fps._numFrames < 120
        #if(아두이노에서 로드셀 값을 받아올 때 50g미만인 경우에 작동)
        frame = video_capture.read()
        rotateframe = Rotate(frame, 270)
        input_q.put(rotateframe)
#        t = time.time()
        output_rgb = cv2.cvtColor(output_q.get(), cv2.COLOR_RGB2BGR)
        
        cv2.imshow('Video', output_rgb)
#        fps.update()
#        print('[INFO] elapsed time: {:.2f}'.format(time.time() - t))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        #else 일경우 continue;

#    fps.stop()
#    print('[INFO] elapsed time (total): {:.2f}'.format(fps.elapsed()))
#    print('[INFO] approx. FPS: {:.2f}'.format(fps.fps()))

    pool.terminate()
    video_capture.stop()
    cv2.destroyAllWindows()