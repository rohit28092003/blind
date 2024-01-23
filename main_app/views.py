from django.shortcuts import render,redirect
import requests
import json
import base64
import time

# Create your views here.
def default(request):
    return render(request,'loggedIn.html')

def index(request):
    return render(request,'index.html')
#
#def login(request):
#    pass
from django.shortcuts import render
from django.http import JsonResponse,HttpResponseRedirect,HttpResponse
from .models import Userdata,Question,ActivityLog
from django.contrib.auth import logout
import json

from django.contrib.auth.decorators import login_required





def submit_question(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        user = request.user
        print(f"User ID: {user.id}")

        question = Question.objects.get(qno=data['qNo'])
        input_data = "";

        source_code = data['source_code']

        # Assuming you have a function to map language names to language IDs
        language_id = data['language']

        # Submit code and get the result
        result = submit_code(source_code, input_data, language_id)

        # Save the log
        log_entry = ActivityLog(
            user=user,
            question=question,
            source_code=source_code,
            input_data=input_data,
            output=result
        )
        log_entry.save()

        # Prepare the response
        response_data = {
            'output': result,
            'timestamp': log_entry.timestamp
        }

        return JsonResponse(response_data)

    return HttpResponse("Invalid request method", status=400)


def submit_code(source_code, input_data, language_id):
    # lang codes
    # 71 - Python
    # 50 - C
    # 54 - C++
    # 62 - Java
    
    headers = {
        "content-type": "application/json",
        "accept": "application/json",
    }

    submission_url = "http://localhost:2358/submissions"
    submission_payload = {
        "source_code": source_code,
        "stdin": input_data,
        "language_id": language_id,
    }

    submission_response = requests.post(submission_url, headers=headers, json=submission_payload)
    submission_data = submission_response.json()
    token = submission_data.get("token")

    if not token:
        return "Error creating submission."

    output_url = f"http://localhost:2358/submissions/{token}?base64_encoded=true"
    output_data = {}


    # Checking submission status
    status_description = "Queue"
    while status_description != "Accepted":
        if "Error" in status_description:
            return f"Error: {status_description}"
        print(f"Checking Submission Status\nstatus: {status_description}")
        output_response = requests.get(output_url, headers=headers)
        output_data = output_response.json()
        status_description = output_data.get("status", {}).get("description")
        time.sleep(1)

    if output_data.get("stdout"):
        output = base64.b64decode(output_data["stdout"]).decode("utf-8")
        dat =  f"Results:\n{output}\nExecution Time: {output_data['time']} Secs\nMemory Used: {output_data['memory']} bytes"
        print(dat)
        return output
    elif output_data.get("stderr"):
        error = base64.b64decode(output_data["stderr"]).decode("utf-8")
        return f"Error: {error}"
    else:
        compilation_error = base64.b64decode(output_data["compile_output"]).decode("utf-8")
        return f"Error: {compilation_error}"

def login(request):
#	if request.POST:
	return redirect('/accounts/google/login')
#	return render(request,'index.html')

@login_required(login_url='/')
def main(request):
   return render(request, 'loggedIn.html',)

def question(request):
	data = json.loads( request.body.decode('utf-8') )
	num = data['queNum']
	print(data)
	ques = Question.objects.get(qno=num)
	question = ques.text
	sampleTestCaseNum = ques.testcaseno
	sampleIn = ques.samplein
	sampleOut = ques.sampleout
	res={}
	res['question'] = question
	res['qNo'] = num
	res['sampTCNum'] = sampleTestCaseNum
	res['sampIn'] = sampleIn
	res['sampleOut'] = sampleOut
	res['userScore'] = Userdata.objects.get(user_id = request.user).score
	print('hi')
	print(res['userScore'])
	return HttpResponse(json.dumps(res))
	
 
 
 
 
def runCode(request):
    postData = json.loads(request.body.decode('utf-8'))
    print(postData)

    que = Question.objects.get(qno=postData['qNo'])
    postData['stdin'] = '3'+'\n'+que.test_case1+'\n'+que.test_case2+'\n'+que.test_case3

    # Assuming you have a function to map language names to language IDs
    language_id = postData['language']  

    resp = submit_code(postData['source_code'], postData['stdin'], language_id)

    print(postData['qNo'])
    print(resp)
    print(resp['output'])

    res = {}
    if 'error' in resp['output'].lower():
        res['output'] = resp['output']
    else:
        quesData = Question.objects.get(qno=postData['qNo'])
        answer = quesData.test_case1_sol+'\n'+quesData.test_case2_sol+'\n'+quesData.test_case3_sol+'\n'
        print(answer)

        currUser = Userdata.objects.get(user_id=request.user)
        currUser.timeElapsed += int(postData['timeElapsed'])

        if answer == resp['output']:
            print('hurray')
            res['output'] = 'Correct Answer'
            print(currUser.answerGiven)
            lst = list(currUser.answerGiven)
            print(lst)
            if lst[postData['qNo']] == '0':
                print('qwer')
                currUser.score += 10
                currUser.save()
            lst[postData['qNo']] = '1'
            currUser.answerGiven = "".join(lst)
        else:
            res['output'] = 'Wrong answer..'

        currUser.save()
        res['score'] = currUser.score

    return HttpResponse(json.dumps(res))

# def runCode(request):
# 	postData = json.loads( request.body.decode('utf-8') )
# 	print(postData)
 
 
# 	url = 'https://api.jdoodle.com/execute/'
# 	que = Question.objects.get(qno=postData['qNo'])
# 	postData['stdin'] = '3'+'\n'+que.test_case1+'\n'+que.test_case2+'\n'+que.test_case3
# 	response = requests.post(url,json=postData)
# 	resp = response.json()
# #	resp = json.loads(resp)
# 	print(postData['qNo'])
# 	print(resp)
# 	print(resp['output'])
# 	res = {}
# 	if resp['output'].find('error') != -1:
# 		res['output'] = resp['output']
# 	else:
# 		quesData = Question.objects.get(qno=postData['qNo'])
# 		answer = quesData.test_case1_sol+'\n'+quesData.test_case2_sol+'\n'+quesData.test_case3_sol+'\n'
# 		print(answer)
# 		currUser = Userdata.objects.get(user_id = request.user)
# 		currUser.timeElapsed += int(postData['timeElapsed'])
# 		if answer == resp['output']:
# 			print('hurray')
# 			res['output'] = 'Correct Answer'
# 			print(currUser.answerGiven)
# 			lst = list(currUser.answerGiven)
# 			print(lst)
# 			if(lst[postData['qNo']] == '0'):
# 				print('qwer')
# 				currUser.score+=10
# 				currUser.save()
# 			lst[postData['qNo']] = '1';
# 			currUser.answerGiven="".join(lst)
			
# 		else:
# 			res['output'] = 'Wrong answer..'
			
# 		currUser.save()
# 		res['score'] = currUser.score
# 	return HttpResponse(json.dumps(res))

def l_out(request):
    logout(request)
    return render(request,'index.html')