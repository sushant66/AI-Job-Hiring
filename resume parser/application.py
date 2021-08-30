from flask import Flask, render_template
from flask import jsonify
import json
import requests
#from flask_cors import CORS
#from flask_cors import cross_origin
from flask import request
from pyresparser import ResumeParser
import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

application = Flask(__name__,template_folder='template')
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
application.config['SESSION_TYPE'] = 'filesystem'
application.secret_key = "f3cfe9ed8fae309f02079dbf"
# print a nice greeting.
@application.route("/")
def hello():
    data = {'name': 'name', 'email':'email', 'mobile_number':'phone no','degree':'degree','skills':'skills'}
    return render_template('index.html', data=data)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@application.route('/parse_resume', methods=['GET','POST'])
def parse_resume():
    #print(request.form)
    print("hello", request.method)
    
    if request.method == 'POST':
        print("IN POST")
        
        if 'file' not in request.files:
            flash('No file part')
            print('NO')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        print(file)
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
            os.rename('uploads/'+file.filename,'uploads/resume.pdf')
            data = ResumeParser('uploads/resume.pdf').get_extracted_data()
            os.remove('uploads/resume.pdf')
            print(data["email"])
            return render_template('index.html', data=data)
    return 'NO'#render_template('index.html')
        

    

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()
