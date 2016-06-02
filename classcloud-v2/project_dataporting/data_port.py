from content.models import Node, Link
from access.models import Account, Person, CustomUser
import json
from django.db import IntegrityError

mediawriter = None

####################
##  write media path
####################
writer = None

####################################
## BASIC SETUP OF USER AND ACCOUNTS
####################################
def _get_user():
    try:
        user = CustomUser.objects.get(username='ell')
    except Exception:
        user = CustomUser.objects.create(username='ell', first_name='ELL', last_name='Zaya')
    return user

def _get_person():
    person, created = Person.objects.get_or_create(user=_get_user())
    return person

def _get_account():
    parent_account, created = Account.objects.get_or_create(title='Zaya Learning Labs')
    ell_account, created = Account.objects.get_or_create(slug='ell', title='ell')

    return ell_account

def port_setup_account_profile():
    _get_user()
    _get_person()
    _get_account()

####################################
### PORTING SKILLS
####################################
def _get_skills(skill_name):
    from .main import logger
    skill, created = Taxonomy.objects.get_or_create(title=skill_name, type=Taxonomy.SKILL)
    logger.info("# MICROSTANDARD created #ID "+skill_name)
    return skill


####################################
## PROCESSING MICROSTANDARD AND NODES
####################################
from taxonomy.models import Taxonomy
def _get_microstandard(microstandard_title):
    from .main import logger

    microstandard, created = Taxonomy.objects.get_or_create(title=microstandard_title, type=Taxonomy.MICROSTANDARD)
    logger.info("# MICROSTANDARD created #ID "+microstandard_title)
    return microstandard

################
# download resource
################
video_files = []


def download_resource(file_path):
    from django.conf import settings
    from .main import logger, get_question_tag, image_files, sound_files, video_files, video_dir
    from os import listdir
    from os.path import isfile, join
    import urllib.request
    from urllib.error import URLError, HTTPError
    from django.core.files import File
    filename = file_path.split('/')[-1]

    curator_path = 'http://curate.zaya.in/media/'
    save_path = '/tmp/videos/'

    url = ''
    if 'http' in file_path or 'https' in file_path:
        url = file_path
    else:
        url = curator_path + file_path

    logger.info("# DOWNLOADING VIDEO MEDIA FROM "+url)
    try:
        if filename in video_files:
            local_filename = video_dir+filename
            logger.info("# VIDEOS ALREADY EXIST ")
        else:
            local_filename, headers = urllib.request.urlretrieve(url, save_path+filename)
    except HTTPError:
        logger.info("# DOWNLOADING FAILED MEDIA FROM " + url)
        pass
    except URLError:
        logger.warning("# STORING FAILED MEDIA  AT "+save_path+filename)
        pass
    except Exception as e:
        logger.warning("# STORING FAILED MEDIA  AT "+save_path+filename+ "reason "+str(e))
        pass
    logger.info("# STORING VIDEO MEDIA AT "+save_path+filename)
    return local_filename


###############
# porting resource
################
from content.models import Resource
def port_resource(resource_details, lesson_id):
    from .main import logger
    from django.core.files import File

    resource_path = resource_details['resource_path']
    file_type = resource_path.split('.')[-1]
    resource_to_attach = File(open(download_resource(resource_path),'rb'))

    resource = Resource.objects.create(path=resource_to_attach, file_type=file_type, size=resource_to_attach.size)

    logger.info("# RESOURCE created #ID "+str(resource.id)+" FOR LESSON "+(str(lesson_id)))
    node = Node.objects.create(title=resource_details['resource_name'], parent_id=lesson_id, account=_get_account(), type=resource)

    logger.info("# RESOURCE NODE created #ID "+str(resource.id)+" FOR LESSON "+(str(lesson_id)))
    return node.id

################
## Taxonomy
################
def _get_level(level):
    from taxonomy.models import Difficulty
    difficulty, created = Difficulty.objects.get_or_create(level=level)
    return difficulty

def _get_grade(grade):
    from taxonomy.models import Grade
    grade, created = Grade.objects.get_or_create(level=grade)
    return grade

###############
# lesson
################
from study.models import Lesson, Assessment
def port_lesson(lesson_details):
    from .main import logger
    if lesson_details['lesson_level']:
        level = _get_level(int(lesson_details['lesson_level']))
    else:
        level = None

    if lesson_details['lesson_grade']:
        grade = _get_grade(int(lesson_details['lesson_grade']))
    else:
        grade = None

    microstandard = _get_microstandard(lesson_details['microstandard'])
    lesson = Lesson.objects.create(objective=lesson_details['lesson_description'], microstandard=microstandard, grade=grade, difficulty=level)
    logger.info("# LESSON created #ID "+str(lesson.id))

    try:
        node = Node.objects.create(id=lesson_details['lesson_id'],title=lesson_details['lesson_name'],description=lesson_details['lesson_description'], type=lesson, account=_get_account(),tag=_get_skills(lesson_details['lesson_tag']))
    except IntegrityError as e:
        original_node = Node.objects.get(id=lesson_details['lesson_id'])
        link = Link.objects.create(link_node=original_node)
        node = Node.objects.create(title=lesson_details['lesson_name'],description=lesson_details['lesson_description'], type=link, account=_get_account(),tag=_get_skills(lesson_details['lesson_tag']))
    return node.id

###############
# assessment
################
def port_assessment(assess_details, lesson_id, type):
    from .main import logger
    assessment = Assessment.objects.create(score=assess_details['fields']['raw_score'], type=type)
    logger.info("# ASSESSMENT created #ID "+str(assessment.id))

    if type == "assessment":
        try:
            node = Node.objects.create(id=assess_details['fields']['id'],
                    title=assess_details['fields']['name'],
                    description=assess_details['fields']['alias'], type=assessment,
                    account=_get_account(), parent_id=lesson_id)
            return node.id
        except IntegrityError as e:
            original_node = Node.objects.get(id=assess_details['fields']['id'])
            link = Link.objects.create(link_node=original_node)
            node = Node.objects.create(title=assess_details['fields']['name'],
                    description=assess_details['fields']['alias'], type=link,
                    account=_get_account(), parent_id=lesson_id)

    #else practice
    node = Node.objects.create(
            title=assess_details['fields']['name'],
            description=assess_details['fields']['alias'], type=assessment,
            account=_get_account(), parent_id=lesson_id)

    return node.id

###############
# question
################
from evaluation.models import JSONQuestion

def get_question_level(level):
    # QUESTION_TYPE = {
    #     'Default': 0,
    #     'SCQ': 1,
    #     'MCQ': 2,
    #     'DR': 3,
    #     'SST': 4,
    #     'SOR': 5,
    #     'PUZ': 6,
    #     'MTF': 7
    # }

    ####################################
    # is_multi = true check remaining
    ####################################

    QUESTION_MAPPING = {
        3:'drquestion',
        1:'choicequestion',
        2:'multichoicequestion',
        4:'sentencestructuring',
        5:'sentenceordering',
        6:'puzzle',
        7:'matchthefollowing'
    }



    return QUESTION_MAPPING[level]

mapper = {
    'a':1,
    'b':2,
    'c':3,
    'd':4
}

def port_question(question_details, lesson_microstandard, assess_id):
    from .main import logger
    from .question_parser import prepare_question
    '''
    1. get parent info
    2. add question to parent node
    '''
    difficulty =  question_details['fields']['difficulty']
    q_type = get_question_level(question_details['fields']['type'])
    score = difficulty*10

    title, content = prepare_question(question_details)

    if q_type=='multichoicequestion':
        q_type='choicequestion'
        content.update({'is_multiple':True})
    elif q_type=='choicequestion':
        q_type='choicequestion'
        content.update({'is_multiple':False})

    if q_type in ['multichoicequestion','choicequestion']:
        old_answer = json.loads(question_details['fields']['answer'])['answer']
        answer = []
        if isinstance(old_answer, dict):
            for key, value in old_answer.items():
                if value:
                    answer.append(mapper[key])
        elif old_answer:
            answer.append(mapper[old_answer])

        if not answer:
            logger.info("# NO ANSWER PROVIDED FOR QUESTION "+str(question_details))

        microstandard = lesson_microstandard
        json_question = JSONQuestion.objects.create(is_critical_thinking=question_details['fields']['ct'],
                        level=difficulty, answer=answer,
                        score=score, content=content, type=q_type,
                        microstandard=microstandard)

        logger.info("# JSON QUESTION created #ID "+str(json_question.id))

        if '<img' in title:
            logger.warning("# IMAGE FOUND in title for question "+str(json_question.id))
            logger.warning("# IMAGE FOUND "+title)

        try:
            node = Node.objects.create(id=question_details['fields']['uuid'],title=title, type=json_question, account=_get_account(), parent_id=assess_id)
        except IntegrityError as e:
            original_node = Node.objects.get(id=question_details['fields']['uuid'])
            link = Link.objects.create(link_node=original_node)
            node = Node.objects.create(title=title, type=link, account=_get_account(), parent_id=assess_id)
        return node.id

    logger.info("# SKIPPING QUESTION TYPE # "+str(question_details))
    return None
