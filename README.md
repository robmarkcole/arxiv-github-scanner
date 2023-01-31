# streamlit-arxiv
Streamlit app for querying the arxiv api. Filter results on validity of Github links, freshness and category, and save to csv. Links will be clickable if the csv is opened in the Mac Numbers application

<p align="center">
<img src="usage.png" width="900">
</p>

## Usage (Mac)
* Create and activate a venv: `python3 -m venv venv` and `source venv/bin/activate`
* Install requirements: `pip install -r requirements.txt`
* `streamlit run app.py`

## References
- [arxiv.py](https://github.com/lukasschwab/arxiv.py)