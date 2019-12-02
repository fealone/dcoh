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
Create the Python script you want to change response.  
The path to deploy is to add extension ".py" to the contents path.  
Also, different from the content is if a path has an end of a slash then, it doesn't add "index.html" to the end.  

For example  

`dcoh/contents/www.google.com/.py`

Also, a script has priority over content.  

## Authors

* **fealone**

See also the list of [contributors](https://github.com/fealone/dcoh/contributors) who participated in this project.

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details
