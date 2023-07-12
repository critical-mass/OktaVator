import json
import time
import boto3
import urllib3
from time import sleep
from datetime import datetime, timedelta
import dateutil.tz


##To do for script##
#1.Clean up database after post request 

def lambda_handler(event, context):
    
    #Load our dyanmoDB resource & point it to our table
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table('OktaVator')
    
    #setup urllib
    http = urllib3.PoolManager()
    
    #Stream all db results and load the "Items" into a json object
    results = table.scan()
    a=(json.dumps(results))
    b=(json.loads(a))
    data=(b["Items"])
    
    #Functions
    def check_time(input_time):
        # Convert input timestamp string to datetime object
        t = datetime.strptime(input_time, "%a %b %d %H:%M:%S %Z%z %Y")
        
        #get current time
        UTC = dateutil.tz.gettz('UTC')
        now = datetime.now(tz=UTC)
        
        # Compare input time and current time
        if t < now:
            return(True)
        else:
            return(False)

    def get_secret(y):
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(
            SecretId=(y)
        )
        database_secrets = json.loads(response['SecretString'])
        return(database_secrets)
    
    def activate_account(url, apiKey, email, userId):
        headers = {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': 'SSWS ' + apiKey
        }
        searchUrl=(url + "api/v1/users/" + userId + "/lifecycle/activate?sendEmail=false")
        print(searchUrl)
        searchBody = http.request('POST', searchUrl, body="", headers=headers, retries = False)
        print(searchBody)

    def suspend_account(url, apiKey, email, userId):
        headers = {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': 'SSWS ' + apiKey
        }
        suspendUrl=(url + "api/v1/users/" + userId + "/lifecycle/suspend")
        http.request('POST', url=suspendUrl, body="", headers=headers, retries = False)
    
    def clear_db_row(email):
        table.delete_item(Key={
            'email': email
        })
    
    #Loop through all items in the list
    for x in data:
        
        c = json.dumps(x)
        e = json.loads(c)
        
        print("---------------------------")
        print("Username: " + (e["email"]))
        print("Client: " + (e["client"]))
        print("Time: " + (e["time"]))
        print("---------------------------")
        
        input_time = e["time"]
        email = e["email"]
        userId = e["userId"]
        
        
        #Logic to take action on the account
        if check_time(input_time) == True:
            print("Time elapsed!")
            
            #Get our data and defind our vars
            databaseSecrets = get_secret(e["client"])
            url = databaseSecrets["url"]
            apiKey = databaseSecrets["apiKey"]
            emailDomain = databaseSecrets["emailDomain"]
            
            #Check if the data is for an on or offboarding
            if e["interactionType"] == "Onboarding":
                print("onboarding user")
                activate_account(url=url, apiKey=apiKey, email=email, userId=userId)
                clear_db_row(email=email)
            elif e["interactionType"] == "Offboarding":
                print("offboarding user")
                suspend_account(url=url, apiKey=apiKey, email=email, userId=userId)
                clear_db_row(email=email)
        elif check_time(input_time) == False:
            print("Interaction time not elapsed! No action being taken")
        
        else:
            print("Oktavator broken")