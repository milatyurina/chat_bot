from enum import Enum

token = '1763762140:AAFcSmgGUZLHHgoBfsM1re5f7yd8vm2mSBo'
MWkey = '7e714f8c-5897-4ac7-8ea6-624947ba99a9'
db_file = 'sql_store.db'
heroku_name = 'https://my-happy-linguine-bot.herokuapp.com/'

well_done_img = 'https://pbs.twimg.com/media/DSglnFbX0AMGXBI.jpg'
not_so_well_img = 'https://ih1.redbubble.net/image.1559592237.3254/flat,750x,075,f-pad,750x1000,f8f8f8.jpg'
rigatoni_img = 'https://pbs.twimg.com/media/ET0HCS-XQAMB7PV.jpg'
pasta_img = ['https://res.cloudinary.com/teepublic/image/private/s--HH9vUdkj--/c_crop,x_10,y_10/c_fit,h_1109/c_crop,g_north_west,h_1260,w_945,x_-83,y_-76/co_rgb:ffffff,e_colorize,u_Misc:One%20Pixel%20Gray/c_scale,g_north_west,h_1260,w_945/fl_layer_apply,g_north_west,x_-83,y_-76/bo_126px_solid_white/e_overlay,fl_layer_apply,h_1260,l_Misc:Art%20Print%20Bumpmap,w_945/e_shadow,x_6,y_6/c_limit,h_1134,w_1134/c_lpad,g_center,h_1260,w_1260/b_rgb:eeeeee/c_limit,f_jpg,h_630,q_90,w_630/v1592710169/production/designs/11529008_0.jpg',
             'https://i.pinimg.com/originals/9c/28/40/9c2840b0401074f174752f9c4429fd26.jpg',
             'http://ae01.alicdn.com/kf/HTB1O0BfaiDxK1RjSsphq6zHrpXaw.jpg',
             'https://webattach.mail.yandex.net/message_part_real/pasta.png?exif_rotate=y&no_disposition=y&name=pasta.png&sid=YWVzX3NpZDp7ImFlc0tleUlkIjoiMTc4IiwiaG1hY0tleUlkIjoiMTc4IiwiaXZCYXNlNjQiOiJJWUd4bjVQMHB5dXlDRVFGL2piMDFRPT0iLCJzaWRCYXNlNjQiOiJEclJmYmNWRXgzS0RtTFFzM0szNnhHY2ZIb3VVaTBtd0RaTEppbTB5K3J0Y3ZKZTZYRUwxaG1Edjg3TGgyT214cUNQaFhoelJ6M2dvZHdpbElYcGpKb1ZBdnZVbE1YMm1KL0ZreTFHVTRESGJlWmhRem9GNklLd3ZaUURyLzhGayIsImhtYWNCYXNlNjQiOiJJcjJEMFEwUld1eitJaVdQNmtDR3pmR1ZCUmFjaHNheE02QU1IelB2YUJjPSJ9',
             'https://www.coolpun.com/images/coolpun/80/80ce162c94181ab837a2fe024c01f213.jpg',
             'https://i.pinimg.com/originals/a9/3b/62/a93b624f786f351bd9bca80174554d14.jpg']
profile_pic = 'https://cdn.powered-by-nitrosell.com/product_images/26/6472/large-EggLinguinei_02.jpg'

#states associated with videos
class States(Enum):
    START = '1'
    SEND_LINK = '2'
    SEND_EXERCISE = '3'
    EXERCISE_SENT = '4'
    EXERCISE_CHECKED = '5'

#states associated with dictionary look-ups
class LookUp(Enum):
    START = '1'
    LOOK_UP = '2'
    ENTER_WORD = '3'

#SQLite table columns
class DB_cols(Enum):
      ID = 'id'
      STATE = 'state'
      URL = 'url'
      EXERCISES = 'exercises'
      EX_KEY = 'ex_key'
      LOOKUP = 'lookup'
      WORD = 'word'
      POS = 'pos'
      COUNTER = 'counter'