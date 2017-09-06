from flask import Flask, render_template, request, redirect, url_for, session
from flask.ext.mysql import MySQL
from flask import jsonify

app = Flask(__name__)
app.secret_key = "mySecretKeyStringforThisApp"
# secret key for cookie encription
mysql = MySQL() 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Welcome1'
app.config['MYSQL_DATABASE_DB'] = 'new_schema'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
# database connection

# patient page
@app.route("/patientPage")
def patientPage():
	if 'username' not in session:
		return redirect(url_for('showSignIn')) 
	if session['userType'] != "1":
		return "you do not have access to this page"
	cursor.execute("SELECT documentId,documentType, requesterId FROM approvals where patientId = %s and status = %s",[int(session['personaId']),1])
	data=cursor.fetchall()
	return render_template('approvePage.html', docs = data)

# end point for approval of document view request
@app.route("/approve")
def approve():
	if 'username' not in session:
		return redirect(url_for('showSignIn')) 
	if session['userType'] != "1":
		return "you do not have access to this page"
	docId = request.args.get('documentId', type=int)
	cursor.execute("update approvals set status = %s where documentId = %s and patientId = %s",[2,docId,int(session['personaId'])])
	
	conn.commit()
	return {"approved"}

#doctor page
@app.route("/doctorPage")
def doctorPage():
	if 'username' not in session:
		return redirect(url_for('showSignIn')) 
	if session['userType'] != "2":
		return "you do not have access to this page"
	query = "SELECT * FROM patient"
	cursor.execute(query)
	patientdata=cursor.fetchall()
	return render_template('submitPage.html', patients = patientdata)

#end point for lead selection handling of master list(master detail behaviour)
@app.route("/selectPatient")
def selectPatient():
	if 'username' not in session:
		return redirect(url_for('showSignIn')) 
	if session['userType'] == "1":
		return "you do not have access to this page"
	patientId = request.args.get('patientId', type=int)
	approvedDocs = []
	unvisitedDocs = []
	allDocuments = []
	approvedDocuments = []
	if session['userType'] == "2":
		cursor.execute("select * from records where patientId = %s",[patientId])
		allDocuments=cursor.fetchall()
		cursor.execute("select documentId from approvals where patientId = %s and requesterId = %s and status = %s and documentType = %s",[patientId, int(session['personaId']),2,1])
		approvedDocuments=cursor.fetchall()			
	elif session['userType'] == "3":
		cursor.execute("select * from prescription where patientId = %s",[patientId])
		allDocuments=cursor.fetchall()
		cursor.execute("select documentId from approvals where patientId = %s and requesterId = %s and status = %s and documentType = %s",[patientId, int(session['personaId']),2,2])
		approvedDocuments=cursor.fetchall()
	for doc in allDocuments:
		if approvedDocuments and doc[0] in approvedDocuments[0]:
			#appr[0] = doc[0]
			#appr[1] = doc[3]
			#appr[2] = doc[2]
			approvedDocs.append([doc[0],doc[3],doc[2]])
		else:
			#unappr[0] = doc[0]
			#unappr[1] = doc[3]
			unvisitedDocs.append([doc[0],doc[3]])
	return jsonify(result=[approvedDocs,unvisitedDocs])
	
#pharmacist page
@app.route("/pharmaPage")
def pharmaPage():
	if 'username' not in session:
		return redirect(url_for('showSignIn')) 
	if session['userType'] != "3":
		return "you do not have access to this page"
	
	query = "SELECT * FROM patient"
	cursor.execute(query)
	patientdata=cursor.fetchall()
	return render_template('submitPage.html', patients = patientdata)

# endpoint for submitting documents for apporval 
@app.route("/submitForApproval")
def submitForApproval():
	if 'username' not in session:
		return redirect(url_for('showSignIn')) 
	if session['userType'] == "1":
		return "you do not have access to this page"
	patientId = request.args.get('patientId', type=int)
	documentId = request.args.get('documentId', type=int)
	if session['userType'] == "2":
		cursor.execute("select documentId from approvals where patientId = %s and requesterId = %s and documentType = %s and documentId = %s",[patientId,int(session['personaId']),1,documentId])
		doc=cursor.fetchone()
		if doc:
			return {"already submited"}						
		else:
			cursor.execute("insert into approvals values (%s,%s,%s,%s,%s)",[patientId,int(session['personaId']),1,documentId,1])
			conn.commit()
	elif session['userType'] == "3":
		cursor.execute("select documentId from approvals where patientId = %s and requesterId = %s and documentType = %s and documentId = %s",[patientId,int(session['personaId']),2,documentId])
		doc=cursor.fetchone()
		if doc:
			return {"already submited"}					
		else:
			cursor.execute("insert into approvals values (%s,%s,%s,%s,%s)",[patientId,int(session['personaId']),1,documentId,2])
			conn.commit()
	return {"success"}

#log in page
@app.route('/showSignIn')
def showSignIn():
    return render_template('signin.html')

# login and start a new sessions
@app.route('/logPage', methods=['POST'])
def logPage():
	userName = request.form['inputName']
	password = request.form['inputPassword']
	if not userName == '' and not password == '':
		cursor.execute("select userType, personaId from usermaster where userName = %s AND password = %s", [userName, password])
		data=cursor.fetchone()
		if data:
			#starting new session
			if 'username' in session:
				session.pop('username', None)
				session.pop('userType', None)
				session.pop('personaId', None)
			session['username'] = userName
			session['userType'] = data[0]
			session['personaId'] = data[1]
			if data[0] == "1":
				return redirect(url_for('patientPage'))
			elif data[0] == "2":
				return redirect(url_for('doctorPage'))
			elif data[0] == "3":
				return redirect(url_for('pharmaPage'))
				
	error = "invalid credentials"
	return render_template('signin.html', error = error)

@app.route('/logoutPage', methods=['POST'])
def logoutPage():
	session.pop('username', None)
	session.pop('userType', None)
	session.pop('personaId', None)
	return redirect(url_for('showSignIn'))


if __name__ == "__main__":
	app.run()