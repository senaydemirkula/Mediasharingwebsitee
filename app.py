from flask import Flask, render_template, request, redirect, flash, url_for, Response
import boto3
from io import BytesIO
from PIL import Image

app = Flask(__name__, template_folder='/home/ec2-user/project/templates')
app.secret_key = 'justakey'

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb', region_name='ca-central-1') 
table = dynamodb.Table('mediasharingwebsite')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        Filename = request.form['name']
        description = request.form['description']
        location = request.form['location']
        file = request.files['file']
        s3.upload_fileobj(file, 'mediasharingwebsite', file.filename)

       
        key = file.filename
        table.put_item(
            Item={
                'id': key,
                'name': Filename,
                'description': description,
                'location': location
            }
        )

        flash('File uploaded successfully')
        return redirect('/')
    else:
        try:
            objects = s3.list_objects(Bucket='mediasharingwebsite')['Contents']
            files = []
            for obj in objects:
                if obj['Key'].endswith('.jpg') or obj['Key'].endswith('.png'):
                    url = url_for('thumbnail', key=obj['Key'])
                    # retrieving metadata from DynamoDB
                    response = table.get_item(
                        Key={
                            'imageId': obj['Key']
                        }
                    )
                    Filename = response['Item']['name']
                    description = response['Item']['description']
                    location = response['Item']['location']
                    files.append({'key': obj['Key'], 'url': url, 'Filename': Filename, 'description': description, 'location': location})
        except:
            files = []
        return render_template('index.html', files=files)

@app.route('/delete', methods=['POST'])
def delete_file():
    key = request.form['key']
    s3.delete_object(Bucket='mediasharingwebsite', Key=key)
    # deleting metadata from Dynamo db
    table.delete_item(
        Key={
            'id': key
        }
    )
    flash('File deleted successfully')
    return redirect('/')

@app.route('/thumbnail/<key>')
def thumbnail(key):
    response = s3.get_object(Bucket='mediasharingwebsite', Key=key)
    image = Image.open(BytesIO(response['Body'].read()))
    image.thumbnail((200, 200))
    image = image.convert('RGB')
    with BytesIO() as output:
        image.save(output, format='JPEG')
        contents = output.getvalue()
    return Response(contents, mimetype='image/jpeg')


if __name__ == '__main__':
    app.run(host='0.0.0.0')