# OpenAPIDocGen2 Backend
[![DOI](https://zenodo.org/badge/275757098.svg)](https://zenodo.org/badge/latestdoi/275757098)

This is backend source code of OpenAPIDocGen2 . OpenAPIDocGen2 is a tool that generates on-demand class documentation based source code and documentation analysis. For a given class, OpenAPI- DocGen2 generates a combined documentation for it, which includes functionality descriptions, directives, domain concepts, usage examples, class/method roles, key methods, relevant classes/methods, characteristics and concepts classification, and usage scenarios.
This project has been accepted to the ICSME 2020 DocGen2 Tool Demo track. You can visit our project demo by this link: [OpenAPIDocGen2](http://106.14.239.166:8080/DocGen/index.html#/)

## Getting Started

### Prerequisites

```
python==3.6.8
nltk==3.4.5
sekg==0.10.3.18
Flask==1.1.2
gunicorn==20.0.4
flask_cors==3.0.8
networkx==2.5
```

## Running the Service

You can simply typing the following command to start the service on server or localhost

```
gunicorn -b localhost:5000 run:app
```

## Contributors

* Mingwei Liu
* Xiujie Meng
* Huanjun Xu
* Shuangshuang Xing
* Xin Wang
* Yang Liu
* Gang Lv


## License

This project is licensed under the MIT License.
