import re
from enum import Enum
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/documents']

def auth_services():
  """Authenticate the Docs API service.

  Returns:
    Docs API service
  """
  flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
  
  creds = flow.run_local_server(port=9000)
  return build('docs', 'v1', credentials=creds)

def create_doc(service, title: str) -> str | None:
  """Create a new Google Doc

  Args:
    service : The Docs API service
    title (str): The title for the Google Doc

  Returns:
    str: The Google Doc ID
  """
  document_id = None
  try:
    body = {
        'title': title
    }
    doc = service.documents().create(body=body).execute()
    print(f'Created document with title: {doc.get('title')}')
    document_id = doc.get('documentId')
  except HttpError as err:
    print(err)

  return document_id

class HeadingStyle(Enum):
  NORMAL = 'NORMAL_TEXT'
  ONE = 'HEADING_1'
  TWO = 'HEADING_2'
  THREE = 'HEADING_3'
def get_heading_style(heading_style: HeadingStyle, start_index: int, end_index: int):
  """Get the UpdateParagraphStyle to format a paragraph as specified heading

  Args:
    heading_style (HeadingStyle): The heading style ot format to
    start_index (int): Start index of range
    end_index (int): End index of range

  Returns:
    dict: UpdateParagraphStyle
  """
  return {
    'updateParagraphStyle': {
      'range': {
        'startIndex': start_index,
        'endIndex': end_index
      },
      'paragraphStyle': {
        'namedStyleType': heading_style.value,
      },
      'fields': 'namedStyleType'
    }
  }

def get_list_style(start_index: int, end_index: int, is_checklist: bool = False):
  """Get the UpdateParagraphStyle to format a paragraph as a list

  Args:
    start_index (int): Start index of range
    end_index (int): End index of range
    is_checkbox (bool): Whether this list should be a checklist instead

  Returns:
    dict: UpdateParagraphStyle
  """

  bullet_preset = 'BULLET_CHECKBOX' if is_checklist else 'BULLET_DISC_CIRCLE_SQUARE'

  return {
    'createParagraphBullets': {
      'range': {
        'startIndex': start_index,
        'endIndex': end_index,
      },
      'bulletPreset': bullet_preset
    }
  }

def clear_list_style(start_index: int, end_index: int):
  """Clear the formatting that makes a paragraph a list

  Args:
    start_index (int): Start index of range
    end_index (int): End index of range

  Returns:
    dict: UpdateParagraphStyle
  """
  return {
    'deleteParagraphBullets': {
      'range': {
        'startIndex': start_index,
        'endIndex':  end_index,
      },
    }
  }

class TextStyle(Enum):
  BOLD = 1
  ITALIC = 2
def get_text_style(start_index: int, end_index: int, styles: list[TextStyle]):
  """Get the UpdateTextStyle to format text in a particular style

  Args:
    start_index (int): Start index of range
    end_index (int): End index of range
    styles (list[TextStyle]): The styles to apply

  Returns:
    dict: UpdateTextStyle
  """
  text_style = {}
  fields = []

  for style in styles:
    if (style == TextStyle.BOLD):
      text_style['bold'] = True
      fields.append('bold')
    elif (style == TextStyle.ITALIC):
      text_style['italic'] = True
      fields.append('italic')

  return {
    'updateTextStyle': {
      'range': {
        'startIndex': start_index,
        'endIndex': end_index,
      },
      'textStyle': text_style,
      'fields': ','.join(fields)
    }
  }

def add_text_to_doc(service, document_id: str, full_text: str):
  """Add the formatted Markup text to the Google Doc.
    This will apply the Markup formatting to the Google Doc.

  Args:
    service : The Docs API service
    document_id (str): The Google Doc ID
    full_text (str): The Markup text
  """
  requests = []
  split_text_arr = full_text.split('\n')
  # go through the Markup text in reverse so we can apply formatting easily to each individual line without having to do index computation.
  split_text_arr.reverse()
  
  list_end_index = 0

  footer_done = False

  for line in split_text_arr:
    is_list = False
    is_checkbox = False

    # check if Markup is a heading or a list and remove the Markup formatting characters from line of content
    final_line = line + '\n'
    heading_style = HeadingStyle.NORMAL
    if (re.match(r'#\s+\w+', line)): # HEADING 1
      final_line = re.sub(r'^#\s+', '', line) + '\n'
      heading_style = HeadingStyle.ONE
    elif (re.match(r'##\s+\w+', line)): # HEADING 2
      final_line = re.sub(r'^##\s+', '', line) + '\n'
      heading_style = HeadingStyle.TWO
    elif (re.match(r'###\s+\w+', line)): # HEADING 1
      final_line = re.sub(r'^###\s+', '', line) + '\n'
      heading_style = HeadingStyle.THREE
    elif (re.match(r'\s*\-\s+\[ \]\s+.+', line)): # CHECK LIST
      is_checkbox = True
      matched_spaces = re.match(r'\s*', line)
      # every 2 space is an indent level
      num_tabs = len(matched_spaces.group(0))//2
      final_line = re.sub(r'^\s*\-\s+\[ \]\s+', '\t'*num_tabs, line) + '\n'
    elif (re.match(r'\s*[\*\-]\s+.+', line)): # LIST
      is_list = True
      matched_spaces = re.match(r'\s*', line)
      # every 2 space is an indent level
      num_tabs = len(matched_spaces.group(0))//2
      final_line = re.sub(r'^\s*[\*\-]\s+', '\t'*num_tabs, line) + '\n'
      # need to update style of entire nested list as a whole so nesting is preserved correctly
      list_end_index += len(final_line)

    # past beginning of list so we can apply the styling
    if (not is_list and list_end_index > 0):
      requests.append(get_list_style(1, list_end_index))
      list_end_index = 0

    # add line of content
    requests.append({
      'insertText': {
        'location': {
          'index': 1,
        },
        'text': final_line
      }
    })
    # apply heading style first so we can override with any text specific ones
    requests.append(get_heading_style(heading_style, 1, len(final_line)))
    # if mentions found, apply bold style
    if (re.search(r'@\w+', final_line)):
      mentions = re.finditer(r'@\w+', final_line)
      for mention in mentions:
        mention_indices = mention.span(0)
        requests.append(get_text_style(mention_indices[0]+1, mention_indices[1]+1, [TextStyle.BOLD]))
    # if still in footer, apply italic style
    if (not footer_done):
      if (final_line == "---\n"): # separator for footer
        footer_done = True
      else:
        requests.append(get_text_style(1, len(final_line), [TextStyle.ITALIC]))

    if (is_checkbox): # if line is a checklist, apply checklist style
      requests.append(get_list_style(1, len(final_line), True))
    elif (not is_list and list_end_index == 0): # otherwise, make sure to clear list style altogether so it doesn't bleed upwards
      requests.append(clear_list_style(1, len(final_line)))

  try:
    service.documents().batchUpdate(documentId=document_id, body={ 'requests': requests }).execute()
    print('Added text to document')
  except HttpError as err:
    print(err)


sample_md = """# Product Team Sync - May 15, 2023
## Attendees
- Sarah Chen (Product Lead)
- Mike Johnson (Engineering)
- Anna Smith (Design)
- David Park (QA)
## Agenda
### 1. Sprint Review
* Completed Features
  * User authentication flow
  * Dashboard redesign
  * Performance optimization
    * Reduced load time by 40%
    * Implemented caching solution
* Pending Items
  * Mobile responsive fixes
  * Beta testing feedback integration
### 2. Current Challenges
* Resource constraints in QA team
* Third-party API integration delays
* User feedback on new UI
  * Navigation confusion
  * Color contrast issues
### 3. Next Sprint Planning
* Priority Features
  * Payment gateway integration
  * User profile enhancement
  * Analytics dashboard
* Technical Debt
  * Code refactoring
  * Documentation updates
## Action Items
- [ ] @sarah: Finalize Q3 roadmap by Friday
- [ ] @mike: Schedule technical review for payment integration
- [ ] @anna: Share updated design system documentation
- [ ] @david: Prepare QA resource allocation proposal
## Next Steps
* Schedule individual team reviews
* Update sprint board
* Share meeting summary with stakeholders
## Notes
* Next sync scheduled for May 22, 2023
* Platform demo for stakeholders on May 25
* Remember to update JIRA tickets
---
Meeting recorded by: Sarah Chen
Duration: 45 minutes"""

if __name__ == "__main__":
  service = auth_services()
  document_id = create_doc(service, 'AnsibleHealthTest')
  add_text_to_doc(service, document_id, sample_md)