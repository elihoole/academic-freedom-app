import json
import re
import sys

import pymongo
from flask import Flask
from flask_restful import Api, Resource
from nltk.stem import PorterStemmer
from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)

cluster = MongoClient("mongodb+srv://TTDSCWAdmin:TTDSPassword@cluster0.zf2ly.mongodb.net/ttds?retryWrites=true&w=majority")
db = cluster["ttds"]
collection = db["cell_phones_and_accessories"]

class Preprocess(Resource):
	pii={}

	#pre-process the given text
	def preprocessing(self, text):
		preprocessedtokens=[]
		stopwordsfile = open(r'../legalstopwords.txt','r')
		stopwords = stopwordsfile.read().split()
		tokens = re.split(r"[ ,.:;!&=\n]", text)
		for token in tokens:
			if token.lower() not in stopwords and token !='': #stopping
				token.lower() #case-folding
				porter = PorterStemmer()
				stemmedtoken = porter.stem(token) #porter-stemming
				if stemmedtoken.lower() not in stopwords: #stopping
					preprocessedtokens.append(stemmedtoken)
		return preprocessedtokens

	def indexv2(self, docbeingprocessed, tokens):
		# evaluate every token to generate index
		for pos, token in enumerate(tokens):
			# if token exists in our index
			if token in self.pii:
				# if the token exists in the doc
				if docbeingprocessed in self.pii[token]:
					self.pii[token][docbeingprocessed].append(pos)
				else:
					self.pii[token][docbeingprocessed] = [pos]
			# if we see the token for the first time
			else:
				self.pii[token] = {}
				# append the document number
				self.pii[token][docbeingprocessed] = [pos]

	def post(self):
		doc_ids=0
		while(doc_ids!=2000000):
			docs = collection.find({"document_id":{'$lt':doc_ids+10000,'$gte':doc_ids}})
			doc_ids+=10000
			for jsonobj in docs:
				if "reviewText" in jsonobj.keys():
					tokens = self.preprocessing(jsonobj["reviewText"])
					self.indexv2(jsonobj["document_id"], tokens)


	def get(self):
		dictobj = json.dumps(self.pii)
		#print(sys.getsizeof(self.pii))
		return sys.getsizeof(dictobj)

	def put(self):
		outputfile = open(r'C:\Users\pyath\Documents\Edinburgh\TTDS\CW3\piinew.txt', 'w')
		outputfile.write(json.dumps(self.pii))

api.add_resource(Preprocess, "/preprocess")
if __name__ == "__main__":
    app.run(debug=True)