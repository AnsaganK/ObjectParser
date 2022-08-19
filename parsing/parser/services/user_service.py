from mimesis import Person
from mimesis.enums import Gender

import random
import io


class GenerateUser():
    def __init__(self):
        pass

    def random_color(self):
        import random
        color = "#%06x" % random.randint(0, 0xFFFFFE)
        return color

    def generate_avatar(self, name_letters):
        from PIL import Image, ImageFont, ImageDraw
        width = 320
        height = 320
        img = Image.new('RGB', (width, height), color=(self.random_color()))
        draw_text = ImageDraw.Draw(img)
        font = ImageFont.truetype('static/fonts/Raleway-Regular.ttf', size=120)
        draw_text.text((width / 2, height / 2), name_letters, anchor='mm', font=font, fill=('#ffffff'))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return img_byte_arr

    def generate_data(self):
        person = Person('en')
        gender_choices = [Gender.FEMALE, Gender.MALE]
        random_gender = random.choice(gender_choices)
        email = person.email()

        full_name = person.full_name(gender=random_gender)
        username = full_name.replace(' ', '_')
        full_name = full_name.split(' ')
        first_name = full_name[0]
        last_name = full_name[-1]

        # password = User.objects.make_random_password()

        user_data = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'gender': random_gender.name,
            # 'password': password
        }
        return user_data

    def get_user(self):
        user_data = self.generate_data()
        name_letters = f'{user_data["first_name"][0]}.{user_data["last_name"][0]}'
        user_img = self.generate_avatar(name_letters)
        user_data['img'] = user_img
        return user_data

    def get_or_create_user(self):
        user_data = self.get_user()
        user = User.objects.get_or_create(username=user_data['username'])
        if not user[1]:
            return user[0]
        user = user[0]
        user.email = user_data['email']
        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        user.password = user_data['password']
        user.save()
        group = Group.objects.filter(name='User').first()
        if group:
            user.groups.add(group)
        user.profile.gender = user_data['gender']
        cloud_image = save_image(user_data['img'])
        user.profile.cloud_img = cloud_image
        user.save()
        return user
