# -*- coding: utf-8 -*-
"""offtarget_createdataset.py
# Create the Data Set for the Experiments.

**Objective** <br>
create the image dataset of the validated and putative off-targets extracted 
from the crispor data set and maximilianh github. <br>

**Procedure** <br>
1. remove the positive labels from the crispor-encoded-data
2. transform the encoded data into a data frame
3. add the positive labels based on the crispor paper github with encoded sequence
4. transform the encoded sequences as an image for the deep neural network experiments

**Encoded crispor data set description** <br>
*   positive labels: 143 validated off-targets
*   negative labels: [len(mm_scores)=26,052 putative off-targets] - positive labels

**Maximiliah validated off-targets data set description** <br>
*   positive labels: 718 validated off-targets
"""
#
#
import sys
import pickle as pkl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.utils import Bunch
#
#
def one_hot_encode_seq(data):
    # define universe of possible input values
    alphabet = 'AGCT'
    # define a mapping of chars to integers
    char_to_int = dict((c, i) for i, c in enumerate(alphabet))
    int_to_char = dict((i, c) for i, c in enumerate(alphabet))
    # integer encode input data
    integer_encoded = [char_to_int[char] if char in alphabet else 0 for char in data]
    # print(integer_encoded)
    # one hot encode
    onehot_encoded = list()
    for value in integer_encoded:
        letter = [0 for _ in range(len(alphabet))]
        letter[value] = 1
        onehot_encoded.append(letter)
    # print(onehot_encoded)
    # invert encoding
    inverted = int_to_char[np.argmax(onehot_encoded[0])]
    # print(inverted)
    return onehot_encoded
#
#
def flatten_one_hot_encode_seq(seq):
    return np.asarray(seq).flatten(order='C')
#
# we import the pkl encoded data
#mm_scores = pkl.load(open('../../pycrispr/notebooks/makarenkov_dummy_input.pkl','rb'), encoding='latin1')
#
# we check the off-target label
# validated off-targets identified by CRISPOR labeled as 1
#nb_val_off_target = np.sum(mm_scores[1])
#print("There is %s validated off-targets identified" % nb_val_off_target)
#
# we convert the encoded data to a pandas dataframe
df_enc = pd.DataFrame(columns=['name', 'guideSeq', 'otSeq', 'label'])
#df_enc['label'] = mm_scores[1]
#
# remove the validated encoded off-targets to replace them from the 
# the validated off-targets from maximilianh. Only keep the putative off-targets
#df_enc = df_enc[df_enc['label'] == 0]

iswritepickle = True

# we import the validated off-targets from maximilianh
fpath = '../../pycrispr/notebooks/makarenkov_input_260520.csv'
#
df_max = pd.read_csv(fpath, sep=',')
df_max = df_max[['name', 'guideSeq', 'otSeq', 'label']]
#
df_max.drop_duplicates(subset='otSeq', keep=False)
#
#
# we encode the new validated off-targets
# as described in the references
enc_dna_list = []
enc_rna_list = []
encoded_list = []
for n in range(len(df_max)):
    target_dna = df_max.loc[n, 'otSeq']
    target_rna = df_max.loc[n, 'guideSeq']
    arr1 = one_hot_encode_seq(target_dna)
    arr2 = one_hot_encode_seq(target_rna)
    arr = np.zeros((23,4))
    for m in range(len(arr1)):
        if arr1[m] == arr2[m]:
            arr[m] = arr1[m]
        else:
            arr[m] = np.add(arr1[m], arr2[m])
    arr = flatten_one_hot_encode_seq(arr)
    enc_dna_list.append(np.asarray(arr1).flatten('C'))
    enc_rna_list.append(np.asarray(arr2).flatten('C'))
    encoded_list.append(np.asarray(arr).flatten('C'))

df_max['enc_dna'] = pd.Series(enc_dna_list)
df_max['enc_rna'] = pd.Series(enc_rna_list)
df_max['encoded'] = pd.Series(encoded_list)
#
#
# we extract the values from the dataframe df_max to merge with the global df
df_enc = pd.DataFrame(df_max['encoded'].values.tolist())
df_enc['label'] = df_max['label']
df_enc['name'] = df_max['name']
#df_to_merge['label'] = 1
#df_enc = df_enc.append(df_to_merge, ignore_index=True)
#df_enc['name'] = 0
#df_enc.loc[df_enc['label'] == 1, 'name'] = df_max['name'].values
#
#
# save the encoded results as 4x23 images
# we put the results in bunch
encoded4x23 = Bunch(
    target_names=df_enc['name'].values, 
    target=df_enc['label'].values, 
    images=(df_enc.iloc[:, 0:92].values * 254).reshape(-1,4,23, order='F')
)
#plt.imshow(encoded4x23.images[0], cmap='Greys')

if iswritepickle is True:
	# we create the pkl file for later use
	pickle_out = open("encoded4x23withoutTsai.pkl","wb")
	pkl.dump(encoded4x23, pickle_out)
	pickle_out.close()

# A -> [1, 0, 0, 0]
# G -> [0, 1, 0, 0]
# C -> [0, 0, 1, 0]
# T -> [0, 0, 0, 1]

# 23 is the length of the sequence which includes the 3-bp PAM adjacent to the 20 bases
# 23 (sequence length) x 4 (size of nucleotides vocabulary)
# 26 034 putative off-targets including 143 validated off-targets identified by CRISPOR
#
#
# we want to transform the encoded putative to 8x23
# we only keep the encoded putative
put_mm_score = df_enc[df_enc['label'] == 0].iloc[:,0:92].values
#
dc = ['A', 'G', 'C', 'T']
seq_sgRNA_DNA = np.chararray((2 * len(put_mm_score),23))
seq_sgRNA_DNA[:] = ''
indx_counter = 0
indx_seq = 0
#
for iline in range(len(put_mm_score)):
	arr = put_mm_score[iline]
	arr = arr.reshape((4,23), order='F')
	# check if the encoded sgRNA-DNA sequence is > 2. => reshape is incorrect
	if (np.sum(arr, axis=0) > 3).any() == True:
		raise ValueError("Incorrect reshape of the flattening. Error at line ", iline)

	for n in range(arr.shape[1]):
		loc_bp = np.where(arr[:,n] == 1)[0]
		indx_seq = 0
		for indx_loc_bp in loc_bp:
			seq_sgRNA_DNA[indx_counter + indx_seq, n] = dc[indx_loc_bp]
			if len(loc_bp) == 1:
				seq_sgRNA_DNA[indx_counter + indx_seq + 1, n] = seq_sgRNA_DNA[indx_counter + indx_seq, n]
			indx_seq += 1
	indx_counter += 2
#
#
#seq_sgRNA_DNA[0].decode()
#pd.DataFrame(seq_sgRNA_DNA.decode())
#
# we have to transform the RNA and DNA sequences to
# a 8x23 image
#
# we create a new column on the crispor data df
# we strucuture the images as the mnist dataset
# digits.target_names is the name
# digits.target is the binary classification
# digits.images is the 8x23 pixels of the image
#a. we do it for the put. off-target
#
# we store the image in im
im = np.zeros((len(df_max), 8, 23))
#
cnt = 0
#b. we do it for the val. off-target
for n in range(len(df_max)):
	# arr1 = one_hot_encode_seq(df_max.loc[n, 'guideSeq'])
	arr1 = one_hot_encode_seq(df_max.loc[n, 'otSeq'])
	arr1 = np.asarray(arr1).T
	# arr2 = one_hot_encode_seq(df_max.loc[n, 'otSeq'])
	arr2 = one_hot_encode_seq(df_max.loc[n, 'guideSeq'])
	arr2 = np.asarray(arr2).T
	arr = np.concatenate((arr1, arr2)) * 254
	im[cnt] = arr
	cnt += 1

# we put the results in bunch
digits = Bunch(
    target_names = df_enc['name'].values, 
    target=df_enc['label'].values, 
    images=im
)
#print(plt.imshow(im[0], cmap='Greys'))
#
#
if iswritepickle is True:
	# we create the pkl file for later use
	pickle_out = open("encoded8x23withoutTsai.pkl","wb")
	pkl.dump(digits, pickle_out)
	pickle_out.close()
