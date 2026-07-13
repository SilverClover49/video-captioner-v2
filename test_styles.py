import requests, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'https://api.cerebras.ai/v1/chat/completions'
headers = {'Authorization': 'Bearer csk-yjr8nkkyw9rnx23vmhhkdd5x8n9nf4dpchdypv5rmrnhxm6x', 'Content-Type': 'application/json'}

scene = 'Urban street in South Korea with golden ginkgo trees, traffic, apartments.'

styles = {
    'formal': 'Write a 2-sentence formal caption about: ' + scene,
    'sarcastic': 'Write a 2-sentence sarcastic caption about: ' + scene,
    'humorous_tech': 'Write a 2-sentence tech-humor caption about: ' + scene,
    'humorous_nontech': 'Write a 2-sentence funny caption about: ' + scene,
}

for style, prompt in styles.items():
    data = {'model': 'gemma-4-31b', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 200}
    r = requests.post(url, headers=headers, json=data, timeout=30)
    resp = r.json()
    content = resp['choices'][0]['message']['content'] if resp.get('choices') else ''
    status = 'OK' if content else 'EMPTY'
    print(f'{style}: [{status}] {content[:120] if content else "(no content)"}')
