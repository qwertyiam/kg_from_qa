# 利用字典构建BIO标注
import json
import pymongo
import time


dicts_address = 'C:\\data\\medicine_dicts\\'
dicts = {'disease': [], 'symptom': [],
         'examination': [], 'medicine': []}


def load_dicts(dicts_address=dicts_address):
    def _load_baikemy_list(address, list_type):
        with open(address, 'r', encoding='utf-8') as f:
            line_list = f.readlines()
        t_list = []
        for line in line_list:
            t = line.strip().lower().split(',')
            if list_type == 'disease' or list_type == 'symptom':
                t.remove(t[3])
            elif list_type == 'examination' or list_type == 'medicine':
                t.remove(t[1])
            t_list.append(tuple(t))
        return t_list

    disease_dict = _load_baikemy_list(address=dicts_address + 'diseases_from_baikemy.csv', list_type='disease')
    symptom_dict = _load_baikemy_list(address=dicts_address + 'symptoms_from_baikemy.csv', list_type='symptom')
    examination_dict = _load_baikemy_list(address=dicts_address + 'examinations_from_baikemy.csv',
                                          list_type='examination')
    medicine_dict = _load_baikemy_list(address=dicts_address + 'medicines_from_baikemy.csv', list_type='medicine')
    return {'disease': disease_dict, 'symptom': symptom_dict,
            'examination': examination_dict, 'medicine': medicine_dict}


class BIO(object):
    def __init__(self, to_mark, use_which_dict='baikemy', dicts=dicts):
        self.to_mark = to_mark.lower()
        self.use_which_dict = use_which_dict
        self.label_positions = []
        bio_list = ['O'] * len(self.to_mark)
        bio_zeros = [0] * len(self.to_mark)
        self.bio_dict = {'bio_list': bio_list, 'bio_zeros': bio_zeros}
        self.dicts = dicts
    # self.bio_dict, self.locations = self._build_bio_list()

    def load_haodf_disease_list(self, address='/root/data/disease_list.txt'):
        with open(address, 'r') as f:
            text = f.read()
        disease_dict = json.loads(text)
        disease_list = []
        for key, value in self.disease_dict.items():
            first_subject = key.strip()
            if type(value) == dict:
                for v, k in value.items():
                    second_subject = v.strip()
                    # k为列表
                    diseases = k
                    for disease in diseases:
                        disease_list.append((first_subject, second_subject, disease))
            else:
                second_subject = ""
                diseases = value
                for disease in diseases:
                    disease_list.append((first_subject, second_subject, disease))
        return disease_list

    def _add_bio_label(self, to_add, start, end, label):
        to_add['bio_list'][start] = 'B-' + label
        to_add['bio_zeros'][start] = 1.5
        for i in range(start + 1, end):
            to_add['bio_list'][i] = 'I-' + label
            to_add['bio_zeros'][i] = 1
        return to_add

    def _build_bio_list(self, list_type):
        name_list = self.dicts[list_type]
        locations = {}

        for name_tuple in name_list:
            location = []
            position = 0
            output_name = ''
            to_find = self.to_mark
            while True:
                if list_type == 'disease' or list_type == 'symptom':
                    name = name_tuple[2]
                    output_name = '{},{},{}'.format(name_tuple[0], name_tuple[1], name_tuple[2])
                elif list_type == 'examination' or list_type == 'medicine':
                    name = name_tuple[0]
                    output_name = '{}'.format(name_tuple[0])
                else:
                    name = ""
                result = to_find.find(name)
                if result > -1:
                    start = result + position
                    position_end = result + len(name)
                    end = position_end + position

                    to_find = to_find[position_end:]
                    able_code = 0
                    for p in self.label_positions:
                        if p[0] == start and p[1] > end:
                            able_code = -1
                            break
                        elif p[1] == end and p[0] < start:
                            able_code = -1
                            break
                        elif p[0] < start and p[1] > end:
                            able_code = -1
                            break
                    if able_code == 0:
                        equal_code = 0
                        small_list = []
                        for lp in self.label_positions:
                            if lp[0] == start and lp[1] == end:
                                equal_code = 1
                            if (lp[0] > start and lp[1] <= end) or (lp[0] >= start and lp[1] < end):
                                small_list.append((lp[0], lp[1], lp[2], name))
                        if equal_code == 0:
                            self.label_positions.append((start, end, list_type))
                        # 删除长度较小的标注
                        if small_list:
                            for small in small_list:
                                self.label_positions.remove(small[0:3])
                        location.append((start, end))
                    position += position_end
                else:
                    break
            if location:
                # # 记录完整名称
                # locations[output_name] = location
                # 不记录完整位置，locations只记录具体名称，不记录科室
                locations[name] = location
        return locations

    def _get_locations(self):
        result_dict = {}

        disease_locations = self._build_bio_list(list_type='disease')
        result_dict['disease'] = disease_locations
        # print('disease', disease_locations)

        symptom_locations = self._build_bio_list(list_type='symptom')
        result_dict['symptom'] = symptom_locations
        # print('symptom', symptom_locations)

        examination_locations = self._build_bio_list(list_type='examination')
        result_dict['examination'] = examination_locations
        # print('examination', examination_locations)

        medicine_locations = self._build_bio_list(list_type='medicine')
        result_dict['medicine'] = medicine_locations
        # print('medicine', medicine_locations)

        for p in self.label_positions:
            self.bio_dict = self._add_bio_label(self.bio_dict, p[0], p[1], p[2])

        return result_dict

    def get_result(self):
        # 必须先调用_get_locations()方法，再调用bio_dict，否则bio_dict为全[o]
        return self._get_locations(), self.bio_dict['bio_list']


if __name__ == '__main__':
    start = time.time()
    # dict_address = '/root/data/'
    dicts_address = 'C:\\data\\medicine_dicts\\'
    dicts = load_dicts()
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client.haodf
    collection = db.train
    train_finder = collection.find({'mark_baikemy': {'$exists': False}}, {'qa_number': 1, '_id': 0})
    finder_count = train_finder.count()
    print('待完成任务：{}'.format(finder_count))
    count = 0
    to_where = int(input("Input where to begin:"))
    finish_where = int(input("Input where to end:"))
    for j in train_finder:
        # 从*之后开始
        if count > finish_where:
            break
        elif count < to_where:
            count += 1
            print('来到序号：{}...'.format(count))
            continue
        qa_number = j['qa_number']
        # qa_number = 501666
        one = collection.find_one({'qa_number': qa_number})
        if '病人主诉' in one.keys():
            saying = one['病人主诉']
        else:
            train_data = ""
        bio_saying = BIO(saying)
        saying_result, saying_bio_list = bio_saying.get_result()
        saying_mark = {'result': saying_result, 'bio': saying_bio_list}

        if '用药情况' in one.keys():
            medicine = one['用药情况']
        else:
            medicine = ''
        bio_medicine = BIO(medicine)
        medicine_result, medicine_bio_list = bio_medicine.get_result()
        medicine_mark = {'result': medicine_result, 'bio': medicine_bio_list}

        if 'qa_pairs' in one.keys():
            qa_pairs = one['qa_pairs']
        else:
            qa_pairs = []
        qa_pairs_mark = []
        for qa_pair in qa_pairs:
            index = qa_pair['index']
            question = qa_pair['question']
            answer = qa_pair['answer']
            bio_question = BIO(question)
            question_result, question_bio_list = bio_question.get_result()
            bio_answer = BIO(answer)
            answer_result, answer_bio_list = bio_answer.get_result()
            qa_pair_mark = {'index': index,
                            'question_result': question_result,
                            'answer_result': answer_result,
                            'question_bio': question_bio_list,
                            'answer_bio': answer_bio_list}
            qa_pairs_mark.append(qa_pair_mark)
        mark = {'saying': saying_mark, 'medicine': medicine_mark, 'qa_pairs': qa_pairs_mark}
        collection.update_one({"qa_number": qa_number}, {'$set': {'mark_baikemy': mark}})
        count += 1
        if count % 100 == 0:
            print('已完成{}个，已耗时{}min...'.format(count, round((time.time() - start) / 60, 2)))
