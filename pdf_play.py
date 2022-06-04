import os
import PyPDF2
import pdfminer.layout
from PyPDF2 import PdfFileReader
from pdfminer.layout import LTTextBoxHorizontal, LTTextBoxVertical, LTLine
from pdfminer.high_level import extract_pages
from shapely.geometry import Polygon
from tqdm import tqdm
import json
from pdfminer.image import ImageWriter
import codecs
import cv2


IOU_THRESHOLD = 0.0001

def get_image(layout_object):
    if isinstance(layout_object, pdfminer.layout.LTImage):
        return layout_object
    if isinstance(layout_object, pdfminer.layout.LTContainer):
        for child in layout_object:
            return get_image(child)
    else:
        return None
#
# from PIL import Image
# def save_images_from_page(page: pdfminer.layout.LTPage, out_dir='output_dir'):
#     images = list(filter(bool, map(get_image, page)))
#     iw = ImageWriter(out_dir)
#     for image in images:
#         name = iw.export_image(image)
#         filename = os.path.join(out_dir, name)
#         print(filename)
#         im = Image.open(filename).convert('RGB')
#
#         #img = cv2.imread(filename)
#         basename = 'kek.png'
#         im.save(os.path.join(out_dir, basename))
#         #cv2.imwrite(os.path.join(out_dir, basename), img)
#         exit(0)


def get_annotations(page):
    anno_bboxes = []
    print('**************')
    print(page)
    print('#################')

    if '/Annots' in page:
        for annot in page["/Annots"]:
            obj = annot.getObject()
            print(obj)
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
        print(anno_bboxes)
        exit(0)
    return anno_bboxes


def convert_bbox_to_poly(bbox):
    x0, y0, x1, y1 = bbox
    poly = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    poly = Polygon(poly)
    return poly


def calculate_iou(poly_1, poly_2):
    iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
    return iou


def calculate_inclusion(poly_1, poly_2):
    inclusion = 0
    if poly_1.area > 0:
        inclusion = poly_1.intersection(poly_2).area / poly_1.area
    return inclusion


def get_texts(page_layout, anno_bboxes):
    anno_polys = [convert_bbox_to_poly(bbox) for bbox in anno_bboxes]
    is_matched = [False] * len(anno_polys)
    matched_dict = {i: [] for i in range(len(anno_polys))}
    texts = []
    bboxes = []
    bboxes_inds = []
    for element in page_layout:
        if isinstance(element, LTTextBoxHorizontal) or isinstance(element, LTTextBoxVertical):
            bbox_poly = convert_bbox_to_poly(element.bbox)

            for a_ind, a_poly in enumerate(anno_polys):
                if not is_matched[a_ind]:
                    iou = calculate_iou(bbox_poly, a_poly)
                    inclusion = calculate_inclusion(bbox_poly, a_poly)

                    if inclusion > IOU_THRESHOLD:
                        matched_dict[a_ind].append()
                        print(element.get_text())
                        print(inclusion)
                        print(element)
                    if iou > IOU_THRESHOLD:
                        #is_matched[a_ind] = True
                        texts.append(element.get_text())
                        bboxes.append(element.bbox)
                        bboxes_inds.append(a_ind)
                else:
                    continue

    return texts, bboxes, bboxes_inds, is_matched


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

    success = True

    for j, (page_layout, page) in enumerate(zip(extract_pages(path), reader.pages)):
        # GET ALL ANNOTATIONS FROM PAGE:
        # save_images_from_page(page_layout)
        anno_bboxes = get_annotations(page)

        all_texts, all_bboxes, bboxes_inds, is_matched = [], [], [], []

        if len(anno_bboxes) > 0:
            all_texts, all_bboxes, bboxes_inds, is_matched = get_texts(page_layout, anno_bboxes)

        if not all(is_matched):
            success = False

        document_annotations['texts'].append(all_texts)
        document_annotations['bboxes'].append(all_bboxes)
        document_annotations['bboxes_inds'].append(bboxes_inds)
        document_annotations['anno_bboxes'].append(anno_bboxes)

    return document_annotations, success

import pdfplumber

#from pdfplumber.page import LTTe

def plumb(filepath):
    document_data = []
    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages):

            hl_bboxes = []

            te = page.extract_words()

            words = [w['text'] for w in te]
            #print(words)

            for anno in page.annots:
                bbox_a = [anno['x0'], anno['y0'], anno['x1'], anno['y1']]

                #print(pdfminer.psparser.PSLiteral())

                #print(anno['data'])
                # print(dir(anno['data']['Subtype']))
                #print(anno['data']['Subtype'].name)
                #print(anno['data']['Subtype'].name)
                if anno['data']['Subtype'].name == 'Highlight':
                    hl_bboxes.append(bbox_a)

            hl_polys = [convert_bbox_to_poly(b) for b in hl_bboxes]

            texts = {i: '' for i in range(len(hl_polys))}

            ff = ''

            #print(bbox_a)
            #exit(0)

            for sym in page.chars:
                bbox = [sym['x0'], sym['y0'], sym['x1'], sym['y1']]

                #print(bbox)
                if bbox[0] == bbox[2]:
                    bbox[2] = bbox[2] + 2
                    #print('WWWWWWWW')
                if bbox[1] == bbox[3]:
                    bbox[3] = bbox[3] + 2
                    #print('YYYYYYY')


                bbox_p = convert_bbox_to_poly(bbox)

                ff += sym['text']

                for ind_h, h_pol in enumerate(hl_polys):
                    iod = calculate_inclusion(bbox_p, h_pol)
                    if iod > IOU_THRESHOLD:
                        texts[ind_h] += sym['text']
                        break

            page_data = {
                'annotation_bboxes': hl_bboxes,
                'annotations': texts,
                'page_size': [page.width, page.height],
            }

            document_data.append(page_data)

            #print(ff)

            # result = ff
            #
            # final_string = ''
            #
            # if 'внесен' in ff.lower() and (page_num == 0):
            #     #print('HOORAY')
            #     index = ff.lower().find('внесен')
            #     #print(index)
            #     result = result[:index]
            #     # print(words)
            #     # for w in words:
            #     #     if w.lower() in result and (len(w) > 3):
            #     #         final_string += w + ' '
            #     #
            #     # final_string = final_string[:-1]
            #     # print(final_string)
            #
            # elif 'внесён' in ff.lower() and (page_num == 0):
            #     #print('HOORAY')
            #     index = ff.lower().find('внесён')
            #     #print(index)
            #     result = result[:index]
            #
            # if page_num == 0:
            #     print(result)
        # exit(0)

    return document_data


def plumb_(filepath):
    document_data = []
    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages):

            hl_bboxes = []

            te = page.extract_words()

            words = [w['text'] for w in te]
            print(words)
            # exit(0)

            # print(page.lines)
            #
            # for element in page.layout:
            #     if isinstance(element, LTLine):
            #         print(element)
            #         print('&&&&&&&')

            # exit(0)
            # print(dir(page))
            # table = page.vertical_edges
            # print(page.objects)
            # print(table)
            # exit(0)

            for anno in page.annots:
                bbox_a = [anno['x0'], anno['y0'], anno['x1'], anno['y1']]

                # print(pdfminer.psparser.PSLiteral())

                # print(anno['data'])
                # print(dir(anno['data']['Subtype']))
                print(anno['data']['Subtype'].name)
                # print(anno['data']['Subtype'].name)
                if anno['data']['Subtype'].name == 'Highlight':
                    hl_bboxes.append(bbox_a)


            hl_polys = [convert_bbox_to_poly(b) for b in hl_bboxes]

            texts = {i: '' for i in range(len(hl_polys))}

            ff = ''

            for sym in page.chars:
                bbox = [sym['x0'], sym['y0'], sym['x1'], sym['y1']]

                bbox_p = convert_bbox_to_poly(bbox)

                ff += sym['text']

                for ind_h, h_pol in enumerate(hl_polys):
                    iod = calculate_inclusion(bbox_p, h_pol)
                    if iod > IOU_THRESHOLD:
                        texts[ind_h] += sym['text']
                        break

            page_data = {
                'annotation_bboxes': hl_bboxes,
                'annotations': texts,
                'page_size': [page.width, page.height],
            }

            document_data.append(page_data)

            print(ff)

            result = ff.lower()

            if 'внесен' in ff.lower() and (page_num == 0):
                print('HOORAY')
                result = ff
            # exit(0)


def prepare_data(data_folder):
    all_files = os.listdir(data_folder)
    all_files = sorted([f for f in all_files if f.endswith('.pdf') and f.startswith('2005')])[0:]

    os.makedirs('result', exist_ok=True)

    for f in tqdm(all_files, total=len(all_files)):
        filepath = os.path.join(data_folder, f)
        res = plumb(filepath)
        doc_id = os.path.splitext(f)[0]

        # with open(f'result/{doc_id}.json', 'w', encoding='windows-1251') as fw:
        with open(f'result/{doc_id}.json', 'w') as fw:
            json.dump(res, fw)

        #break

def prepare_data_2011(data_folder):
    all_files = os.listdir(data_folder)
    all_files = sorted([f for f in all_files if f.endswith('.pdf') and f.startswith('2010')])[1:]

    os.makedirs('result', exist_ok=True)

    for f in tqdm(all_files, total=len(all_files)):
        filepath = os.path.join(data_folder, f)
        res = plumb(filepath)
        doc_id = os.path.splitext(f)[0]

        # with open(f'result/{doc_id}.json', 'w', encoding='windows-1251') as fw:
        with open(f'result/{doc_id}.json', 'w') as fw:
            json.dump(res, fw)
        break


if __name__ == '__main__':
    path = 'D:\Downloads\si_izm\si\data_1\pdfs'
    prepare_data(path)
    #play(path)