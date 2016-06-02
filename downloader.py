import json
import sys
import os
import re

sys.path.append( '.' )
sys.path.append( '..' )
sys.path.append( '../../' )
sys.path.append( '../../../' )
sys.path.append( '../../../home/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from apps.content.models import *
from apps.curator.models import *

def get_image_from_content(content):
    try:
        if re.search('img', content):
            return re.findall ( 'src="(.*?)"', content, re.DOTALL)
    except Exception:
        return None


def dataporting():
    print '''
    \n\n
    ########################
    ####  DATA PORTING  ####
    ########################
    \n\n
    '''

    import csv

    writer = None
    import datetime
    date = datetime.datetime.now().strftime("%d-%m-%Y")

    # with open('porting_assessment_csv_unit_1_'+date+'.csv', 'w') as csvfile:
    #     fieldnames = ['course_id','course_name','unit_id','unit_name','unit_grade','topic_id','topic_name','lesson_id','lesson_tag','lesson_name','lesson_description','lesson_level','lesson_grade','resource_available','resource_path','resource_name','practice_available','practice_name','practice_questions','assessment_available','assessment_id','assessment_name','assessment_questions','assessment_score','microstandard']
    #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t',
    #                         quotechar='"', quoting=csv.QUOTE_ALL)
    #     writer.writeheader()

    sound_list = set()
    with open('downloadable_media_'+date+'.csv', 'w') as media_file:
    	fieldnames = ['video']
        writer = csv.DictWriter(media_file, fieldnames=fieldnames, delimiter='\t', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        lesson_counter = 0
        course = Course.objects.get(id=384)
        # units = course.course_units.all()
        units = course.course_units.all()
        dict_head = {'video':None}

        for unit in units:
            #TODO : CHECK FOR BLOCK ASSESSMENT
            for topic in unit.unit_topics.all():
                for lesson in topic.lessons.all():
                    lesson_counter = lesson_counter+1
                    sys.stdout.write("\rlesson processing # :%d"%lesson_counter)
                    sys.stdout.flush()

                    # if lesson.resources.last():
                    #     dict_head['video']=lesson.resources.last().path.split('/')[-1]

                    ##########################################
                    ### prepare assessment and practice
                    ##########################################
                    lesson_questions = Question.objects.filter(microstandard=lesson.microstandard)
                    for question in lesson_questions:
                        # if get_image_from_content(question.title):
                        #     # for img in get_image_from_content(question.title):
                        #     #     dict_head['image'] = img

                        if 'content' in json.loads(question.soundclips).keys():
                        # if json.loads(question.soundclips)['content']:
                            for key,value in json.loads(question.soundclips)['content'].items():
                                # dict_head['content-sound']=value.split('/')[-1]
                                sound_list.add(value.split('/')[-1])

                            if 'question' in json.loads(question.soundclips).keys():
                                if 'path' in json.loads(question.soundclips)['question']:
                                    path = json.loads(question.soundclips)['question']['path']
                                    sound_list.add(path.split('/')[-1])




        for sound in sound_list:
            dict_head['sound']=sound
            writer.writerow(dict_head)

    print ('\n  DONE \n')
if __name__ == "__main__":
    ''' .. actual code starts here ..'''
    dataporting()
