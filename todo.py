from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re

DATA_KEY_EVENTS = "events"
data = {
    DATA_KEY_EVENTS: []
}

REG_RFC3339 = r"^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9]|60)?(\.[0-9]+)?(Z|(\+|-)([01][0-9]|2[0-3]):([0-5][0-9]))$"
reg_date = re.compile(REG_RFC3339)

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path_elements = parsed_path.path.split('/')[1:]
        result = {}
        code = -1

        if (not self.valid_path(path_elements)):
            self.send_response(404)
            self.end_headers()
            return
        
        try:
            content_len = int(self.headers.get('content-length'))
            event = json.loads(self.rfile.read(content_len).decode('utf-8'))
        except Exception as e:
            print(e)
            self.send_response(500)
            self.end_headers()
            return

        
        error_message = self.validate_event(event)
        if (error_message == ""):
            id = self.__register_event(event)
            result = {"deadline": "success", "message": "registered", "id": id}
            code = 200
        else:
            result = {"deadline": "failure", "message": error_message}
            code = 400

        self.res(code, result)
        return

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path_elements = parsed_path.path.split('/')[1:]
        
        if (not self.valid_path(path_elements)):
            self.send_response(404)
            self.end_headers()
            return

        
        if(len(path_elements) > 3):
            try:
                id = int(path_elements[3])
                self.__get_event(int(path_elements[3]))
            except ValueError as e:
                print(e)
                self.send_response(400)
                self.end_headers()
                
        else:
            self.res(200, data)    
        return
    
    def res(self, code, dic = None):
        try:
            self.send_response(code)
            self.end_headers()
            if (dic != None):
                j_son = json.dumps(dic)
                self.wfile.write('{}\n'.format(j_son).encode('utf-8'))
        except Exception as e:
            print(e)
            self.send_response(500)
            self.end_headers()
        return
    
    def valid_path(self,path_elements):
        if (len(path_elements) < 3):
            return False
        return path_elements[:3] == ["api", "v1", "event"]

    def __get_event(self, id):
        events = data[DATA_KEY_EVENTS]
        if (id < 0 or len(events) <= id):
            self.send_response(404)
            self.end_headers()
        else:
            self.res(200, events[id])
        return
        
    def validate_event(self, event):
        event_keys = event.keys()
        if (("deadline" or "title") not in event_keys):
            return "invalid event format"
        
        date = event["deadline"]
        if(reg_date.match(date) == None):
            print(date)
            return "invalid date format"

        return ""

    def __register_event(self, event):
        events = data[DATA_KEY_EVENTS]
        id = len(events)
        event["id"] = id
        events.append(event)

        return id

def main():
    server = HTTPServer(('', 8080), RequestHandler)
    server.serve_forever()
        

if __name__ == "__main__":
    main()