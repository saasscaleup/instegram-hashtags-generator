#!/usr/bin/python3.9

import urllib3
import boto3
import base64

rekognition     = boto3.client("rekognition")
http            = urllib3.PoolManager()
        
class Hashtags():
    """Hashtags class: image coming from the GET event and analyzed with AWS Rekognition
        
        REQUEST:
            - image_url [string]     : image url | required
            - name [string]          : image name
            - max_labels [int]       : max number of labels to detect
            - min_confidence [int]   : confidence threshold

    """

    def __init__(self, event):
        
        # check if the `event` contain Get parameters
        if "queryStringParameters" not in event:
            
            body = {
                "message": "[ERROR]: Query string parameters are missing! Please try new GET request with QUERY PARAMS",
                "success": False,
                "request": event
            }
            
            self.response       = Response._response(400,body)
            
        else:
            
            self.event          = event
            
            # Set request parameters
            self.name           = event["queryStringParameters"]["name"] if 'name' in event["queryStringParameters"] else 'test name'
            self.image_url      = event["queryStringParameters"]["image_url"] if 'image_url' in event["queryStringParameters"] else 'test url'
            self.max_labels     = int(event["queryStringParameters"]["max_labels"]) if 'max_labels' in event["queryStringParameters"] else 20
            self.min_confidence = int(event["queryStringParameters"]["min_confidence"]) if 'min_confidence' in event["queryStringParameters"] else 75
            
            # Download image from link as base 64
            self.image_base64   = self.get_as_base64()
            
            # Run AWS Rekognition (AI) detect_labels
            self.labels         = self.detect_labels()
            
            # Generate labels as instagram hashtags
            self.hashtags       = self.parse_labels()
            
            # Set proper response
            self.response       = self.parse_response()
        
    def get_as_base64(self):
        
        try:
            image_download = http.request('GET',self.image_url)
        except:
            print('get_as_base64 error:', e)
            return False
        
        return base64.b64encode(image_download.data)
        
    def detect_labels(self):
        '''Call to AWS Rekognition for object detection'''
        
        print("Call to AWS Rekognition for object detection on image '{}'".format(self.name))
        
        labels = []
        
        if (self.image_base64==False):
            return labels
        
        try:
            
            response = rekognition.detect_labels(
              Image = {
                "Bytes": base64.b64decode(self.image_base64)
              },
              MaxLabels = self.max_labels,
              MinConfidence = self.min_confidence
            )
            
        except Exception as e:
            print('rekognition error:', e)
            return labels
        
        if "Labels" in response.keys():
            for obj in response["Labels"]:
                labels.append({"name": obj["Name"],"confidence": obj["Confidence"]})
        
        return labels
     
    def parse_labels(self):
        hashtags = []
    
        for obj in self.labels:
            hashtag = obj["name"].lower().replace(' ','_')
            hashtags.append("#"+hashtag)
            
        return hashtags
    
    def parse_response(self):
        
        # If no labels generated -> return error
        if not self.hashtags:
            
            http_code = 400
            body = {
                "message": "[ERROR]: Please try again with different image url or make sure image is available for download",
                "success": False,
                "request": self.event["queryStringParameters"]
            }

        # If labels generated -> return hashtags
        else:
            http_code = 200
            body = {
                "message": "Object {} analyzed successfully!".format(self.name),
                "success": True,
                "labels": self.labels,
                "hashtags": self.hashtags
            }
            
        return Response._response(http_code,body)


# Helper class to refactore response messages
class Response():
    def _response(http_code, body):
        return {
            "headers": {'Content-Type': 'application/json'},
            "statusCode": http_code,
            "body": body
        }


# main lambda handler - Code excute here
def lambda_handler(event, context):
    '''Method run by Lambda when the function is invoked''' 
    
    # calling Hashtags calss and invoke hastags detect
    result = Hashtags(event)
    
    # return response 
    return result.response
