import PyPDF2
import sys

def play(path):
    from PyPDF2 import PdfFileReader

    import pdfminer.high_level  # $ pip install pdfminer.six

    #with open(path, 'rb') as file:
    text = pdfminer.high_level.extract_text(pdf_file=path)

    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer
    for j,page_layout in enumerate(extract_pages(path)):
        print('*****', j)
        for element in page_layout:
            print(element)

    #pdfminer
    #print(text)
    #exit(0)
        # pdfminer.high_level.extract_text_to_fp(file, sys.stdout)

    reader = PdfFileReader(path)

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