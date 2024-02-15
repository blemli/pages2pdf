#!/usr/bin/env python3

import os
import click
import cloudconvert
from dotenv import load_dotenv

load_dotenv()

# Configure the CloudConvert API
cloudconvert.configure(api_key=os.environ['CLOUDCONVERT_API_KEY'])


def convert_file_to_pdf(file_path):
    # Create a job with tasks for uploading, converting, and exporting the file
    job = cloudconvert.Job.create(payload={
        'tasks': {
            'upload-file': {
                'operation': 'import/upload'
            },
            'convert-to-pdf': {
                'operation': 'convert',
                'input': ['upload-file'],
                'output_format': 'pdf',
            },
            'export-file': {
                'operation': 'export/url',
                'input': ['convert-to-pdf'],
            }
        }
    })

    upload_task = next(task for task in job['tasks'] if task['name'] == 'upload-file')

    # Correctly handle the upload using the provided task object
    upload_task_obj = cloudconvert.Task.find(id=upload_task['id'])
    with open(file_path, 'rb') as file:
        cloudconvert.Task.upload(file_name=file_path, task=upload_task_obj)

    print("Wait for the export task to complete and get the result")
    export_task = next(task for task in job['tasks'] if task['name'] == 'export-file')
    cloudconvert.Task.wait(id=export_task['id'])  # Wait for the task to finish

    print("Download the converted file")
    export_task_refreshed = cloudconvert.Task.find(id=export_task['id'])
    file_url = export_task_refreshed['result']['files'][0]['url']
    output_path = os.path.splitext(file_path)[0] + '.pdf'
    cloudconvert.download(url=file_url, filename=output_path)
    print(f'Converted and downloaded: {output_path}')




def convert_all_pdf_to_pdf(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.pdf'):
                file_path = os.path.join(root, file)
                convert_file_to_pdf(file_path)

@click.command()
@click.argument('directory')
def cli(directory):
    """Converts all .pdf files in the directory to .pdf format using CloudConvert."""
    convert_all_pdf_to_pdf(directory)

if __name__ == '__main__':
    cli()
