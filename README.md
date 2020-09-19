# dcoh

## What is this

This software is to deceive the communication of HTTP(S).  
The reason for making is to debug API and hack API to do.  

## Getting Started

This project was created to deceive the communication of HTTP(S).  
To use this project so see "Installing" and "Usage" section.  

### Prerequisites

This software to use needs prepares, the environment for executing a Python.  
Further, need to install bellow packages so written in requirements.txt.  

* requests 
    - `>= 2.20.1`

### Installing
To usage so clone the repository and set up the CA root.  
Enter the bellow command line to installing.  

```bash
git clone https://github.com/fealone/dcoh
cd dcoh
pip install -r requirements.txt
cd CA
./init.sh # Setup the CA root
```

Default DN is this.

```
C = "JP"
ST = "Tokyo"
L = "Minato-ku"
O = "dcoh"
OU = "dcoh"
```

If you need to change DN then change settings.py.

### Usage 
To using try to enter the bellow command line.  

```bash
cd dcoh
python main.py
```

#### How to deceive
Create the contents you want to deceive.  
If a path has an end of a slash then, add "index.html" to the end.  

`dcoh/contents/{domain}/{url}`

For example

`dcoh/contents/www.google.com/index.html`

#### How to use custom script
Create the Python script you want to change response and request.
The path to deploy is to add extension ".py" to the contents path.  
Also, different from the content is if a path has an end of a slash then, it doesn't add "index.html" to the end.  

For example  

* Path

`dcoh/contents/www.google.com/.py`

* Script

```python
from typing import Any, Dict, Generator

from lib.content_object import ContentObject
from lib.delegate_object import DelegateObject
import requests


class Delegate(DelegateObject):

    # Can change requests if you need to deceive to request.
    # This method is optional.
    def get_request(self) -> requests.Request:
        if self.request_payload:
            req = requests.Request(self.headers["method"],
                                   f"{self.protocol}://{self.target}{self.headers['url']}",
                                   headers=self.header,
                                   data=self.request_payload)
        else:
            req = requests.Request(self.headers["method"],
                                   f"{self.protocol}://{self.target}{self.headers['url']}",
                                   headers=self.header)
        return req

    # Can change responses if you need to deceive to a response.
    # This method is optional.
    def get_response(self, response: requests.Response) -> "ResponseObject":
        return ResponseObject(response, self.header)


class ResponseObject(ContentObject):

    # Can use this property if you need to change any headers.
    # This property is optional.
    @property
    def headers(self) -> Dict[str, Any]:
        return self.res.headers

    # Can use this property if you need to change the status code.
    # This property is optional.
    @property
    def status_code(self) -> int:
        return self.res.status_code

    # Can use this method if you explicitly specify content size.
    # This property is optional.
    def size(self) -> int:
        # If return content size then selected "Content-Length".
        return self.res.headers["Content-Length"]
        # If return None then selected "Transfer-Encoding: chunked".
        return None

    def stream(self) -> Generator[bytes, None, None]:
        for line in self.res.raw:
            yield line
```

Also, a script has priority over content.  

#### How to use proxy in Google Chrome

If you use in Google Chrome then set options this.

```
--proxy-server="https=127.0.0.1:8443;http=127.0.0.1:8080"
```

You can divide a session if you use these options.

```
--user-data-dir="{UserConfigDirectory}"
```

## Authors

* **fealone**

See also the list of [contributors](https://github.com/fealone/dcoh/contributors) who participated in this project.

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details
