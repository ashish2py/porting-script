import json
import sys
import os

sys.path.append( '.' )
sys.path.append( '..' )
sys.path.append( '../../' )
sys.path.append( '../../home/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from apps.content.models import *
from apps.curator.models import *

def get_skill_from_lesson_title(lesson_title):
    lesson_title = lesson_title.lower()

    skill_tag_map = {
        'grammar':'Grammar',
        'vocabulary':'Vocabulary',
        'listening':'Listening',
        'reading':'Reading'
    }
    if 'grammar' in lesson_title or 'alphabetic' in lesson_title:
        return skill_tag_map['grammar']
    if 'vocabulary' in lesson_title or 'words' in lesson_title:
        return skill_tag_map['vocabulary']
    if 'listening' in lesson_title:
        return skill_tag_map['listening']
    if 'reading' in lesson_title or 'phonics' in lesson_title:
        return skill_tag_map['reading']
    return 'No tag'

# lesson_to_map = [15440,9735,18219,9690,15445,16572,8369,8377,8388,15491,18293,15504,15518,15522,15523,18948,13114,17093,18954,13147]

# lesson_to_map = {13221:"Words - Pronouns - I, you",
# 9736:"Words - Greetings - hello, goodbye, please, thanks you",
# 16510:"Words - People - student, teacher, headmaster, headmistress, friend",
# 9690:"Words - Stationery - pencil, book, pen, paper",
# 13083:"Words - Commands - look, listen, read, write",
# 13218:"Words - Conversations - How are you?",
# 8369:"Alphabetic Principle - Upper Case - Alphabetical Order",
# 8377:"Alphabetic Principle - Lower Case - Letter names (Name to letter)",
# 8388:"Alphabetic Principle - Lower Case - Consonants vs Vowels",
# 13856:"Reading - Comprehension - Introducing yourself",
# 9698:"Grammar - Concept - Indefinite Articles (a vs an)",
# 10419:"Grammar - Concept - The Adjective",
# 10422:"Grammar - Rule - This vs That",
# 10423:"Words - Question Words - What",
# 13089:"Words - Question Words - Which",
# 18948:"Listening - Comprehension - Which",
# 13114:"Words - Conversational - My Favourite",
# 13234:"Reading - Comprehension - My Favourite",
# 18954:"Listening - Comprehension - My Favourite",
# 13151:"Grammar - Negative Sentences - Introductions"}

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

    with open('porting_ell_mobile_1_'+date+'.csv', 'w') as csvfile:
        fieldnames = ['course_id','course_name','unit_id','unit_name','unit_grade','topic_id','topic_name','lesson_id','lesson_tag','lesson_name','lesson_description','lesson_level','lesson_grade','resource_available','resource_path','resource_name','practice_available','practice_name','practice_questions','assessment_available','assessment_id','assessment_name','assessment_questions','assessment_score','microstandard']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t',
                            quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writeheader()

        dict_head = {
            'course_id':'course_id',
            'course_name':'course_name',
            'unit_id':'unit_id',
            'unit_name':'unit_name',
            'unit_grade':'unit_grade',
            'topic_id':'topic_id',
            'topic_name':'topic_name',
            'lesson_id':'lesson_id',
            'lesson_tag':'lesson_tag',
            'lesson_name':'lesson_name',
            'lesson_description':'lesson_description',
            'lesson_level':'lesson_level',
            'lesson_grade':'lesson_grade',
            'resource_available':None,
            'resource_path':'resource_path',
            'resource_name':'resource_name',
            'practice_available':None,
            'practice_name':'practice_name',
            'practice_questions':[],
            'assessment_available':None,
            'assessment_id':'assessment_id',
            'assessment_name':'assessment_name',
            'assessment_questions':[],
            'assessment_score':'assessment_score',
            'microstandard':'microstandard',
        }

        lesson_counter = 0
        course = Course.objects.get(id=715)
        # units = course.course_units.all()
        units = course.course_units.all()

        dict_head['course_id']=course.uuid
        dict_head['course_name']=course.name

        for unit in units:
            dict_head['unit_id'] = unit.uuid
            dict_head['unit_name'] = unit.name

            #TODO : CHECK FOR BLOCK ASSESSMENT
            grade = unit.name.split(' ')[-1]
            if grade in ['0', '1', '2', '3', '4', '5']:
                dict_head['unit_grade'] = grade
            else:
                dict_head['unit_grade'] = None

            for topic in unit.unit_topics.all():
                dict_head['topic_id']=topic.uuid
                dict_head['topic_name']=topic.name

                for lesson in topic.lessons.all():
                    lesson_counter = lesson_counter+1
                    sys.stdout.write("\rlesson processing # :%d"%lesson_counter)
                    sys.stdout.flush()

                    dict_head['lesson_id']=lesson.uuid
                    dict_head['lesson_name']=(lesson.name).encode('utf-8')
                    dict_head['lesson_description']=(lesson.desc).encode('utf-8')
                    dict_head['lesson_level']=lesson.difficulty.level
                    dict_head['lesson_grade']=grade
                    dict_head['lesson_tag']=get_skill_from_lesson_title(lesson.name).encode('utf-8')
                    dict_head['microstandard']=lesson.microstandard.name

                    # RESOURCE
                    #assuming only one resource attached
                    if lesson.resources.last():
                        dict_head['resource_available']=True
                        dict_head['resource_path']=lesson.resources.last().path
                        dict_head['resource_name']=(lesson.resources.last().name).encode('utf-8')
                    else:
                        dict_head['resource_available']=False
                        dict_head['resource_path']=None
                        dict_head['resource_name']=None

                    ##########################################
                    ### prepare assessment and practice
                    ##########################################
                    lesson_assessments_ids = lesson.assessments.all().values_list('id', flat=True)
                    assessment = lesson.assessments.last()

                    # print ('in assessment', lesson_assessments_ids)
                    assessment_question_ids = AssessmentQuestions.objects.filter(assessment_id__in=lesson_assessments_ids).values_list('question_id', flat=True)

                    practice_question_ids = Question.objects.filter(microstandard=lesson.microstandard).exclude(id__in=assessment_question_ids).values_list('id',flat=True)

                    ####################
                    # PRACTICE
                    ####################
                    if practice_question_ids:
                        dict_head['practice_available']=True
                        dict_head['practice_name']=(lesson.name).encode('utf-8')
                        dict_head['practice_questions']=[id for id in practice_question_ids]
                    else:
                        dict_head['practice_available']=False
                        dict_head['practice_name']=None
                        dict_head['practice_questions']=[]

                    ####################
                    # ASSESSMENT
                    ####################
                    if assessment_question_ids:
                        dict_head['assessment_available']=True
                        dict_head['assessment_id']=assessment.uuid
                        dict_head['assessment_score']=assessment.raw_score
                        dict_head['assessment_name']=(assessment.name).encode('utf-8')
                        dict_head['assessment_questions']=[id for id in assessment_question_ids]

                    else:
                        dict_head['assessment_available']=False
                        dict_head['assessment_id']=None
                        dict_head['assessment_name']=None
                        dict_head['assessment_score']=None
                        dict_head['assessment_questions']=[]

                    writer.writerow(dict_head)
    print ('\n  DONE \n')
if __name__ == "__main__":
    ''' .. actual code starts here ..'''
    dataporting()
