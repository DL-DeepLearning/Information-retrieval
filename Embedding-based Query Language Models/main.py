import operator
import numpy as np
import readAssessment
import ProcDoc
import Expansion
import plot_diagram
import word2vec_model
import Embedded_based
from collections import defaultdict
from math import log
import cPickle as Pickle
import os

data = {}				# content of document (doc, content)
background_model = {}	# word count of 2265 document (word, number of words)
general_model = {}
query = {}				# query
query_lambda = 0.4
doc_lambda = 0.8
remove_list = ["update_embedded_query_expansion_ci.pkl", "update_embedded_query_expansion_qi.pkl", "collection_embedded.pkl", "query_embedded.pkl", "collection_total_similarity.pkl"]

document_path = "../Corpus/TDT2/SPLIT_DOC_WDID_NEW"
query_path = "../Corpus/TDT2/QUERY_WDID_NEW_middle"

# document model
data = ProcDoc.read_file(document_path)
doc_wordcount = ProcDoc.doc_preprocess(data)
doc_unigram = ProcDoc.unigram(dict(doc_wordcount))

# background_model
background_model = ProcDoc.read_background_dict()

# general model
collection = {}
collection_total_similarity = {}
for key, value in doc_wordcount.items():
	for word, count in value.items():
		if word in collection:
			collection[word] += count
		else:
			collection[word] = count
			
collection_word_sum = 1.0 * ProcDoc.word_sum(collection)
general_model = {k : v / collection_word_sum for k, v in collection.items()}

# query model
query = ProcDoc.read_file(query_path)
query = ProcDoc.query_preprocess(query)
query_wordcount = {}

for q, q_content in query.items():
	query_wordcount[q] = ProcDoc.word_count(q_content, {})

query_unigram = ProcDoc.unigram(dict(query_wordcount))
query_model = query_unigram
Pickle.dump(query_model, open("model/query_model.pkl", "wb"), True)

# remove template file
for rm_file in remove_list:
	if os.path.isfile("model/" + rm_file):
		os.remove("model/" + rm_file)
		
# Embedded Query Expansion
m_list = np.linspace(0, 80, num=81)
m = 1
interpolated_aplpha_list = np.linspace(0, 1.0, num=11)
word2vec = word2vec_model.word2vec_model()

EQE1 = []
EQE2 = []
for m in m_list:
	[tmp_eqe1, tmp_eqe2] = Embedded_based.EmbeddedQuery(query_wordcount, collection, word2vec, 0.5, int(m))
	tmp_eqe1 = ProcDoc.modeling(tmp_eqe1, background_model, query_lambda)
	tmp_eqe2 = ProcDoc.modeling(tmp_eqe2, background_model, query_lambda)
	EQE1.append(tmp_eqe1)
	EQE2.append(tmp_eqe2)

Pickle.dump(EQE1, open("model/eqe1_10.pkl", "wb"), True)
Pickle.dump(EQE2, open("model/eqe2_10.pkl", "wb"), True)
'''

EQE1 = Pickle.load(open("model/eqe1_10.pkl", "rb"))
EQE2 = Pickle.load(open("model/eqe2_10.pkl", "rb"))
'''
# query process
print "query ..."
assessment = readAssessment.get_assessment()
query_docs_point_fb = {}
query_model_fb = {}
mAP_list = []
for query_model in EQE2:
	for step in range(1):
		query_docs_point_dict = {}
		AP = 0
		mAP = 0
		for q_key, q_word_prob in query_model.items():
			docs_point = {}
			for doc_key, doc_words_prob in doc_unigram.items():
				point = 0
				# calculate each query value for the document
				for query_word, query_prob in q_word_prob.items():
					word_probability = 0			# P(w | D)
					# check if word at query exists in the document
					if query_word in doc_words_prob:
						word_probability = doc_words_prob[query_word]
					# KL divergence 
					# (query model) * log(doc_model) 			
					point += query_model[q_key][query_word] * log((1-doc_lambda) * word_probability + doc_lambda * background_model[query_word])
				docs_point[doc_key] = point
				# sorted each doc of query by point
			docs_point_list = sorted(docs_point.items(), key=operator.itemgetter(1), reverse = True)
			query_docs_point_dict[q_key] = docs_point_list
		# mean average precision	
		mAP = readAssessment.mean_average_precision(query_docs_point_dict, assessment)
		mAP_list.append(mAP)
		print "mAP"
		print mAP
		'''
		if step < 1:
			# save one shot result
			Pickle.dump(query_model, open("model/query_model.pkl", "wb"), True)
			Pickle.dump(query_docs_point_dict, open("model/query_docs_point_dict.pkl", "wb"), True)
		# load one shot result
		query_docs_point_fb = Pickle.load(open("model/query_docs_point_dict.pkl", "rb"))
		query_model_fb = Pickle.load(open("model/query_model.pkl", "rb"))
			
		query_model = Expansion.feedback(query_docs_point_fb, query_model_fb, dict(doc_unigram), dict(doc_wordcount), dict(general_model), dict(background_model), step + 1)
		'''
	
print np.argmax(np.array(mAP_list), axis = 0), mAP_list[np.argmax(np.array(mAP_list), axis = 0)]
plot_diagram.plotList(m_list, mAP_list, "Conditional Independence of Query Terms", "mAP")


