import numpy as np
import os
from tqdm import tqdm
import argparse



def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", help="The path to the created feature vector", required=True, type=str)
    parser.add_argument("--labels", help="The path to the created lable vector", required=True, type=str)
    parser.add_argument("--descriptions", help="The path to the folder with all country images", required=True, type=str)
    return parser.parse_args()

args = get_args()

features = np.load(args.features)

with open(args.lables, "r") as label_file:
    labels = label_file.read().splitlines()



train_features = np.vstack(features)
train_labels = np.array(labels)


features = [] #free memory

descriptions = os.listdir(args.descriptions)

num_labels = []
for i in train_labels:
    num_labels.append(descriptions.index(i))



from sklearn.linear_model import LogisticRegression
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from tqdm import tqdm


# Split dataset into a training set and a validation set
X_train, X_val, y_train, y_val = train_test_split(train_features, np.array(num_labels), test_size=0.05, random_state=1)

boost_classifier = xgb.XGBClassifier(
    objective='multi:softmax',
    num_class=100,
    n_estimators=50,
    max_depth=5,
    learning_rate=0.1,
    random_state=1,
    eval_metric="mlogloss",
    tree_method = 'hist'
)


with tqdm(total=boost_classifier.n_estimators, desc="Training") as pbar:
    boost_classifier.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=True,             
    )


from sklearn.ensemble import RandomForestClassifier

forest_classifier = RandomForestClassifier(n_estimators=100, max_depth = 25, random_state=1)
forest_classifier.fit(X_train, y_train)


from sklearn.svm import SVC


svm_classifier = SVC(kernel='poly', C=20, gamma=0.7, degree=2, probability=True, verbose=0)
svm_classifier.fit(X_train, y_train)


classifier = LogisticRegression(random_state=1, C=137, max_iter=2000, multi_class='multinomial')
classifier.fit(X_train, y_train)


from sklearn.ensemble import AdaBoostClassifier

adaboost_classifier = AdaBoostClassifier(
    estimator=LogisticRegression(random_state=1, C=400000, max_iter=1000, multi_class='multinomial', solver='lbfgs', penalty='l2'),
    n_estimators=2,
    learning_rate=0.05,
    random_state=1
)

adaboost_classifier.fit(X_train, y_train)


from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

lda_classifier = LinearDiscriminantAnalysis()
lda_classifier.fit(X_train, y_train)

from sklearn.linear_model import SGDClassifier

sgd_classifier = SGDClassifier(loss='hinge', alpha=0.004, max_iter=500, random_state=1)
sgd_classifier.fit(X_train, y_train)



import joblib
joblib.dump(boost_classifier, 'Franco_Detect\\models\\countryside_models\\boost_classifier.pkl')
joblib.dump(forest_classifier, 'Franco_Detect\\models\\countryside_models\\forest_classifier.pkl')
joblib.dump(svm_classifier, 'Franco_Detect\\models\\countryside_models\\svm_classifier.pkl')
joblib.dump(classifier, 'Franco_Detect\\models\\countryside_models\\log_classifier.pkl')
joblib.dump(adaboost_classifier, 'Franco_Detect\\models\\countryside_models\\adaboost_classifier.pkl')
joblib.dump(lda_classifier, 'Franco_Detect\\models\\countryside_models\\lda_classifier.pkl')
joblib.dump(sgd_classifier, 'Franco_Detect\\models\\countryside_models\\sgd_classifier.pkl')