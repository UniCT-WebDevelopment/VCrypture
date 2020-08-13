from flask import Flask, request, send_from_directory, after_this_request
from flask_executor import Executor
from flask_mail import Mail, Message
from io import BytesIO
from os import getcwd, path, unlink
from PIL import Image
from requests import get
from typing import List, Tuple
from uuid import uuid4
from zipfile import ZipFile

import dhiman_kasana
import naor_shamir
import taghaddos_latif


app = Flask(__name__)
app.config.from_pyfile('settings.cfg')
executor = Executor(app)
mail = Mail(app)

web_endpoint = app.config['WEB_ENDPOINT']
storage_folder = path.join(getcwd(), app.config['STORAGE_FOLDER'])


def send_email(subject, recipient, body, attachment=None):
    msg = Message(subject)
    msg.add_recipient(recipient)
    msg.html = body
    if attachment:
        msg.attach(attachment['filename'],
                   attachment['mimetype'],
                   attachment['data'])
    mail.send(msg)


def create_zip(entries: List[Tuple[str, bytes]]) -> str:
    filename = f'{uuid4()}.zip'
    filepath = path.join(storage_folder, filename)
    zip_file = ZipFile(filepath, 'w')
    for name, data in entries:
        zip_file.writestr(name, data)
    zip_file.close()
    return filename


def task(tsk, x, dest):
    output = tsk['f'](x)
    if type(output) == tuple:
        # f is encryption -> output contains shares
        subject = 'VCrypture - Encryption'
        shares = tuple((f'{uuid4()}.png', share.getvalue())
                       for share in output)
        filename = create_zip(shares)
        with open('htmls/encryption_mail.html') as msg:
            body = msg.read()
        body = body.replace('{ALG}', tsk['alg']).replace('{LINK}', f'{web_endpoint}/download/{filename}').replace(
            '{WEB}', web_endpoint).replace('{BG}', f'{web_endpoint}/assets/img/bg.jpg')
        attachment = None
    else:
        # f is decryption -> output is image
        subject = 'VCrypture - Decryption'
        with open('htmls/decryption_mail.html') as msg:
            body = msg.read()
        body = body.replace('{ALG}', tsk['alg']).replace('{LINK}', tsk['link']).replace(
            '{WEB}', web_endpoint).replace('{BG}', f'{web_endpoint}/assets/img/bg.jpg')
        attachment = {
            'filename': f'{uuid4()}.png',
            'mimetype': 'image/png',
            'data': output.getvalue()
        }
    send_email(subject, dest, body, attachment)


def check_image(i) -> Tuple[int, int]:
    try:
        with Image.open(i) as img:
            return img.size
    except:
        return None
    finally:
        i.seek(0)


def check_same_size(*sizes):
    return len(sizes) > 0 and all(size == sizes[0] for size in sizes)


def check_form_data(form_data, required_fields: tuple) -> bool:
    for field in required_fields:
        if field not in form_data:
            return False
    return True


def download_images(n, size, enc, covers, dest):
    # Download images and then start encryption
    width, height = size
    for _ in range(n):
        # Download random images to create covers for shares
        res = get(
            f'https://picsum.photos/{width}/{height}', allow_redirects=True)
        covers.append(BytesIO(res.content))
    task_info = {
        'f': enc,
        'alg': 'Dhiman-Kasana',
    }
    executor.submit(task, task_info, tuple(covers), dest)


@app.route('/api/download/<path:filename>')
def download(filename):
    filepath = path.join(storage_folder, filename)
    if path.exists(filepath) and path.isfile(filepath):
        @after_this_request
        def x(response):
            unlink(filepath)
            return response
        return send_from_directory(storage_folder, filename, as_attachment=True)
    return {
        'error': 'Not Found'
    }, 404


@app.route('/api/dhimankasana', methods=['POST'])
def dhiman_kasana_enc():
    if not check_form_data(request.form, ('mode', 'dest')) or not check_form_data(request.files, ('image',)):
        return {
            'operation': 'encryption',
            'algorithm': 'Dhiman-Kasana',
            'error': 'Invalid input data'
        }, 400

    secret = request.files['image']
    mode = int(request.form['mode'])
    dest = request.form['dest']

    if mode == 1:
        # Each share will contain 1 channel only, all shares are required for decryption
        enc = dhiman_kasana.enc_nn
        sharesRequired = 3
    else:
        # Each share will contain 2 channels, 2 shares are required to decrypt
        enc = dhiman_kasana.enc_kn
        sharesRequired = 2

    img_size = check_image(secret)
    if not img_size:
        return {
            'operation': 'encryption',
            'algorithm': 'Dhiman-Kasana',
            'error': 'Invalid image'
        }, 400

    sharesCreated = 3
    covers = [BytesIO(secret.read())]
    executor.submit(download_images, sharesCreated,
                    img_size, enc, covers, dest)

    return {
        'operation': 'encryption',
        'algorithm': 'Dhiman-Kasana',
        'imgSize': img_size,
        'sharesCreated': sharesCreated,
        'sharesRequired': sharesRequired,
        'dest': dest
    }


@app.route('/api/dhimankasana/dec', methods=['POST'])
def dhiman_kasana_dec():
    if not check_form_data(request.form, ('mode', 'dest')):
        return {
            'operation': 'decryption',
            'algorithm': 'Dhiman-Kasana',
            'error': 'Invalid input form'
        }, 400

    mode = int(request.form['mode'])
    dest = request.form['dest']
    if mode == 1:
        n_shares = 3
        f = dhiman_kasana.dec_nn
    else:
        n_shares = 2
        f = dhiman_kasana.dec_kn

    if not check_form_data(request.files, tuple([f'share{i}' for i in range(1, n_shares+1)])):
        return {
            'operation': 'decryption',
            'algorithm': 'Dhiman-Kasana',
            'error': 'Invalid input files'
        }, 400

    sizes = []
    for i in range(1, n_shares + 1):
        size = check_image(request.files[f'share{i}'])
        if not size:
            return {
                'operation': 'decryption',
                'algorithm': 'Dhiman-Kasana',
                'error': f'Invalid image share{i}'
            }, 400
        sizes.append(size)

    if not check_same_size(*sizes):
        return {
            'operation': 'decryption',
            'algorithm': 'Dhiman-Kasana',
            'error': 'Covers must have the same size'
        }, 400

    shares = [BytesIO(request.files[f'share{i}'].read())
              for i in range(1, n_shares + 1)]

    task_info = {
        'f': f,
        'alg': 'Dhiman-Kasana',
        'link': web_endpoint
    }
    executor.submit(task, task_info, tuple(shares), dest)

    return {
        'operation': 'decryption',
        'algorithm': 'Dhiman-Kasana',
        'sharesSize': sizes[0],
        'dest': dest
    }


@app.route('/api/naorshamir', methods=['POST'])
def naor_shamir_enc():
    if not check_form_data(request.form, ('dest',)) or not check_form_data(request.files, ('image',)):
        return {
            'operation': 'encryption',
            'algorithm': 'Naor-Shamir',
            'error': 'Invalid input data'
        }, 400

    secret = request.files['image']
    dest = request.form['dest']

    img_size = check_image(secret)
    if not img_size:
        return {
            'operation': 'encryption',
            'algorithm': 'Naor-Shamir',
            'error': 'Invalid image'
        }, 400

    source = BytesIO(secret.read())
    task_info = {
        'f': naor_shamir.enc,
        'alg': 'Naor-Shamir'
    }
    executor.submit(task, task_info, source, dest)

    return {
        'operation': 'encryption',
        'algorithm': 'Naor-Shamir',
        'imgSize': img_size,
        'dest': dest
    }


@app.route('/api/naorshamir/dec', methods=['POST'])
def naor_shamir_dec():
    if not check_form_data(request.form, ('dest',)) or not check_form_data(request.files, ('share1', 'share2')):
        return {
            'operation': 'decryption',
            'algorithm': 'Naor-Shamir',
            'error': 'Invalid input data'
        }, 400

    share1 = request.files['share1']
    share2 = request.files['share2']
    dest = request.form['dest']

    s1 = check_image(request.files['share1'])
    s2 = check_image(request.files['share2'])
    if not s1 or not s2 or s1 != s2:
        return {
            'operation': 'decryption',
            'algorithm': 'Naor-Shamir',
            'error': 'Invalid shares'
        }, 400

    shares = (BytesIO(share1.read()), BytesIO(share2.read()))

    task_info = {
        'f': naor_shamir.dec,
        'alg': 'Naor-Shamir',
        'link': web_endpoint
    }
    executor.submit(task, task_info, shares, dest)

    return {
        'operation': 'decryption',
        'algorithm': 'Naor-Shamir',
        'sharesSize': s1,
        'dest': dest
    }


@app.route('/api/taghaddoslatif', methods=['POST'])
def taghaddos_latif_enc():
    if not check_form_data(request.form, ('dest',)) or not check_form_data(request.files, ('image',)):
        return {
            'operation': 'encryption',
            'algorithm': 'Taghaddos-Latif',
            'error': 'Invalid input data'
        }, 400

    secret = request.files['image']
    dest = request.form['dest']

    img_size = check_image(secret)
    if not img_size:
        return {
            'operation': 'encryption',
            'algorithm': 'Taghaddos-Latif',
            'error': 'Invalid image'
        }, 400

    source = BytesIO(secret.read())
    task_info = {
        'f': taghaddos_latif.enc,
        'alg': 'Taghaddos-Latif'
    }
    executor.submit(task, task_info, source, dest)

    return {
        'operation': 'encryption',
        'algorithm': 'Taghaddos-Latif',
        'imgSize': img_size,
        'dest': dest
    }


@app.route('/api/taghaddoslatif/dec', methods=['POST'])
def taghaddos_latif_dec():
    if not check_form_data(request.form, ('dest',)) or not check_form_data(request.files, ('share1', 'share2')):
        return {
            'operation': 'decryption',
            'algorithm': 'Taghaddos-Latif',
            'error': 'Invalid input data'
        }, 400

    share1 = request.files['share1']
    share2 = request.files['share2']
    dest = request.form['dest']

    s1 = check_image(request.files['share1'])
    s2 = check_image(request.files['share2'])
    if not s1 or not s2 or s1 != s2:
        return {
            'operation': 'decryption',
            'algorithm': 'Taghaddos-Latif',
            'error': 'Invalid shares'
        }, 400

    shares = (BytesIO(share1.read()), BytesIO(share2.read()))

    task_info = {
        'f': taghaddos_latif.dec,
        'alg': 'Taghaddos-Latif',
        'link': web_endpoint
    }
    executor.submit(task, task_info, shares, dest)

    return {
        'operation': 'decryption',
        'algorithm': 'Taghaddos-Latif',
        'sharesSize': s1,
        'dest': dest
    }
