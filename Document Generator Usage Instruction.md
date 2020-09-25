# Document Generator Usage Instruction



## DOI Citation

- **Front-End**:  [![DOI](https://zenodo.org/badge/281585398.svg)](https://zenodo.org/badge/latestdoi/281585398)

- **Back-End**:  [![DOI](https://zenodo.org/badge/275757098.svg)](https://zenodo.org/badge/latestdoi/275757098)



## Usage Instruction

### [Back-End](https://github.com/FudanSELab/doc-generate)

1. Install prerequisites 

```
python==3.6.8
nltk==3.4.5
sekg==0.10.3.18
Flask==1.1.2
gunicorn==20.0.4
flask_cors==3.0.8
```

2. Run the Service


```shell
# You can simply typing the following command to start the service on server or localhost
gunicorn -b localhost:5000 run:app
```

### [Front-End](https://github.com/FudanSELab/doc_gen_front_end)

1.Dependencies

```
axios: 0.19.2
d3: 5.16.0
element-ui: 2.13.2
jquery: 3.5.1
vue: 2.5.2
vue-router: 3.4.0
```

2.Run and Build

```shell
# install dependencies
npm install

# serve with hot reload at localhost:8080
npm run dev

# build for production with minification
npm run build

# build for production and view the bundle analyzer report
npm run build --report
```