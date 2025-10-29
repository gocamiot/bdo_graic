#!/usr/bin/env bash
# exit on error
set -o errexit

# Install & Execute WebPack 
npm i
npm run build

#Initial setup install - One liners
#py -m venv venv && cd venv\Scripts && activate && cd .. && cd .. && cd bdo_graic
#python -m pip install --upgrade pip & pip install -r requirements.txt & pip install git+https://github.com/gocamiot/loader.git & pip install git+https://github.com/gocamiot/comms.git && python manage.py collectstatic --no-input && python manage.py makemigrations && python manage.py migrate && py manage.py runserver

#After Initial Setup of GRC - One liners
#cd venv\Scripts && activate && cd .. && cd .. && cd bdo_graic
#python manage.py makemigrations && python manage.py migrate && py manage.py runserver


#Commands to install GRC for First time on a Device
py -m venv venv
cd venv\Scripts
activate
cd ..
cd ..
cd bdo_graic
python -m pip install --upgrade pip
pip install -r requirements.txt
#Install Loader
pip install git+https://github.com/gocamiot/loader.git # Make sure you have setup git access, otherwise you need to install manaully
#Install Comms
pip install git+https://github.com/gocamiot/comms.git # Make sure you have setup git access, otherwise you need to install manaully
python manage.py collectstatic --no-input
python manage.py makemigrations
python manage.py migrate
py manage.py runserver


#in another cmd
#goto project dir
#activate venv
python manage.py process_tasks

# Collect Static
python manage.py collectstatic --no-input

# DB Migration & Provisioning  
# python manage.py csv-to-model

#python manage.py csv-to-model -ld
python manage.py column-processor

#To install loader
#pip install git+https://github.com/gocamiot/loader.git
#To run loader
#python manage.py process_tasks

#Create Users
#py manage.py createsuperuser 
#py manage.py createaudituser
#pip install git+https://github.com/gocamiot/loader.git 

