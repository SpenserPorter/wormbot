import cairosvg as svg
import svgutils.transform as sg
import boto3
import copy
import os
import asyncio
import uuid

coord_dict = {
    "1": (42, 332),
    "2": (42, 240),
    "3": (42, 148),
    "4": (123, 332),
    "5": (123, 240),
    "6": (123, 148),
    "7": (204, 332),
    "8": (204, 240),
    "9": (204, 148),
    "10": (284, 332),
    "11": (284, 240),
    "12": (284, 148),
    "13": (365, 332),
    "14": (365, 240),
    "15": (365, 148),
    "16": (445, 332),
    "17": (445, 240),
    "18": (445, 148),
    "19": (526, 332),
    "20": (526, 240),
    "21": (526, 148),
    "22": (607, 332),
    "23": (607, 240),
    "24": (607, 148),
    "25": (687, 332),
    "26": (687, 240),
    "27": (687, 148),
    "28": (768, 332),
    "29": (768, 240),
    "30": (768, 148),
    "31": (849, 332),
    "32": (849, 240),
    "33": (849, 148),
    "34": (929, 332),
    "35": (929, 240),
    "36": (929, 148),
    "red": (380, 487),
    "black": (540, 487),
    "odd": (712, 487),
    "even": (216, 487),
    "1-18": (61, 487),
    "19-36": (862, 487),
    "1-12": (141, 394),
    "13-24": (465, 394),
    "25-36": (788, 394),
    "1st": (986, 309),
    "2nd": (986, 215),
    "3rd": (986, 125)
}

def get_coords(space, offset=(0,0), chip=False):
    if chip:
        if space in [str(x) for x in range(1,37)]:
            offset = (offset[0]-24,offset[1]-24)
    base=coord_dict[str(space)]
    actual=(base[0]+offset[0],base[1]+offset[1])
    return actual

async def cleanup():
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('lottobot')
    return bucket.objects.all().delete()

async def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3')

    try:
        s3.upload_file(local_file, bucket, s3_file, ExtraArgs={'ACL':'public-read'})
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

class Table(object):
    def __init__(self):
        self.table=sg.fromfile('staging_table.svg')
        self.blue = self.table.find_id("svg_226")
        self.red = self.table.find_id("svg_231")
        self.black = self.table.find_id("svg_241")
        self.green = self.table.find_id("svg_236")
        self.marker = self.table.find_id("svg_43")

    def add_wagers(self, wager_dict):
        user = 0
        for user_id, wager_list in wager_dict.items():
            user+=1
            for wager in wager_list:
                self.create_token(wager.space, user)

    def create_token(self, space, user):
        if (user % 4 == 1):
            token_base = self.blue
            offset=(0,0)
        elif (user % 4 == 2):
            token_base = self.red
            offset=(5,5)
        elif (user % 4 == 3):
            token_base = self.black
            offset=(10,10)
        elif (user % 4 == 0):
            token_base = self.green
            offset=(15,15)
        token_copy = copy.deepcopy(token_base)
        copy_coords=get_coords(space, offset=offset, chip=True)
        token_copy.moveto(*copy_coords)
        self.table.append(token_copy)

    def mark_winning_space(self, space):
        winner_coords=get_coords(space, offset=(-25,-15))
        self.marker.moveto(*winner_coords)
        self.table.append(self.marker)

    async def render(self):
        image_id = uuid.uuid4()
        s3_image_url = '{}.png'.format(image_id)
        self.table.save("modifiedtable.svg")
        svg.svg2png(url="modifiedtable.svg", write_to="final_table.png")
        await upload_to_aws('final_table.png', 'lottobot', s3_image_url)
        return s3_image_url
