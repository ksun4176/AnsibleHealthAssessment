# AnsibleHealthAssessment
Create a Google Doc based on a Markup file.
This will preserve the following formats:
- Main title = Heading 1 style
- Section headers = Heading 2 style
- Sub-section headers = Heading 3 style
- Nested lists with proper indentation
- Checkboxes
- Mentions will be in bold
- Footer will be in italics

# Required Dependencies
- Python 3.10.7 or greater
- The pip package management tool
- A Google Cloud project
- A Google Account

## Set Up
1. Create a Google Cloud project
2. Go to Branding and set up the app to allow authentication
3. Go to Clients and set up a OAuth 2.0 Client for Web application
  - This will generate a Client secrets file (download this)
4. Add `http://localhost:9000` as an Authorized redirect URI
5. Rename your Clients secrets file to `credentials.json` and move to the same folder a `AnsibleHealthAssessment.py`
  - .gitignore is set up to not save your credentials
6. Go to Data Access and add `/auth/documents` to the scope
7. Run `pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib` to install python dependencies

## How to Run
1. Run `python AnsibleHealthAssessment.py`
2. This will launch in your browser a log in page for a Google Account
3. Go through the steps and allow access to Google Doc
4. After program has finished running, you can go into your Google Doc and find the newly created `AnsibleHealthTest` file
5. Open the file and you will see the formatted Markup file as a Google Doc