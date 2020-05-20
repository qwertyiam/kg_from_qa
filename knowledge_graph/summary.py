# 根据标注结果找出疾病、症状、检查、药物几种实体
import pymongo
import time

start = time.time()

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client.haodf
collection = db.train

mark_finder = collection.find({'mark_baikemy': {'$exists': True}}, {'mark_baikemy': 1,
                                                                    'qa_number': 1,
                                                                    '_id': 0})


def count(result={}):
    result['disease'] = {k: len(v) for k,v in result['disease'].items()}
    result['symptom'] = {k: len(v) for k,v in result['symptom'].items()}
    result['medicine'] = {k: len(v) for k,v in result['medicine'].items()}
    result['examination'] = {k: len(v) for k,v in result['examination'].items()}
    return result


def summary(result_all={}, new_result={}):
    def _sum_one(result_one, new_result_one):
        for name in new_result_one.keys():
            if name in result_one.keys():
                result_one[name] += new_result_one[name]
            else:
                result_one[name] = new_result_one[name]
        return result_one
    result_all['disease'] = _sum_one(result_all['disease'], new_result['disease'])
    result_all['symptom'] = _sum_one(result_all['symptom'], new_result['symptom'])
    result_all['medicine'] = _sum_one(result_all['medicine'], new_result['medicine'])
    result_all['examination'] = _sum_one(result_all['examination'], new_result['examination'])
    return result_all


def find_max(names={}):
    mnum = 0
    mname = ''
    for name in names.keys():
        if names[name] > mnum:
            mnum = names[name]
            mname = name
        elif names[name] == mnum:
            if len(name) > len(mname):
                mname = name
    return mname


num = 0
for mark in mark_finder:
    result_all = {'disease': {}, 'symptom': {}, 'medicine': {}, 'examination': {}}
    qa_number = mark['qa_number']
    markb = mark['mark_baikemy']
    medicine_mark = markb['medicine']
    qa_pairs_mark = markb['qa_pairs']
    saying_mark = markb['saying']

    # qas_result = qa_pairs_mark['result']
    medicine_result = medicine_mark['result']

    for qa in qa_pairs_mark:
        question_result = qa['question_result']
        result_all = summary(result_all, count(question_result))
        answer_result = qa['answer_result']
        result_all = summary(result_all, count(answer_result))
    result_all = summary(result_all, count(medicine_result))

    f = lambda x: x[1]
    if result_all['disease'] != {}:
        main_disease = find_max(result_all['disease'])
    else:
        main_disease = ''
    if result_all['symptom'] != {}:
        main_symptom = find_max(result_all['symptom'])
    else:
        main_symptom = ''
    if result_all['examination'] != {}:
        main_examination = find_max(result_all['examination'])
    else:
        main_examination = ''
    if result_all['medicine'] != {}:
        main_medicine = find_max(result_all['medicine'])
    else:
        main_medicine = ''

    collection.update_one({"qa_number": qa_number}, {'$set': {'summary': {'all': result_all,
                                                                          'main': {'disease': main_disease,
                                                                                   'symptom': main_symptom,
                                                                                   'examination': main_examination,
                                                                                   'medicine': main_medicine}}}})
    num += 1
    if num % 1000 == 1:
        print('disease', main_disease)
        print('symptom', main_symptom)
        print('examination', main_examination)
        print('medicine', main_medicine)
        print('已完成{}个，耗时{}s...'.format(num, time.time()-start))

