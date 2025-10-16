import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from math import log10 as log

# from sympy.abc import A, B, C, D, F, G, H, I
from bson import json_util
from flask import Flask, jsonify, request, url_for
from nltk.stem import PorterStemmer
from pymongo import MongoClient
from sympy.logic.boolalg import to_dnf

app = Flask(__name__)

class Query:

    def __init__(self):
        with open('preprocessing/pii') as index_fh:
            self.pos_inv_index = json.load(index_fh)
            self.all_docs = list(set([int(doc) for count_posting in self.pos_inv_index.values()
                                      for doc in count_posting[1].keys()]))
            print('all docs', sorted(self.all_docs))

        with open('EnglishST.txt', 'r', encoding='utf-8') as swords_fh:
            swords = swords_fh.readlines()
            self.stop_words = [sword.strip() for sword in swords]

        self.symbol_map = {'A': 'B'}
        self.logic_opertors = ['&', '|', '~']
        self.stemmer = PorterStemmer()



    def query_type_checker(self, query):
        query_length = len(query.split())
        query_split = query.split()
        print('Query: ', query, type(query))
        if query_length == 1:
            docs_for_query = self.search_single_word(query)

        elif query_length > 1 and any(logic_operator for logic_operator in query_split
                                      if logic_operator in self.logic_opertors):
            docs_for_query = self.search_boolean(query)

        elif query_length > 1 and ((query[0] == '"' or query[0] == "'") and (query[-1] == '"' or query[-1] == "'")):
            docs_for_query = self.run_phrase_proximity_search(query)
        else:
            docs_for_query = []

        return docs_for_query

    def search_single_word(self, single_word_query):
        stemmed_query = self.stemmer.stem(single_word_query)
        if stemmed_query in self.pos_inv_index:
            docs = sorted([int(doc) for doc in self.pos_inv_index[stemmed_query][1].keys()])
        else:
            print('I am heere')
            docs = []
        return docs

    def search_phrase(self, quote_query):
        # check if quote
        pass

    def search_boolean(self, bool_query):
        tokens = re.findall(r"[ \w']+", bool_query)
        tokens = [token.strip() for token in tokens if len(token.strip()) > 0]

        symbols = ['A', 'B', 'C', 'D', 'F', 'G', 'H', 'I']
        token_symbols_pairs = dict()



        for j, token in enumerate(tokens):
            token_symbols_pairs[symbols[j]] = token

        print(token_symbols_pairs)
        bool_query_symbol = bool_query
        for symbol, token in token_symbols_pairs.items():
            bool_query_symbol = bool_query_symbol.replace(token, symbol)

        bool_query_symbol = re.sub(r'"', '', bool_query_symbol)
        bool_query_symbol = re.sub(r"'", '', bool_query_symbol)
        print('bool after replacement :', bool_query_symbol)


        operators = re.findall(r'& |~ |\| |&~ |\|~', bool_query_symbol)
        operators = [operator.strip() for operator in operators]
        dnf_bool_query = to_dnf(bool_query_symbol, True)
        print('dnf solution :', dnf_bool_query)

        disjuncts = [item.strip() for item in str(dnf_bool_query).split('|')]

        if len(disjuncts) > 1:
            for disjunct in disjuncts:
                if disjunct.find('(') == -1:
                    print('This has no brackets: ', disjunct)
                    disjunct = disjunct.strip()
                    docs_for_query = self.search_disjunct(disjunct, token_symbols_pairs)
                else:
                    disjunct = re.sub(r'\(|\)', '', disjunct)
                    print('stripped of brackets', disjunct)
                    query_terms = disjunct.split('&')
                    query_terms = [query.strip() for query in query_terms]
                    docs_for_query = self.search_disjunct(query_terms[0], token_symbols_pairs)
                    for j, query in enumerate(query_terms):
                        if j == 0:
                            continue
                        inter_docs_for_query = self.search_disjunct(query, token_symbols_pairs)
                        print('query:', query, 'docs', inter_docs_for_query)
                        docs_for_query = set(docs_for_query).intersection(set(inter_docs_for_query))
        else:
            docs_for_query = self.search_normals(disjuncts, token_symbols_pairs)

        print('final out ', docs_for_query)
        return docs_for_query

    def search_disjunct(self, disjunct, token_symbols_pairs):

        if disjunct[0] == '~':
            query = token_symbols_pairs[disjunct[1:]]
            docs_query = self.search_single_word(query)
            docs_query = [doc for doc in self.all_docs if doc not in docs_query]
        else:
            query = token_symbols_pairs[disjunct]
            docs_query = self.search_single_word(query)

        return docs_query

    def search_normals(self, disjuncts, token_symbols_pairs):
        bool_query = disjuncts[0]
        query_terms = [term.strip() for term in re.split(r'&|\|', bool_query)]
        operators = [operator.strip() for operator in re.findall(r'&|\|', bool_query)]
        print(query_terms, operators)
        docs_for_query = self.search_disjunct(query_terms[0], token_symbols_pairs)
        for i, query in enumerate(query_terms):
            if i == 0:
                continue
            inter_docs_for_query = self.search_disjunct(query, token_symbols_pairs)
            if operators[i - 1] == '&':
                docs_for_query = set(docs_for_query).intersection(set(inter_docs_for_query))
            elif operators[i - 1] == '|':
                docs_for_query = set(docs_for_query).union(set(inter_docs_for_query))

        return sorted(list(docs_for_query))

    def docID(self, plist):
        return plist[0]

    def position(self, plist):
        return plist[1]

    def pos_intersect(self, p1, p2, k):
        answer = []  # answer <- ()
        len1 = len(p1)
        len2 = len(p2)
        i = j = 0
        while i != len1 and j != len2:  # while (p1 != nil and p2 != nil)
            if self.docID(p1[i]) == self.docID(p2[j]):
                l = []  # l <- ()
                pp1 = self.position(p1[i])  # pp1 <- positions(p1)
                pp2 = self.position(p2[j])  # pp2 <- positions(p2)

                plen1 = len(pp1)
                plen2 = len(pp2)
                ii = jj = 0
                while ii != plen1:  # while (pp1 != nil)
                    while jj != plen2:  # while (pp2 != nil)
                        if pp2[jj] - pp1[ii] <= k and pp2[jj] - pp1[ii] > 0:  # if (|pos(pp1) - pos(pp2)| <= k)
                            l.append(pp2[jj])  # l.add(pos(pp2))
                        elif pp2[jj] > pp1[ii]:  # else if (pos(pp2) > pos(pp1))
                            break
                        jj += 1  # pp2 <- next(pp2)
                    # l.sort()
                    while l != [] and abs(l[0] - pp1[ii]) > k:  # while (l != () and |l(0) - pos(pp1)| > k)
                        l.remove(l[0])  # delete(l[0])
                    for ps in l:
                        doc_id_list = []
                        doc_id_list.append(self.docID(p1[i]))
                        doc_id_list.append([ps])  # for each ps in l
                        answer.append(doc_id_list)  # add answer(docID(p1), pos(pp1), ps)
                    ii += 1  # pp1 <- next(pp1)
                i += 1  # p1 <- next(p1)
                j += 1  # p2 <- next(p2)
            elif self.docID(p1[i]) < self.docID(p2[j]):  # else if (docID(p1) < docID(p2))
                i += 1  # p1 <- next(p1)
            else:
                j += 1  # p2 <- next(p2)
        return answer

    def run_phrase_proximity_search(self, phrase):
        # self.pos_inv_index  = {}  # pii to be setup with actual pii in runtime
        # self.setup_pii(self.pos_inv_index)  # initialize pii dict with random values for testing purposes, remove this line in actual code

        print("PHRASE->", phrase)

        phrase = re.sub("'", '', phrase)  # split phrase to words
        words = phrase.split()
        words = [self.stemmer.stem(word) for word in words]
        print('phrase search after stemming: ', words)
        input()
        merged_list = []  # to contain the merge result of docs-pos of previous two words
        j = 1
        k = 1  # value for phrase search k=1, proximity search k maybe any number
        for index, word in enumerate(words):
            if j < len(words):
                list1 = []
                list2 = []

                if word in self.pos_inv_index and len(merged_list) == 0:  # if the first word in pii and if merged  list is empty
                    for key, val in self.pos_inv_index[word][1].items():
                        list1 = self.create_list_of_lists(key, list1,
                                                     val)  # list1 setup only for first word as merged list is empty in the first iteration
                if words[j] in self.pos_inv_index:
                    for key, val in self.pos_inv_index[words[j]][1].items():
                        list2 = self.create_list_of_lists(key, list2, val)  # setup list 2 with the next word
                j += 1  # increment pointer to point to next word
                if len(merged_list) == 0:
                    merged_list = self.pos_intersect(list1, list2,
                                                k)  # setup merged list for the first time with result of first 2 words in phrase
                else:
                    merged_list = self.pos_intersect(merged_list, list2,
                                                k)  # update merged list to contain result of prev two words doc-pos merge

        # print("merge result of ",phrase,": ",merged_list )
        # merged list contains the doc-pos data for the phrase/proximity search query
        phrase_proximity_result = []
        for element in merged_list:
            phrase_proximity_result.append(element[0])
        #
        return phrase_proximity_result

    def create_list_of_lists(self, key, result, val):
        res = []
        res.append(key)
        res.append(val)
        result.append(res)
        return result

@app.route('/ttdscw3/queryMongo', methods=['POST'])
def query_mongo_db():
    if request.method == 'POST':
        query = request.json['query']
        print(query)
    cluster = MongoClient(
        "mongodb+srv://TTDSCWAdmin:TTDSPassword@cluster0.zf2ly.mongodb.net/ttds?retryWrites=true&w=majority")
    db = cluster["ttds"]
    collection = db["cell_phones_and_accessories"]
    query_processor = Query()
    doc_ids = query_processor.query_type_checker(query)
    cur = collection.find({"document_id": {"$in": doc_ids}})
    list_cur = list(cur)
    json_data = json.loads(json_util.dumps(list_cur))
    print(json_data)

    return jsonify(json_data)


if __name__ == '__main__':
    # query_processor = Query()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

    '''

    with open('queries.boolean.txt', 'r', encoding='utf-8') as query_fh:
        queries = query_fh.readlines()
        queries =[query.split(' ', 1)[1].strip() for query in queries]
        print('all queries\n', queries)
    for query in queries:
        input()
        print('-----------------------------------')
        print(query)

        result = query_processor.query_type_checker(query)
        print('result is  . . . . ')
        print(result)

    # with open('results.boolean.txt', 'w+', encoding='utf-8') as bool_fh:
    #     process_bool_queries_from_file('queries.boolean.txt', positional_index, bool_fh)
    #
    # # open fh with write permission to write results of ranked queries
    # with open('results.ranked.txt', 'w+', encoding='utf-8') as ranked_fh:
    #     process_ranked_queries('queries.ranked.txt', positional_index, ranked_fh)
        '''