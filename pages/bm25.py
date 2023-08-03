import json
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import re
import string
from math import log
import operator
import timeit
import glob
import nltk

from django.conf import settings

print("settings.BASE_DIR", settings.BASE_DIR)

legalstopwords_path = settings.BASE_DIR / "legalstopwords.txt"

with open(legalstopwords_path) as f:
    legal_stop_words = f.readlines()
    legal_stop_words = [word.strip() for word in legal_stop_words]


nltk.data.path.append("./nltk_data/")

nltk.download("stopwords")
nltk.download("punkt")
# import punctuations

stop_words = set(stopwords.words("english"))


stop_words = stop_words.union(legal_stop_words)


"""
supreme_court_cases_file_path = (
    "/Users/elijah.hoole/Documents/paralegal/cases_supreme_court"
)



with open("primary_key_filename_dict.json", "r") as f:
    primary_key_filename_dict = json.load(f)

"""


def clean_up_case_text(text):
    """
    This function cleans up text by removing punctuation, numbers, and stopwords.
    It also lemmatizes and stems the text.
    """
    # Remove punctuation
    # text = re.sub(r"[^\w\s]", "", text)

    # Remove newlines
    # text = re.sub(r"\n\n", "\n", text)

    # when there are two or more newlines, replace with one newline
    text = re.sub(r"(\n\s+){2,}", "", text)
    text = re.sub(r"\n\n", "\n", text)
    text = re.sub(r"\x0c", "", text)

    # replace newline charcters that are preceded and followed by alphabet or numbers with a space
    text = re.sub(r"([a-zA-Z] *)\n( *[a-zA-Z])", r"\1 \2", text)

    text = re.sub(r" {2,}", " ", text)

    text = re.sub(r"(p|P)age \d+|of \d+", " ", text)

    text = text.lower()

    return text


def preprocess(text):
    # remove punctuation

    text = text.translate(str.maketrans("", "", string.punctuation))

    # convert to lower case
    text = text.lower()
    # tokenize
    tokens = word_tokenize(text)
    # remove stop words
    tokens = [w for w in tokens if not w in stop_words]
    # stem
    tokens = [PorterStemmer().stem(w) for w in tokens]
    return tokens


def clean_query(query):
    # remove punctuations and replace with space
    tokens = preprocess(query)
    return " ".join(tokens)


##Github Version of pii.json
def createDocTable(data):
    dlt = defaultdict(int)
    for k, v in data.items():
        for p, q in v.items():
            dlt[p] += len(q)
    return dlt


def queryTokenFreq(query):
    query = clean_query(query)  ## Stemming
    query_token_freq = defaultdict(int)
    for i in set(query.strip().split()):
        query_token_freq[i] = query.split(" ").count(i)
    # print(query_token_freq)
    return query_token_freq


def score_BM25(n, f, qf, r, N, dl, avdl):
    k1 = 1.2
    k2 = 100
    b = 0.75
    R = 0.0
    K = compute_K(dl, avdl)
    first = log(((r + 0.5) / (R - r + 0.5)) / ((n - r + 0.5) / (N - n - R + r + 0.5)))
    second = ((k1 + 1) * f) / (K + f)
    third = ((k2 + 1) * qf) / (k2 + qf)
    return first * second * third


def compute_K(dl, avdl):
    k1 = 1.2
    b = 0.75
    return k1 * ((1 - b) + (b * dl / avdl))


def search_main_func(query, data, dlt):
    return search_query_bm25(query, data, dlt)


def search_query_bm25(query, data, dlt):
    query_token_freq = queryTokenFreq(query)

    sum_doc = 0

    for k, v in dlt.items():
        type(v)
        sum_doc += v
    avdl = sum_doc / len(dlt)

    query_doc_score = dict.fromkeys(dlt, 0)
    for k, v in data.items():
        if k in query_token_freq:
            for p, q in v.items():
                query_doc_score[p] += score_BM25(
                    len(data[k]),
                    len(q),
                    query_token_freq[k],
                    0,
                    len(dlt),
                    dlt[p],
                    avdl,
                )

    sorted_rank = sorted(
        query_doc_score.items(), key=operator.itemgetter(1), reverse=True
    )
    doc_list = []
    for i in sorted_rank:
        doc_list.append(i[0])

    return doc_list
