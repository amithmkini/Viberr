from numpy import genfromtxt
import numpy as np

original_filename = "train_triples.txt"
trunc_filename = "truncated_data.txt"


def similarity(u,v):
	# print "Calculating sim between " + str(u) + " and " + str(v),
	numerator = float(np.inner(u,v))
	norm_u = np.linalg.norm(u)
	norm_v = np.linalg.norm(v)
	denominator = norm_u * norm_v
	# print numerator, denominator
	# print " = " + str(numerator/denominator)
	return numerator/denominator

def score(user_index,song_index,data):
	u = data[user_index]
	u_avg = np.mean(u)
	numerator = 0
	denominator = 0
	# print 'similarity = '
	for u1 in data:
		u1_avg = np.mean(u1)
		sim = similarity(u,u1)
		# print sim,
		numerator += sim * (u[song_index]-u1_avg)
		denominator += abs(sim)
	return u_avg + (numerator/denominator)	

def prediction(user_index,data,k=16):
	score_list = []
	print "Constructing score list...",
	for i in xrange(data.shape[1]):
		s = score(user_index, i, data)
		score_list.append((s, i))
	score_list.sort()
	print "Done"
	recommendations = score_list[data.shape[1]-k:data.shape[1]]
	rec_songs = [y for (x,y) in recommendations]
	# print score_list
	return rec_songs

def normalizeMatrix(data_matrix):

	num_rows = data_matrix.shape[0]
	num__cols = data_matrix.shape[1]

	data_matrix_normalized = [[0]*num__cols] * num_rows

	#normalizing the data
	for i in xrange(num_rows):
		data_matrix_normalized[i] = data_matrix[i] / float(np.amax(data_matrix[i]))

	return np.asarray(data_matrix_normalized)

if __name__ == '__main__':
	data = genfromtxt("newmatrix.csv",delimiter=",")
	num_users = data.shape[0]
	data_normal = normalizeMatrix(data)
	u = user_id
	print prediction(u,data_normal)
	print num_users 
	print data.shape[1]

	#user_music = genfromtxt('matrix.csv', delimiter=',')
	#print user_music

