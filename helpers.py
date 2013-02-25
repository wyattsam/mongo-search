def clean_jira_results(raw_results, query):
    JIRA_BASE_URL = 'http://jira.mongodb.com/browse/'

    clean = []
    for i in raw_results:
        doc = {}
        doc['score'] = i['score']
        doc['summary'] = i['obj']['fields']['summary']
        doc['url'] = JIRA_BASE_URL + i['obj']['key']
        doc['source'] = "jira"

        description = i['obj']['fields']['description']
        match_start = description.find(query)
        if match_start != -1:
            start, end = max(0, match_start-200), max(400, match_start+200)
            doc['snippet'] = description[start:end] + " ..."
        else:
            doc['snippet'] = description[:400] + " ..."

        clean.append(doc)
    return clean

def clean_chat_results(raw_results, query):
    clean = []
    for i in raw_results:
        doc = {}
        doc['score'] = i['score']
        doc['summary'] = ''.join(['Chat from ', i['obj']['user'], ' in ', i['obj']['channel']])
        doc['url'] = ''
        doc['snippet'] = i['obj']['content']
        doc['source'] = "chat"

        clean.append(doc)
    return clean