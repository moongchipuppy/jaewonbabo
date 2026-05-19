import requests

url = "https://generativelanguage.googleapis.com/v1beta/models?key=AIzaSyAB-KXvn4rYu2u6N-52JlDCDSnV2DTPIJ4"
response = requests.get(url)
print(response.status_code)

if response.status_code == 200:
    for model in response.json().get('models', []):
        if 'generateContent' in model.get('supportedGenerationMethods', []):
            print(model['name'])
else:
    print(response.text)
