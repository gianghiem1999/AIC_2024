<pre>
System/
|---clip_model/
|---csv_data/
|---keyframes/
    |---L01_V001/
    |-----/
|---map/
|---result/
</pre>
Resource link: https://drive.google.com/file/d/1TiNs1tXzLbXTk34UPbMwpleZWRq3Zsy3/view?usp=drive_link
<Br>
Use Python 3.10.18
<Br>
Using Anaconda and Install separated environment: 
```
conda create -n AIC python==3.10.18
```
```
pip install numpy torch torchvision torchaudio pandas
pip install transformers scikit-learn python-socketio eventlet
pip install PyQt5 googletrans==4.0.0-rc1 spacy
```
```
python -m spacy download en_core_web_sm
```
```
python server.py
```
```
python app.py
```
