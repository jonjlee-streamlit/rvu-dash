# Start streamlit in virtual environment. 
# To run interactively without script, be sure to first: pipenv shell
# Disable CORS and Xsfr protection per https://github.com/orgs/community/discussions/18038
pipenv run streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false