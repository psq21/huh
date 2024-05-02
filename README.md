
# huh


## setup 
```
# activate venv (optional)
python -m venv venv
source venv/Scripts/activate # or the equivalent in your OS

# install deps
pip install -r requirements.txt

# run
python app.py
# or with different host and port
env HUH_HOST=localhost HUH_PORT=8080 python app.py
```

format python files: ``black .``
format html: ``djlint . --reformat``
