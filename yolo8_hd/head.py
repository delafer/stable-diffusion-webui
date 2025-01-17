#Import Packages
import os
import onnxruntime
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
#import fire
import cvzone

# Global Variables
confidence = 80
conf_thresold = 0
iou_thresold = 0.3

# read image
def read_image(image_path):
    image = cv2.imread(image_path)
    # Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return rgb_image


#pre proccess image
def pre_image(image,input_shape):
    input_height, input_width = input_shape[2:]
    resized = cv2.resize(image, (input_width, input_height))
    # Scale input pixel value to 0 to 1
    input_image = resized / 255.0
    input_image = input_image.transpose(2,0,1)
    input_tensor = input_image[np.newaxis, :, :, :].astype(np.float32)
    input_tensor.shape
    return input_tensor

# load model
def load_model(model_path):
    opt_session = onnxruntime.SessionOptions()
    opt_session.enable_mem_pattern = False
    opt_session.enable_cpu_mem_arena = False
    opt_session.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_DISABLE_ALL
    model_path = model_path
    EP_list = ['CUDAExecutionProvider', 'CPUExecutionProvider']
    ort_session = onnxruntime.InferenceSession(model_path, providers=EP_list)
    model_inputs = ort_session.get_inputs()
    input_names = [model_inputs[i].name for i in range(len(model_inputs))]
    input_shape = model_inputs[0].shape

    return [ort_session, input_shape]

# run inference using the onnx model
def predict(image, ort_session, input_tensor,conf=0.8):

    conf_thresold = conf


    model_inputs = ort_session.get_inputs()
    input_names = [model_inputs[i].name for i in range(len(model_inputs))]
    input_shape = model_inputs[0].shape
    input_height, input_width = input_shape[2:]
    image_height, image_width = image.shape[:2]
    model_output = ort_session.get_outputs()
    output_names = [model_output[i].name for i in range(len(model_output))]
    outputs = ort_session.run(output_names, {input_names[0]: input_tensor})[0]
    predictions = np.squeeze(outputs).T
    # conf_thresold = 0.8
    # conf_thresold = confidence/100
    # Filter out object confidence scores below threshold
    scores = np.max(predictions[:, 4:], axis=1)
    predictions = predictions[scores > conf_thresold, :]
    scores = scores[scores > conf_thresold]
    # Get the class with the highest confidence
    class_ids = np.argmax(predictions[:, 4:], axis=1)
    # Get bounding boxes for each object
    boxes = predictions[:, :4]
    #rescale box
    input_shape = np.array([input_width, input_height, input_width, input_height])
    boxes = np.divide(boxes, input_shape, dtype=np.float32)
    boxes *= np.array([image_width, image_height, image_width, image_height])
    boxes = boxes.astype(np.int32)

    return [boxes, scores, class_ids]

# annotate the image by drawing the bounding boxes
def annotate(image, boxes, scores, class_ids,iou=0.3):

    iou_thresold =iou


    # Apply non-maxima suppression to suppress weak, overlapping bounding boxes
    indices = nms(boxes, scores, iou_thresold)
    # Define classes
    CLASSES = ['head']
    image_draw = image.copy()
    for (bbox, score, label) in zip(xywh2xyxy(boxes[indices]), scores[indices], class_ids[indices]):
        bbox = bbox.round().astype(np.int32).tolist()
        cls_id = int(label)
        cls = CLASSES[cls_id]
        color = (0,255,0)

        x1,y1,w,h = bbox[0], bbox[1], bbox[2]-bbox[0], bbox[3]-bbox[1]
        cvzone.cornerRect(image_draw, (x1,y1,w,h), colorR=(0, 255, 0),t=1)
        cvzone.putTextRect(image_draw, f"{score:.2f}", (max(0,x1), max(35,y1)), thickness=2,scale=0.8, font=cv2.FONT_ITALIC)
        #{cls} {score:.2f}

    # Image.fromarray(cv2.cvtColor(image_draw, cv2.COLOR_BGR2RGB))
    rgb_image_draw = cv2.cvtColor(image_draw, cv2.COLOR_BGR2RGB)
    return rgb_image_draw

def nms(boxes, scores, iou_threshold):
    # Sort by score
    sorted_indices = np.argsort(scores)[::-1]
    keep_boxes = []
    while sorted_indices.size > 0:
        # Pick the last box
        box_id = sorted_indices[0]
        keep_boxes.append(box_id)
        # Compute IoU of the picked box with the rest
        ious = compute_iou(boxes[box_id, :], boxes[sorted_indices[1:], :])
        # Remove boxes with IoU over the threshold
        keep_indices = np.where(ious < iou_threshold)[0]
        # print(keep_indices.shape, sorted_indices.shape)
        sorted_indices = sorted_indices[keep_indices + 1]

    return keep_boxes

def compute_iou(box, boxes):
    # Compute xmin, ymin, xmax, ymax for both boxes
    xmin = np.maximum(box[0], boxes[:, 0])
    ymin = np.maximum(box[1], boxes[:, 1])
    xmax = np.minimum(box[2], boxes[:, 2])
    ymax = np.minimum(box[3], boxes[:, 3])

    # Compute intersection area
    intersection_area = np.maximum(0, xmax - xmin) * np.maximum(0, ymax - ymin)

    # Compute union area
    box_area = (box[2] - box[0]) * (box[3] - box[1])
    boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    union_area = box_area + boxes_area - intersection_area

    # Compute IoU
    iou = intersection_area / union_area

    return iou

def xywh2xyxy(x):
    # Convert bounding box (x, y, w, h) to bounding box (x1, y1, x2, y2)
    y = np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2
    y[..., 1] = x[..., 1] - x[..., 3] / 2
    y[..., 2] = x[..., 0] + x[..., 2] / 2
    y[..., 3] = x[..., 1] + x[..., 3] / 2
    return y

def prediction(image_path, conf=20, model_path="best_re_final.onnx"):
    global confidence
    global conf_thresold

    confidence = conf
    conf_thresold = confidence/100
    # *Calling Functions
    model = load_model(model_path)
    image = read_image(image_path)
    input_I = pre_image(image, model[1]) #path and input shape is passed
    predictions = predict(image, model[0], input_I, conf_thresold)  #image, ort_session, and input tensor is passed
    print(predictions)
    annotated_image = annotate(image, predictions[0], predictions[1], predictions[2]) #boxes, and scores are passed
    # plt.imshow(annotated_image)
    # plt.show()
    return annotated_image

def getCenter(image, conf=20, model_path="yolo8_hd/best_re_final.onnx"):
    global confidence
    global conf_thresold

    confidence = conf
    conf_thresold = confidence/100
    # *Calling Functions
    model = load_model(model_path)
    input_I = pre_image(image, model[1]) #path and input shape is passed
    predictions = predict(image, model[0], input_I, conf_thresold)  #image, ort_session, and input tensor is passed
    all_rect = predictions[0]
    if len(all_rect) > 0:
        bbox = all_rect[np.argmax(predictions[1])]
        return bbox[0], bbox[1]
    else:
        return None, None

def getHeadxywh(image, conf=20, model_path="yolo8_hd/best_re_final.onnx"):
    global confidence
    global conf_thresold

    confidence = conf
    conf_thresold = confidence/100
    # *Calling Functions
    model = load_model(model_path)
    input_I = pre_image(image, model[1]) #path and input shape is passed
    predictions = predict(image, model[0], input_I, conf_thresold)  #image, ort_session, and input tensor is passed
    all_rect = predictions[0]
    if len(all_rect) > 0:
        bbox = all_rect[np.argmax(predictions[1])]
        bbox = xywh2xyxy(bbox)
        x,y,w,h = bbox[0], bbox[1], bbox[2]-bbox[0], bbox[3]-bbox[1]
        return x,y,w,h
    else:
        return None, None, None, None

def test():
    input_path = "../workdir/input-old/"
    output_path = "../workdir/head/"
    for f in os.listdir(input_path):
        sth = prediction(input_path+f)
        cv2.imwrite(output_path+f, sth)

def testxywh():
    path = ("../workdir/input-old/output_0072.jpg")
    x,y,w,h = getHeadxywh(read_image(path))
    image = cv2.imread(path)
    image[y+h:] = 0
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.imwrite("sth.jpg", image)

def testprediction():
    path = ("../workdir/input-old/output_0072.jpg")
    sth = prediction(path)
    cv2.imwrite("sth.jpg", sth)

if __name__=="__main__":
    testxywh()
