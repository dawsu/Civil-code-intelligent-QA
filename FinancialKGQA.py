import json
import synonyms
import os.path as osp
from flask import Flask, request
from py2neo import Graph
import warnings

warnings.filterwarnings("ignore")
data_dir = 'data'
data_di = 'ci'
app = Flask(__name__)


@app.route("/qa", methods=['POST', 'GET'])
def kg_qa():
    if request.method == 'GET':
        ques = request.args.get('question')
        cb = request.args.get('callback')
        print(ques)
        ansList = []
        qa_graph = Graph('http://localhost:7474', username='neo4j', password='123456')
        if len(ques) >= 3:
            if (ques[0] == '第') and (ques[len(ques) - 1]) == '条':
                okl = 0
            elif (ques[0] == 'd') and (ques[1] == 'l') and (ques[2] == ':'):
                okl = 1
            else:
                okl = 2
        else:
            okl = 2
        keyword = []
        analyzer = synonyms.seg(ques)
        data1 = analyzer[0]
        data2 = analyzer[1]
        data_len = len(data1)
        data3 = [''] * data_len
        for i in range(0, len(data1)):
            data3[i] = data1[i] + '/' + data2[i]
        for word in data3:
            pos = word.split("/")
            a = ['n', 'nz', 'nr', 'nrf', 'v', 'vn', 'j', 'an', 'm', 'l', '合同']
            vn = ['雇佣', '聘请', '聘用']
            if (pos[1] in a) or (pos[0] in a):
                if len(pos[0]) >= 2:
                    if pos[0] in vn:
                        keyword.append('责任主体的特殊规定')
                    if pos[0] not in keyword:
                        keyword.append(pos[0])
        data = sorted(keyword, key=keyword.count, reverse=True)
        keyword = list(set(data))
        keyword.sort(key=data.index)
        print(keyword)
        print(okl)
        if okl == 2:
            for key1 in keyword:
                query_str = "MATCH (n:`章`) WHERE n.name =~'.*%s.*' return n.name" % key1
                if len(query_str) > 0:
                    answer = qa_graph.run(query_str).data()
                    if answer:
                        for item in answer:
                            ans_str = item['n.name']
                            if ans_str not in ansList:
                                ansList.append(ans_str)
        elif okl == 1:
            with open(osp.join(data_dir, '1.txt'), 'r') as f:
                lines = f.read()
                lines = lines.strip().split(',')
            anList = []
            for key1 in keyword:
                for line in lines:
                    u = synonyms.compare(line, key1, seg=True)
                    if u >= 0.875:
                        print(line + "," + key1 + ',' + str(u))
                        query_str = "MATCH (n:`章`) WHERE n.name =~'.*%s.*' return n.name" % line
                        if 0 < len(query_str):
                            answer = qa_graph.run(query_str).data()
                            if answer:
                                for item in answer:
                                    ans_str = item['n.name']
                                    ansList.append(ans_str)
            print(ansList)
            data = sorted(ansList, key=ansList.count, reverse=True)
            ansList = list(set(data))
            ansList.sort(key=data.index)
            print(ansList)
            if len(ansList) > 5:
                data = [ansList[0], ansList[1], ansList[2], ansList[3], ansList[4]]
                ansList = data
            if len(ansList) == 0:
                ansList = anList
        elif okl == 0:
            query_str = "MATCH (n:`条`) WHERE n.name = '%s' return n.strip" % ques
            if len(query_str) > 0:
                answer = qa_graph.run(query_str).data()
                if answer:
                    for item in answer:
                        ans_str = item['n.strip']
                        ansList.append(ans_str)
        if okl !=0:
            opr = []
            for ikm in range(len(ansList)):
                for iu in range(1, 8):
                    ru_ssk = ''
                    with open(osp.join(data_di, str(iu) + '.txt'), 'r') as f:
                        lines = f.read()
                        lines = lines.strip().split('\n')
                    for line in lines:
                        lines = line.strip()
                        if ansList[ikm] in lines:
                            if iu == 1:
                                ru_ssk = '总则'
                            elif iu == 2:
                                ru_ssk = '物权'
                            elif iu == 3:
                                ru_ssk = '合同'
                            elif iu == 4:
                                ru_ssk = '人格权'
                            elif iu == 5:
                                ru_ssk = '婚姻家庭'
                            elif iu == 6:
                                ru_ssk = '继承'
                            elif iu == 7:
                                ru_ssk = '侵权责任'
                    if ru_ssk != '':
                        opr.append(ru_ssk + " 下属: " + ansList[ikm])
            ansList = opr
        print(ansList)
        re_ans = "您问的可能是这些问题:"
        for i in range(len(ansList)):
            re_ans += "(%s) %s " % (i + 1, ansList[i])
        if len(ansList) == 0:
            re_ans = '您好,对于此类问题,您可以咨询公安部门'
        print(re_ans)
        result = {
            "question": ques,
            "answer": re_ans
        }
        res_str = json.dumps(result)
        cb_str = cb + "(" + res_str + ")"
        return cb_str
    return 'Error Format'


if __name__ == '__main__':
    from werkzeug.serving import run_simple

    run_simple('127.0.0.1', 9001, app)
