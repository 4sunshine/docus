import os
import PyPDF2
from PyPDF2 import PdfFileReader
from pdfminer.layout import LTTextBoxHorizontal, LTTextBoxVertical
from pdfminer.high_level import extract_pages
from shapely.geometry import Polygon
from tqdm import tqdm
import json


IOU_THRESHOLD = 0.15


def get_annotations(page):
    anno_bboxes = []
    if '/Annots' in page:
        for annot in page["/Annots"]:
            obj = annot.getObject()
            if '/C' in obj:
                assert '/Rect' in obj
                anno_rect = obj['/Rect']
                if isinstance(anno_rect, list):
                    if not isinstance(anno_rect[0], PyPDF2.generic.FloatObject) and not isinstance(anno_rect[0], PyPDF2.generic.NumberObject):
                        print('HAS EXCEPTION')
                        print(type(anno_rect[0]))
                        continue
                    else:
                        anno_rect = [float(x) for x in anno_rect]
                anno_bboxes.append(anno_rect)
    return anno_bboxes


def convert_bbox_to_poly(bbox):
    x0, y0, x1, y1 = bbox
    poly = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    poly = Polygon(poly)
    return poly


def calculate_iou(poly_1, poly_2):
    iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
    return iou


def get_texts(page_layout, anno_bboxes):
    anno_polys = [convert_bbox_to_poly(bbox) for bbox in anno_bboxes]
    is_matched = [False] * len(anno_polys)
    texts = []
    bboxes = []
    bboxes_inds = []
    for element in page_layout:
        if isinstance(element, LTTextBoxHorizontal) or isinstance(element, LTTextBoxVertical):
            bbox_poly = convert_bbox_to_poly(element.bbox)

            for a_ind, a_poly in enumerate(anno_polys):
                if not is_matched[a_ind]:
                    iou = calculate_iou(bbox_poly, a_poly)
                    if iou > IOU_THRESHOLD:
                        is_matched[a_ind] = True
                        texts.append(str(element.get_text()))
                        bboxes.append(element.bbox)
                        bboxes_inds.append(a_ind)
                else:
                    continue

    return texts, bboxes, bboxes_inds


def play(path):
    reader = PdfFileReader(path)

    doc_id = os.path.basename(path)
    doc_id = os.path.splitext(doc_id)[0]

    document_annotations = {
        'texts': [],
        'bboxes': [],
        'bboxes_inds': [],
        'anno_bboxes': [],
        'doc_id': doc_id,
    }

    for j, (page_layout, page) in enumerate(zip(extract_pages(path), reader.pages)):
        # GET ALL ANNOTATIONS FROM PAGE:
        anno_bboxes = get_annotations(page)

        all_texts, all_bboxes, bboxes_inds = [], [], []

        if len(anno_bboxes) > 0:
            all_texts, all_bboxes, bboxes_inds = get_texts(page_layout, anno_bboxes)

        document_annotations['texts'].append(all_texts)
        document_annotations['bboxes'].append(all_bboxes)
        document_annotations['bboxes_inds'].append(bboxes_inds)
        document_annotations['anno_bboxes'].append(anno_bboxes)

    return document_annotations


def prepare_data(data_folder):
    all_files = os.listdir(data_folder)
    all_files = sorted([f for f in all_files if f.endswith('.pdf')])

    os.makedirs('result', exist_ok=True)

    for f in tqdm(all_files, total=len(all_files)):
        anno = play(os.path.join(data_folder, f))
        doc_id = anno['doc_id']
        with open(f'result/{doc_id}.json', 'w', encoding='utf8') as fw:
            json.dump(anno, fw)


if __name__ == '__main__':
    path = 'D:\Downloads\si_izm\si\data_1\pdfs'
    prepare_data(path)
    #play(path)