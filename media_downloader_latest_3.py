def download_file_from_media_file():
    import csv
    import sys
    import datetime
    date = datetime.datetime.now().strftime("%d-%m-%Y")

    with open('downloadable_media_'+date+'.csv', 'r') as media_csv:        
        media_reader = csv.DictReader(media_csv, delimiter='\t',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)        

        img_save_path = '/home/ubuntu/porting/ell/image/'
        sound_save_path = '/home/ubuntu/porting/ell/sound/'
        video_save_path = '/home/ubuntu/porting/ell/video/'

        import urllib.request    
        
        counter = 0
        for row in media_reader:
            counter = counter + 1
            sys.stdout.write("\rProcessing # :%d"%counter)
            sys.stdout.flush()

            sound_filename = row['sound'].split('/')[-1]
            img_filename = row['image'].split('/')[-1]
            video_filename = row['video'].split('/')[-1]

            # if row['image']:
            #     img_url ="http://curate.zaya.in"+row['image']
            #     response = urllib.request.urlretrieve(img_url, img_save_path+img_filename)
            
            # if row['sound']:
            #     sound_url ="http://curate.zaya.in"+row['sound']
            #     response = urllib.request.urlretrieve(sound_url, sound_save_path+sound_filename)
            #     
            print row['video']

            # if row['video']:
            #     video_url = ''
            #     if 'http://' in row['video'] or 'https://' in row['video']:
            #         video_url = row['video']
            #     else:
            #         video_url ="http://curate.zaya.in/media/"+row['video']
            #     response = urllib.request.urlretrieve(video_url, video_save_path+video_filename)

download_file_from_media_file()