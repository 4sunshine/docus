import PyPDF2
import sys

from PyPDF2 import PdfFileReader
from pdfminer.layout import LTTextContainer
from pdfminer.high_level import extract_pages


def play(path):
    reader = PdfFileReader(path)

    for j, (page_layout, page) in enumerate(zip(extract_pages(path), reader)):
        print('*****', j)
        for element in page_layout:
            print(element)

    #pdfminer
    #print(text)
    #exit(0)
        # pdfminer.high_level.extract_text_to_fp(file, sys.stdout)



    for i, page in enumerate(reader.pages):
        print('PAGE', i)
        # text = page.extractText()
        # print(text)
        try:
            for annot in page["/Annots"]:
                print(annot.getObject())  # (1)
                print("")
        except:
            # there are no annotations on this page
            pass


if __name__ == '__main__':
    path = 'D:\Downloads\si_izm\si\data_1\pdfs\\2005-30815-05.pdf'
    play(path)