#!/usr/bin/env python3

import os,threading
import click
import cloudconvert
from dotenv import load_dotenv

load_dotenv()

globally_confirmed = False

# Configure the CloudConvert API
cloudconvert.configure(api_key=os.environ['CLOUDCONVERT_API_KEY'])


def convert(file_path):
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

    print(f"Wait for  task {file_path} to finish")
    export_task = next(task for task in job['tasks'] if task['name'] == 'export-file')
    cloudconvert.Task.wait(id=export_task['id'])  # Wait for the task to finish

    export_task_refreshed = cloudconvert.Task.find(id=export_task['id'])
    file_url = export_task_refreshed['result']['files'][0]['url']
    output_path = os.path.splitext(file_path)[0] + '.pdf'
    cloudconvert.download(url=file_url, filename=output_path)
    print(f'Converted and downloaded: {output_path}')

def threaded_convert(filename):
    # Wrap the convert function in a thread
    conversion_thread = threading.Thread(target=convert, args=(filename,))
    conversion_thread.start()
    return conversion_thread

def convert_all(path, silent=False):
    global globally_confirmed
    if path is None or not os.path.exists(path):
        print('Invalid path:', path)
        return
    count = 0
    threads = []
    for filename in [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if f.endswith('.pages')]:
        if not silent:
            if not globally_confirmed:
                confirm = input(f'Want to convert {filename}? (y/n/a): ')
                if confirm.lower() == 'a':
                    globally_confirmed = True
                elif confirm.lower() != 'y':
                    continue
            base, _ = os.path.splitext(filename)
            if os.path.exists(base + '.pdf'):
                confirm = input(f'DANGER: File {base + ".pdf"} already exists. Overwrite? (y/n): ')
                if confirm.lower() != 'y':
                    continue
        thread = threaded_convert(filename)
        threads.append(thread)
        count += 1
    for thread in threads:
        thread.join()  # Wait for all threads to complete
    print(f'Converted {count} files')



@click.command()
@click.argument('path')
@click.option('--silent', is_flag=True, default=False, help="don't ask for confirmation (DANGER!)")
def cli(path, silent):
    """Converts all .pdf files in the directory to .pdf format using CloudConvert."""
    convert_all(path=path, silent=silent)

if __name__ == '__main__':
    cli()