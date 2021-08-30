import pickle
from numpy.lib.function_base import vectorize
import pandas as pd
import flask
from flask import Flask, render_template, request, jsonify
import sqlite3 as sql
import os
from pdfminer.high_level import extract_text
from pyresparser import ResumeParser
import re
# 0.22.2.post1 sklearn version: pip install scikit-learn==0.22.2.post1
# run as su
# text = extract_text('report.pdf')

app=Flask(__name__)

path = "static/Resume/"

classifier = pickle.load(open('finalized_model.sav', 'rb'))
le = pickle.load(open('label_encoder.sav', 'rb'))
tfidf_vectorizer = pickle.load(open('tfidf_vec.sav', 'rb'))
df = pd.read_csv('UpdatedResumeDataSet.csv' ,encoding='utf-8')
jb_roles = list(df['Category'].unique())
role_ids = list(le.transform(jb_roles))
resumes = list(os.listdir(path))
curr_jr = ""

# print(resumes)
col_names = ['name', 'email', 'mobile_number', 'skills', 'college_name', 'degree', 'designation', 
             'experience', 'company_names', 'no_of_pages', 'total_experience', 'raw_resume', 'round1']

def cleanResume(resumeText):
    resumeText = re.sub('http\S+\s*', ' ', resumeText)  # remove URLs
    resumeText = re.sub('RT|cc', ' ', resumeText)  # remove RT and cc
    resumeText = re.sub('#\S+', '', resumeText)  # remove hashtags
    resumeText = re.sub('@\S+', '  ', resumeText)  # remove mentions
    resumeText = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', resumeText)  # remove punctuations
    resumeText = re.sub(r'[^\x00-\x7f]',r' ', resumeText) 
    resumeText = re.sub('\s+', ' ', resumeText)  # remove extra whitespace
    return resumeText


def pred(raw_resume, jr_id):
    raw_resume = cleanResume(raw_resume)
    resume_jr_pred = int(classifier.predict(tfidf_vectorizer.transform([raw_resume]))[0])
    if jr_id == resume_jr_pred:
        return 1
    return 0


def parse(jr_id):
    df_temp = pd.DataFrame(columns=col_names)
    for res in resumes:
        res_path = path + res
        res_str = extract_text(res_path)
        res_data = ResumeParser(res_path).get_extracted_data()
        res_data['raw_resume'] = res_str
        res_data['round1'] = pred(res_str, jr_id)
        df_temp = df_temp.append(res_data, ignore_index = True) 
    #df_temp.to_csv("results.csv")   
    result = []
    for i,j in zip(df_temp['name'],df_temp['round1']):
        if j ==1:
            result.append(i)  
    return result
    #conn = sql.connect('Results.db')
    #df_temp.to_sql('Results', conn, if_exists='replace')


@app.route('/')
@app.route('/index', methods = ['GET', 'POST'])
def index():
    message = "NO"
    if request.method == 'POST':
        select = request.form.get('jbr')
        results = parse(int(select))
        res=[]
        c=1
        for i in results:
            res.append((c,i))
            c+=1
        curr_jr = str(le.inverse_transform([int(select)])[0])
        message = "User Data Base Updated"
        #ind = list(range(len(results)))
        return render_template('result.html',results=res)
    return flask.render_template('index.html', jb_roles=jb_roles, role_ids=role_ids, sizes=len(jb_roles), 
    resumes=resumes, t_heads = ['Index', 'Applicants Resume'], message=message)
    


@app.route('/result', methods = ['GET','POST'])
def result():
    return render_template("result.html")

if __name__ == "__main__":
    app.run(debug=True)