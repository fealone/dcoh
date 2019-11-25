# dcoh

## What is this

This software is to deceive the communication of HTTPS.  
The reason for making is to debug API and hack API to do.  

## Getting Started

This project was created to deceive the communication of HTTPS.  
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

`dcoh/contents/{domain}/{url}`

For example

`dcoh/contents/www.google.com/index.html`

## After this
* Support HTTP protocol
* Support custom contents with Python script.

## Authors

* **fealone**

See also the list of [contributors](https://github.com/fealone/dcoh/contributors) who participated in this project.

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details
