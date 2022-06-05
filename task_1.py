import json
import pandas as pd
import torch
from tqdm import tqdm
import os

from sklearn.feature_extraction.text import TfidfVectorizer

from transformers import AutoTokenizer, BertForMaskedLM, BertForSequenceClassification

# tokenizer = AutoTokenizer.from_pretrained("sberbank-ai/ruBert-base")
# model = BertForMaskedLM.from_pretrained("sberbank-ai/ruBert-base")
#
# corpus = ['Преобразователи давления пневматические.', 'Преобразователи давления пневматические.',
#           'Генераторы телевизионных испытательных сигналов.', 'Измерители суммарного люфта рулевого управления автотранспортных средств',]
# vectorizer = TfidfVectorizer()
# X = vectorizer.fit_transform(corpus)
# print(vectorizer.get_feature_names_out())
#
# print(vectorizer)
#
# exit(0)

def match_measure(jsons_dir='D:\personal_repos\dataset_hl', file='D:\Downloads\si_izm\dataset_13.xlsx'):
    df = pd.read_excel(file)
    df = df.rename(columns={
        "Номер_в_госреестре": "N",
        "Наименование_СИ": "CI",
        "Единица_измерения_СИ": "CI count",
        "Погрешность_СИ": "Error",
        "Наименование_файла_с_описанием": "File",
    })

    all_jsons = os.listdir(jsons_dir)

    all_jsons = sorted(all_jsons)

    stop_words = ['не менее', 'не превышает', 'Диапазон измерений', 'а 1 - Основные метроло',
                  'ии', 'ий', 'ис', 'ост', 'зк', 'лич' , 'ee', 'троло', 'част', 'ее', 'нал',
                  '...', '000', 'оток', "ени", "ова", "ниев", "до"]

    total = 0
    nones = 0

    for f in all_jsons:
        doc_id = os.path.splitext(f)[0]
        doc_id = '-'.join(doc_id.split('-')[1:3])
        filename = os.path.join(jsons_dir, f)
        err_string = None
        with open(filename, 'r') as f:
            data = json.load(f)

            all_annots = [page for page in data]
            all_entries = [anno['annotations'] for anno in all_annots]
            result_entries = []
            for anno in all_entries:
                for k, v in anno.items():
                    result_entries.append(v)

            if len(result_entries) > 1:
                measure_string = result_entries[1]
            if len(result_entries) > 2:
                err_string = result_entries[-1]
                err_string = err_string.replace(' ', '')
                err_string = ''.join([s for s in err_string if not s.isalpha()])
                #err_string = err_string.split(',')[-1]
                if ('погр' in measure_string.lower()) or ('греш' in measure_string.lower()):
                    measure_string = None
                elif len(measure_string) == 0:
                    measure_string = None
                if measure_string is not None:
                    if measure_string[-1] == ';' or measure_string[-1] == ':' or measure_string[-1] == ',':
                        measure_string = measure_string[:-1]
                    measure_string = measure_string.split(',')[-1]
                    measure_string = measure_string.split(')')[-1]
                    measure_string = measure_string.replace(' ', '')
                    measure_string = measure_string.replace(';', '')
                    if len(measure_string) > 0:
                        if measure_string[-1] == ';' or measure_string[-1] == ':' or measure_string[-1] == ',':
                            measure_string = measure_string[:-1]
                    if len(measure_string) > 6:
                        measure_string = measure_string[-6:]
                    if len(measure_string) == 0:
                        measure_string = None
            else:
                measure_string = None
            if (measure_string is not None) and (len(measure_string) == 0):
                measure_string = None
            total += 1
            if measure_string is not None:
                for word in stop_words:
                    if word in measure_string.lower():
                        measure_string = None
                        break
            if measure_string is not None:
                nones += 1

                #print(measure_string)
        print(err_string)
        #
        # if measure_string is not None:
        #     try:
        #         row = df.loc[df['N'] == doc_id].index.values[0]
        #         col = "CI count"
        #         df.loc[row, col] = measure_string
        #     except IndexError:
        #         pass

        if err_string is not None and isinstance(err_string, str):
            err_string = str(err_string)
            if len(err_string) > 6:
                err_string = err_string[-6:]

        if measure_string is not None:
            try:
                row = df.loc[df['N'] == doc_id].index.values[0]
                col = "CI count"
                df.loc[row, col] = measure_string
            except IndexError:
                pass

                if err_string is not None:
                    try:
                        col = "Error"
                        df.loc[row, col] = err_string
                    except IndexError:
                        pass
    #
    # print(total)
    # print(nones)
    # exit(0)

    df = df.sort_values(by=['CI count', 'Error'])

    df = df.rename(columns={
        "N": "Номер_в_госреестре",
        "CI": "Наименование_СИ",
        "CI count": "Единица_измерения_СИ",
        "Error": "Погрешность_СИ",
        "File": "Наименование_файла_с_описанием",
    })

    new_dataset_csv_file = 'D:\Downloads\si_izm\dataset_final_f_ff3_2.xlsx'

    df.to_excel(new_dataset_csv_file, index=False)

@torch.no_grad()
def create_task_one_table(file='D:\Downloads\si_izm\si\data_1\ds_1.csv'):
    sep = ';'
    csv = pd.read_csv(file, delimiter=';', encoding='windows-1251')
    print(csv.head())
    all_vecs = []
    all_files = os.listdir('D:\Downloads\si_izm\si\data_1\pdfs')
    # all_nums =

    for index, row in tqdm(csv.iterrows()):
        num = row['Номер_в_госреестре']
        si = row['Наименование_СИ']
        file_id = row['Наименование_файла_с_описанием']
        meas = row['Единица_измерения_СИ']
        delta = row['Погрешность_СИ']

        print(num)
        break



        # tokenized = tokenizer([si], max_length=30, padding='max_length')
        #
        # outputs = model(input_ids=torch.tensor(tokenized.input_ids),
        #                 attention_mask=torch.tensor(tokenized.attention_mask),
        #                 token_type_ids=torch.tensor(tokenized.token_type_ids),
        #                 return_dict=True, output_hidden_states=True,)
        #
        # vec = outputs['hidden_states'][-1][0, 0]
        #
        # all_vecs.append(vec)

    # all_vecs = torch.stack(all_vecs)
    # torch.save(all_vecs, 'si_bert_vectors.pth')
    # # print(all_vecs.shape)
    # # exit(0)
    #
    # with open(file, 'r', encoding='windows-1251') as f:
    #     for i, line in f.readlines():
    #         line = line.strip()
    #         elements = line.split(';')
    #         target_file = elements[-1]
    #         code = elements[0]
    #         si = elements[1]
    #
    #         print(target_file)
    #         print(code)
    #         print(si)
    #         exit(0)


# def string_similarity():
#     string_1 = 'Счетчики скоростные крыльчатыехолодной и горячей воды'
#
#     #string_2 = 'Счетчики скоростные крыльчатые холодной и горячей воды'
#     string_2 = 'Пределы допускаемых значенийотносительной погрешности винтервалах измеряемого расхода,'
#
#     inputs = [string_1, string_2]
#
#     tokenized = tokenizer(inputs, max_length=18, padding='max_length')
#
#     with torch.no_grad():
#         print(tokenized)
#         outputs = model(input_ids=torch.tensor(tokenized.input_ids)[:, :18],
#                         attention_mask=torch.tensor(tokenized.attention_mask)[:, :18],
#                         token_type_ids=torch.tensor(tokenized.token_type_ids)[:, :18],
#                         return_dict=True, output_hidden_states=True,
#                         )
#         hs = outputs['hidden_states'][-1]
#
#         vec1, vec2 = hs[:, 0, :]
#         scalar = torch.sum(vec1 * vec2) / torch.norm(vec1) / torch.norm(vec2)
#         print(vec1.shape)
#         print(scalar)
#         exit(0)
#         #print(hs)
#         #print(hs.shape)
#         print(len(hs))
#         print(hs[0].shape)
#     # print(tokenized)
#     # print(outputs)


if __name__ == '__main__':
    match_measure()
    #create_task_one_table()
    #string_similarity()


