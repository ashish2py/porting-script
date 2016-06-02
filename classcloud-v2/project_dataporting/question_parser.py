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
##  processing question
##  actual code starts here
####################################
import json
import re
from django.conf import settings
from .main import get_question_tag, image_files, sound_files, video_files

mapper = {
    'a':1,
    'b':2,
    'c':3,
    'd':4
}

def get_file_availbility():
    # global image_files
    # global sound_files
    #
    # from os import listdir
    # from os.path import isfile, join
    # image_dir = settings.MEDIA_ROOT+'/ell/images'
    # sound_dir = settings.MEDIA_ROOT+'/ell/sounds'
    #
    # image_files = [f for f in listdir(image_dir) if isfile(join(image_dir, f))]
    # sound_files = [f for f in listdir(sound_dir) if isfile(join(sound_dir, f))]
    pass

def download_media_from_path(filepath, type):
    # check availablibity
    # get_file_availbility()

    from .main import logger
    import urllib.request
    from urllib.error import URLError, HTTPError

    curator_path = 'http://curate.zaya.in'
    save_path = settings.MEDIA_URL + 'ell/%s/'%(type)
    filename = filepath.split('/')[-1]

    url = ''
    if 'http' in filepath or 'https' in filepath:
        url = filepath
    else:
        url = curator_path + filepath

    media_path = settings.MEDIA_URL + 'ell/%s/%s'%(type, filename)

    try:
        logger.info("# DOWNLOADING "+type+" MEDIA FROM " + url)
        if type=='images':
            if filename in image_files:
                logger.info("# FILE ALREADY AVAILABLE")
                pass
            else:
                local_filename, headers = urllib.request.urlretrieve(url, save_path[1:] + filename)

        if type=='sounds':
            if filename in sound_files:
                logger.info("# FILE ALREADY AVAILABLE")
                pass
            else:
                local_filename, headers = urllib.request.urlretrieve(url, save_path[1:] + filename)

    except HTTPError:
        logger.info("# DOWNLOADING FAILED "+type+" MEDIA FROM " + url)
        pass
    except URLError:
        logger.warning("# STORING FAILED "+type+" MEDIA  AT "+media_path)
        pass
    except Exception as e:
        logger.warning("# STORING FAILED "+type+" MEDIA  AT "+media_path+ "reason "+str(e))
        pass

    logger.info("# STORING "+type+" MEDIA  AT "+media_path)
    return media_path


def get_image_from_content(content):
    try:
        if re.search('img', content):
            return re.findall ( 'src="(.*?)"', content, re.DOTALL)
    except Exception:
        return None

from django.template.defaultfilters import removetags


def prepare_question(question_details):
    '''
    1. check whether question title has media files or not.
    2. check whether question content has media files or not.
    3. prepare content first.
    4. prepare media second.

    widgets : {
        'sound':'',
        'image':'',
        'video':''
    }
    '''

    question_widgets = {
        'widgets':{
            'sounds':{},
            'images':{},
            'videos':{},
        }
    }


    old_question = question_details

    old_question_fields =  old_question['fields']
    old_question_title = old_question_fields['title'].replace('<p>',' <p>')
    old_question_hints = removetags(old_question_fields['hints'], 'p i img br').replace('&nbsp;','').strip()
    old_question_content = json.loads(old_question_fields['content'])
    old_question_soundclips = json.loads(old_question_fields['soundclips'])
    old_question_tag = old_question_fields['tags']
    _get_question_tag = []
    #prepare question tags
    for tag in old_question_tag:
        _get_question_tag.append(get_question_tag(int(tag))['fields']['name'])


    _question_title = ''

    _question_content = {'options':[],'instruction':None,'tags':[]}

    _question_content_widgets_element = question_widgets
    _question_content_widgets = _question_content_widgets_element['widgets']
    _question_content_widgets_images = _question_content_widgets['images']
    _question_content_widgets_sounds = _question_content_widgets['sounds']

    sound_clip_counter = 0
    img_counter = 0

    question_content_status = False

    if 'img' in old_question_title:
        _question_title_without_html = removetags(old_question_title, 'p br img strong').replace('&nbsp;','').strip()
        all_imgs = get_image_from_content(old_question_title)

        _question_title = ''
        for img in all_imgs:
            img_counter = img_counter + 1
            img = download_media_from_path(img,'images')
            _question_content_widgets_images.update({img_counter:img})
            _question_title_without_html = _question_title_without_html+" [[img id=%s]]"%(img_counter)
            _question_title = _question_title_without_html
    else:
        _question_title = old_question_title

    # check sound in title and content
    if 'content' in old_question_soundclips or 'question' in old_question_soundclips:
        '''
        1. prepare sound for title/question
        2. prepare sound for content/options
        '''
        if 'question' in old_question_soundclips:
            if old_question_soundclips['question']:
                sound_clip_counter = sound_clip_counter+1

                q_sound_path = old_question_soundclips['question']['path']
                q_sound_path = download_media_from_path(q_sound_path,'sounds')

                #audio to pic and question instruction logic
                for tag in _get_question_tag:
                    sounds = "[[sound id=%d]]"%(sound_clip_counter)
                    if not tag.startswith('audioto'):
                        _question_content.update({'instruction':sounds})

                _question_content_widgets_sounds.update({sound_clip_counter:q_sound_path})
                _question_title = _question_title + removetags(old_question_title, 'p br img em strong').replace('&nbsp;','').strip()

                if '[[img ' in _question_title:
                    _question_title = _question_title+" [[sound id=%d]] "%(sound_clip_counter)
                else:
                    _question_title_without_html = removetags(old_question_title, 'p br img em strong').replace('&nbsp;','').strip()
                    _question_title = _question_title_without_html + " [[sound id=%d]] "%(sound_clip_counter)

        if 'content' in old_question_soundclips:
            if old_question_soundclips['content']:
                for key, value in old_question_soundclips['content'].items():
                    # check if img is available content
                    question_placeholder = ''
                    for content_key, content_value in old_question_content.items():
                        if content_key == key and 'img' in content_value:
                            _question_content_without_html = removetags(content_value, 'img p')
                            all_imgs = get_image_from_content(content_value)
                            for img in all_imgs:
                                img = download_media_from_path(img,'images')
                                img_counter = img_counter + 1
                                _question_content_widgets_images.update({img_counter:img})
                            question_placeholder = _question_content_without_html+" [[img id=%s]] "%(img_counter)


                    # q_sound_path = old_question_soundclips['question']['path']
                    # q_sound_path = download_media_from_path(q_sound_path,'sounds')
                    sound_clip_counter = sound_clip_counter+1
                    q_sound_path = download_media_from_path(value,'sounds')
                    _question_content_widgets_sounds.update({sound_clip_counter:q_sound_path})
                    question_placeholder = question_placeholder+" [[sound id=%d]] "%(sound_clip_counter)
                    _question_content['options'].append({'key':mapper[key],'option':question_placeholder})
                    # _question_content.update(_question_content_widgets_sounds)
                question_content_status = True
        else:
            pass
            # logger.info('no question sound or no question image found.')
    else:
        pass

    if question_content_status == False:
        if isinstance(old_question_content,dict):
            for key, value in old_question_content.items():
                value_without_html = removetags(value, 'p br img').replace('&nbsp;','').strip()
                all_imgs = get_image_from_content(value)

                if not all_imgs:
                    _question_content['options'].append({'key':mapper[key],'option':value_without_html})
                else:
                    for img in all_imgs:
                        img_counter = img_counter + 1
                        img = download_media_from_path(img,'images')
                        _question_content_widgets_images.update({img_counter:img})
                        value_without_html = value_without_html+" [[img id=%s]]"%(img_counter)
                        _question_content['options'].append({'key':mapper[key],'option':value_without_html})

        elif isinstance(old_question_content,list):
            _question_content = {'option':[]}
            # values = removetags(key, 'p br img').replace('&nbsp;','').strip()
            _question_content['option'].append(old_question_content)

        elif old_question_content:
            #values = removetags(old_question_content, 'p br img').replace('&nbsp;','').strip()
            _question_content['option'].append(old_question_content)

    _question_content.update(_question_content_widgets_element)
    _question_content.update({'hints':old_question_hints})
    _question_title = removetags(_question_title, 'p br img strong em').replace('&nbsp;','').strip()
    if _question_title.startswith('.'):
        _question_title = _question_title.replace('.',' ')

    _question_content['tags']=_get_question_tag
    return  _question_title, _question_content
