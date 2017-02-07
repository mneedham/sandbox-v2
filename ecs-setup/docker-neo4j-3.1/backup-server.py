import SimpleHTTPServer
import SocketServer
import urlparse
import os
import subprocess
import boto3
import time
import json

AWS_ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
AWS_ACCESS_SECRET = os.environ['AWS_ACCESS_SECRET']
AWS_S3_BACKUP_BUCKET = os.environ['AWS_S3_BACKUP_BUCKET']

class port_http_handler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        global AWS_ACCESS_KEY, AWS_ACCESS_SECRET, AWS_S3_BACKUP_BUCKET

        parsedParams = urlparse.urlparse(self.path)
        queryParsed = urlparse.parse_qs(parsedParams.query)
        responseCode = 500

        if 'sandbox' in queryParsed.keys():
            if 'SANDBOX_HASHKEY' in os.environ.keys() and queryParsed['sandbox'][0] == os.environ['SANDBOX_HASHKEY']:
                responseStr = "Initiating backup\n\n"
                responseStr = responseStr + subprocess.check_output(["/var/lib/neo4j/bin/neo4j-backup", "-host", "localhost", "-to", "/db-backup/"])
                responseStr = responseStr + subprocess.check_output(["zip", "-r", "/db-backup.zip", "/db-backup"])
                awssession = boto3.Session(
                    aws_access_key_id=AWS_ACCESS_KEY,
                    aws_secret_access_key=AWS_ACCESS_SECRET
                )
                s3 = awssession.resource('s3')
                s3.meta.client.upload_file('/db-backup.zip', AWS_S3_BACKUP_BUCKET, '%s-%s.zip' % (os.environ['SANDBOX_HASHKEY'], time.time()))
                responseCode = 200
                responseJson = {
                  "STATUS": "SUCCESS",
                  "LOG": responseStr
                }
                response = json.dumps(responseJson)
            else:
                response = "Unauthorized"
                responseCode = 403
        else:
            response = "ERROR - no sandbox sent"
            responseCode = 404
        self.send_response(responseCode)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-length", len(response))
        self.end_headers()
        self.wfile.write(response)

PORT = 9500

httpd = SocketServer.TCPServer(("", PORT), port_http_handler)

print "serving at port", PORT
httpd.serve_forever()
