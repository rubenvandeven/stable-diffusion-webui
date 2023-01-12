'''
Simple script that takes the files in the outputs directory and parses it into a sortable table
'''

from pathlib import Path
import logging

import tqdm
import datetime

logging.basicConfig()
logger = logging.getLogger('outputs_to_table')


model_hash_files = {
    "7460a6fa": "models/Stable-diffusion/sd-v1.4.ckpt",
    "08bf2ce2": "models/Stable-diffusion/finetuned: epoch=000307.ckpt",
    "9a4c6612": "models/Stable-diffusion/epoch=000461.ckpt",
    "2efa9d2e": "models/Stable-diffusion/finetuned: last.ckpt",
}
model_hash_names = {
    "7460a6fa": "stable diffusion v1.4",
    "08bf2ce2": "finetuned: epoch 000307",
    "9a4c6612": "finetuned: epoch 000461",
    "2efa9d2e": "finetuned: last",
}

outputs_dir = Path(__file__).parent / "outputs"

files = outputs_dir.glob('**/*.txt')

prompts = []
for file in tqdm.tqdm(files):
    img_file = file.with_suffix('.png')
    if not img_file.exists():
        logger.warning(f"No png found {img_file}")
        continue
    
    with open(file, 'r') as fp:
        contents = fp.readlines()
    settings = dict([y.strip() for y in x.split(":")] for x in contents[-1].strip().split(","))
    settings['Model name'] = model_hash_names[settings['Model hash']]
    settings['prompt'] = contents[0]
    settings['img'] = img_file.relative_to(outputs_dir)
    settings['Created'] = datetime.datetime.fromtimestamp(file.stat().st_ctime)

    if contents[1].startswith('Negative prompt'):
        settings['Negative prompt'] = contents[1].split(':', 1)[1].strip()
    
    prompts.append(settings)

prompts.sort(key=lambda s: (list(model_hash_files.keys()).index(s['Model hash']), s['Created']))

# print([s['Model hash'] for s in prompts])


output = """
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>

    <script src="https://unpkg.com/pagedjs/dist/paged.polyfill.js"></script>
    <link rel="stylesheet" href="style.css">
    <link href="pagedjs-interface.css" rel="stylesheet" type="text/css" />
</head>
<body>

    <section id='cover'>
        <h1 class="title">This Place Does Exist</h1>
        <h2>stable diffusion logbook</h2>
    </section>

    <section id="toc">
        <h2>Table of contents</h2>
        <ul>
        
    
    
"""

for h, name in model_hash_names.items():
    output += f"<li>{name} <a class='tocitem' data-target-id='#model{h}'></a></li>"

output += "</ul>"

last_model = None
for prompt in tqdm.tqdm(prompts):
    if last_model != prompt['Model hash']:
        print(prompt['Model hash'])
        output += f"</section><section id='model{prompt['Model hash']}' class='prompt'><h1>{prompt['Model name']}</h1>"
        output += f"<h2>{prompt['Model hash']}</h2>"
        last_model = prompt['Model hash']

    output+= f"""
    <div class='prompt'>
    <img src="{prompt['img']}" >
    <p>{prompt['prompt']}</p>
    <table>
    """

    if "Negative prompt" in prompt:
        output+= f"""
        <p><strong>Negative:</strong> {prompt['Negative prompt']}</p>
        """

    attributes = {x: prompt[x] for x in prompt if x not in ['Model hash', 'Model name', 'img', 'prompt', 'Negative prompt']}

    output+="<tr><th>" + "</th><th>".join(attributes.keys()) + "</th></tr>"
    output+="<tr><td>" + "</td><td>".join([
        p.isoformat(timespec='minutes', sep=' ') if type(p) is datetime.datetime else str(p)
        for p in attributes.values()
        ]) + "</td></tr>"
    
    output+= """
    </table>
    </div>
    """
output += "</section></body></html>"

with open(outputs_dir / "overview.html", 'w') as fp:
    fp.write(output)