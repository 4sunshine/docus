import urllib.request
import json

def get_html(url):
    req = urllib.request.urlopen(url)
    html_bytes = req.read()
    html_str = html_bytes.decode("utf8")
    req.close()
    return html_str

''' Parse application methods Link '''

html = get_html("https://all-pribors.ru/cat-mi")

application_method = [string.split('</a>')[0] 
                      for string in html.split('class="card-title h3">')[1:]]

application_method_liks = [string.split('a href="')[1].split('"')[0] 
                           for string in html.split('class="card-title h3">')[1:]]

application_methods = {m: {'url': l} for m, l in zip(application_method, application_method_liks)}


''' Parse categories Link '''

for m in application_methods:
    html = get_html(application_methods[m]['url'])

    categories = [string.split('</a>')[0]
                  for string in html.split('class="card-title h5">')[1:]]

    categories_liks = [string.split('a href="')[1].split('"')[0] 
                       for string in html.split('class="card-title h5">')[1:]]
    
    categories = {m: l for m, l in zip(categories, categories_liks)}
    
    application_methods[m]['categories'] = {}
    
    for category, url in zip(categories, categories_liks):
        application_methods[m]['categories'][category] = {'url': url} 

''' Parse subcategories Link '''

for m in application_methods:
    for c in application_methods[m]['categories']:
        html = get_html(application_methods[m]['categories'][c]['url'])

        subcategories = [string.split('</a>')[0]
                         for string in html.split('class="card-title h5">')[1:]]

        subcategories_liks = [string.split('a href="')[1].split('"')[0] 
                             for string in html.split('class="card-title h5">')[1:]]

        subcategories = {m: l for m, l in zip(subcategories, subcategories_liks)}

        application_methods[m]['categories'][c]['subcategories'] = {}

        for subcategory, url in zip(subcategories, subcategories_liks):
            application_methods[m]['categories'][c]['subcategories'][subcategory] = {'url': url} 

n_devices = 0
flag = False
for m in application_methods:
    for c in application_methods[m]['categories']:
        for sc in application_methods[m]['categories'][c]['subcategories']:      
                page = 1
                while True:
                    html = get_html(application_methods[m]['categories'][c]['subcategories'][sc]['url'] + f"?page={page}")

                    devices_ids = [string.split('</div>')[0]
                                  for string in html.split('<div class="h4 text-center">')[1:]]

                    if not len(devices_ids):
                        break
                    else:
                        page += 1

                    devices_links = [string.split('"')[0]
                                     for string in html.split('<div class="text-right"><a href="')[1:]]

                    application_methods[m]['categories'][c]['subcategories'][sc]['ids'] = {}

                    for ID, l in zip(devices_ids, devices_links):
                        n_devices += 1
                        html = get_html(l)
                        try:
                            class_CI = html.split('Класс СИ')[1].split('<td>')[1].split('</td>')[0]
                            year = html.split('Год регистрации')[1].split('<td>')[1].split('</td>')[0]
                            country = html.split('Страна-производитель')[1].split('<td>')[1].split('</td>')[0]
                        except IndexError:
                            continue

                        application_methods[m]['categories'][c]['subcategories'][sc]['ids'][ID] = {
                            "Класс СИ": class_CI, 
                            "Год регистрации": year,
                            "Страна-производитель": country
                        }                   

                with open('data.json', 'w') as f:
                    json.dump(application_methods, f)
                print(f"Total: {round(n_devices/95220, 3)}%. Path: ", m + "/" + c + "/" + sc)
