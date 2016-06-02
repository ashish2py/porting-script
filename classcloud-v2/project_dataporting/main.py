import configparser
import sys
import datetime
import csv
import logging
import os
import json
from .data_port import port_assessment, port_question, port_lesson, port_resource, get_question_level
from django.conf import settings

from os import listdir
from os.path import isfile, join
image_files = []
sound_files = []
video_files = []

image_dir = settings.MEDIA_ROOT+'/ell/images'
sound_dir = settings.MEDIA_ROOT+'/ell/sounds'
video_dir = '/tmp/videos/'

video_files = [f for f in listdir(video_dir) if isfile(join(video_dir, f))]
image_files = [f for f in listdir(image_dir) if isfile(join(image_dir, f))]
sound_files = [f for f in listdir(sound_dir) if isfile(join(sound_dir, f))]

project_path=os.path.dirname(os.path.abspath(__file__))
date = datetime.datetime.now().strftime("%d-%m-%Y")

config = configparser.ConfigParser()
with open(project_path+'/setup.ini', 'r', encoding='utf-8') as f:
    config.read_file(f)
config.sections()
file_path = config['files']['path']

csv_path = file_path+config['files']['csv_path']
json_path = file_path+config['files']['json_path']
logger_path = file_path+config['files']['logger_path']


###############
###  LOGGER
###############
logger = logging.getLogger('setup_porting')
# logger.disabled = True

hdlr = logging.FileHandler(logger_path+'db_porting_logging_'+date+'.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

course_json = {}
topic_json = {}
unit_json = {}
lesson_json = {}
assessment_json = {}
question_json = {}
microstandard_json = {}
resources_json = {}

_assessmnet_question_collection = []

#######################################
#  FILE HANDLING AND DICTIONARY CREATION
#######################################
def question_import():
    logger.warning('QUESTIONS import')
    global question_json
    with open (json_path + config['files']['question']) as question_f:
        logger.info('# question file '+ config['files']['question'])
        question_json = json.load(question_f)


def microstandard_import():
    logger.warning('MICROSTANDARD tags import')
    global microstandard_json
    with open (json_path + config['files']['microstandard']) as microstandard_f:
        logger.info('#  microstandard file '+ config['files']['microstandard'])
        microstandard_json = json.load(microstandard_f)


#######################################
#   MAPPING
#######################################
def get_question(question_id):
    for question in question_json:
        if question_id == question['pk']:
            return question

def get_question_tag(tag_id):
    for tag in microstandard_json:
        if tag_id == tag['pk']:
            return tag

###########################
### practice processing
###########################
import json
def processed_assessment():
    with open (csv_path + config['files']['porting_assessment'], encoding='utf-8') as course_f:
        assess_reader = csv.DictReader(course_f, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        _prev_node_lesson_id = None

        counter = 0

        print ('\n')
        for row in assess_reader:
            counter = counter+1
            sys.stdout.write("\rlesson processing # :%d"%counter)
            sys.stdout.flush()

            lesson_details = {
                'lesson_id':row['lesson_id'],
                'lesson_name':row['lesson_name'],
                'lesson_description':row['lesson_description'],
                'lesson_tag':row['lesson_tag'],
                'lesson_level':row['lesson_level'],
                'lesson_grade':row['unit_grade'],
                'microstandard':row['microstandard']
            }
            #
            # if row['assessment_id'] != "701d1fc8-1823-4813-9a64-751c705b37c6":
            #     continue
            #

            logger.info('\n\n #### NEW LESSON #### \n\n ')
            logger.info('#  LESSON CREATED FOR '+ row['lesson_name'])
            _prev_node_lesson_id = port_lesson(lesson_details)
            logger.info('#  NEW LESSON '+ str(_prev_node_lesson_id))


            ####################
            ## Resources of lesson
            ####################
            if row['resource_available'] == 'True':
                logger.info('#  CREATING RESOURCE ')
                resource_details = {
                    'resource_path':row['resource_path'],
                    'resource_name':row['resource_name'],
                }
                ported_resource = port_resource(resource_details, _prev_node_lesson_id)
                logger.info('#  RESOURCE PORINT STARTED FOR '+ row['lesson_name'])
                logger.info('#  RESOURCE PORTED WITH ID  '+ str(ported_resource))


            #############
            #  PRACTICE
            #############
            if row['practice_available']=='True':
                logger.info('#  CREATING PRACTICE ')
                old_assessment = {
                    'fields':{
                        'id':row['assessment_id'],
                        'raw_score':0,
                        'name':row['lesson_name'],
                        'alias':row['lesson_name']
                    }
                }

                logger.info('#  OLD PRACICE ASSESSMENT '+ str(old_assessment))
                _prev_node_practice_id = port_assessment(old_assessment, _prev_node_lesson_id, 'practice')
                logger.info('#  NEW PRACICE ASSESSMENT '+ str(_prev_node_practice_id))

                for question_id in json.loads(row['practice_questions']):
                    practice_old_question = get_question(question_id)

                    q_type = get_question_level(practice_old_question['fields']['type'])
                    if q_type not in ['multichoicequestion','choicequestion']:
                        logger.info('#  OUESTION TYPE NOT SUPPORTED '+ str(practice_old_question))
                        break

                    logger.info('#  OLD QUESTION '+ str(practice_old_question))
                    _node_question = port_question(practice_old_question, row['microstandard'], _prev_node_practice_id)
                    logger.info('#  NEW QUESTION '+ str(_node_question))

            ###########
            ##   ASSESSMNET
            ###########

            if row['assessment_available'] == 'True':
                old_assessment = {
                    'fields':{
                        'id':row['assessment_id'],
                        'raw_score':row['assessment_score'],
                        'name':row['lesson_name'],
                        'alias':row['lesson_name']
                    }
                }
                logger.info('#  CREATING ASSESSMENT ')
                _prev_node_assessment_id = port_assessment(old_assessment, _prev_node_lesson_id, 'assessment')
                logger.info('#  NEW ASSESSMNET '+ str(_prev_node_assessment_id))

                q_counter = 0
                for question_id in json.loads(row['assessment_questions']):
                    old_question = get_question(question_id)

                    q_type = get_question_level(old_question['fields']['type'])
                    if q_type not in ['multichoicequestion','choicequestion']:
                        logger.info('#  OUESTION TYPE NOT SUPPORTED '+ str(old_question))
                        break

                    logger.info('#  OLD QUESTION '+ str(old_question))
                    _node_question = port_question(old_question, row['microstandard'], _prev_node_assessment_id)
                    logger.info('#  NEW QUESTION '+ str(_node_question))

###########################
### assessment processing
###########################

from  django.http import HttpResponse

def start_porting(request):
    porting_bot = '''
    \n
    PORTING STARTED

    python home/manage.py dumpdata curator.course --indent 2 --format json > course.json
    python home/manage.py dumpdata content.question --indent 2 --format json > questions.json
    python home/manage.py dumpdata content.lesson  --indent 2 --format json > lesson.json
    python home/manage.py dumpdata curator.topic  --indent 2 --format json > topic.json
    python home/manage.py dumpdata common.tag --indent 2 --format json > tags.json
    python home/manage.py dumpdata content.resources --indent 2 --format json > tags.json
    python home/manage.py dumpdata content.assessment --indent 2 --format json > assessment.json
    python home/manage.py dumpdata curator.unit --indent 2 --format json > unit.json
    python home/manage.py dumpdata content.index --indent 2 --format json > resource.json

    \n\n\n
    '''

    print (porting_bot)
    logger.info(porting_bot)

    question_import()
    microstandard_import()

    processed_assessment()
    print ('\n')
    return HttpResponse({"status : done"})
