import time
import random

from selenium import webdriver
from selenium.webdriver.common.by import By

from constants import IS_SHORT
from ..utils import clicked_object, error_catching, function_error_catching
from ..utils import wait_and_get_element


class GetReviews:
    def __init__(self, driver):
        self.review_list = []
        self.driver = driver

    @error_catching('Получение отзывов', value=[])
    def get_reviews(self):
        self.get_page_review_button()
        self._get_reviews_objects()
        reviews = self.scrolled_driver()
        for review in reviews:
            self.review_detail(review)
        self.close_review_pages()
        return self.review_list

    @error_catching('Получить кнопку по отзывам')
    def get_page_review_button(self):
        review_button_classes = ['HHrUdb', 'Yr7JMd-pane-hSRGPd']
        # review_button = wait_and_get_element(self.driver, 'HHrUdb')
        self.driver.execute_script(
            f'let get_review_button = document.getElementsByClassName("HHrUdb")[0];'
            f'get_review_button.click()'
        )
        # clicked_object(review_button, 10)

    def _get_reviews_objects(self):
        review_card_classes = ['jftiEf', 'ODSEW-ShBeI']
        reviews = function_error_catching(
            func=lambda: wait_and_get_element(self.driver, 'jftiEf', many=True),
            value=[],
            message='Получить первые отзывы'
        )
        print(len(reviews))
        time.sleep(1)
        return reviews

    @error_catching('Ошибка при скролле по отзывам')
    def scrolled_driver(self):
        time.sleep(1)
        if IS_SHORT:
            self._scroll_review_block(count=1)
        else:
            self._scroll_review_block(count=2)
        reviews = self._get_reviews_objects()
        if IS_SHORT:
            reviews = reviews[:3]
        else:
            reviews = reviews[:random.randint(10, 20)]
        return reviews

    @error_catching('Скролл по отзывам')
    def _scroll_review_block(self, count=1):
        scroll_block_classes = ['DxyBCb', 'siAUzd-neVct section-scrollbox cYB2Ge-oHo7ed cYB2Ge-ti6hGc']
        for i in range(1, count + 1):
            self.driver.execute_script(
                f'let q_12 = document.getElementsByClassName("DxyBCb")[0];'
                f'q_12.scrollTo(0, q_12.scrollHeight);')
            time.sleep(1)

    @error_catching('Клик на кнопку ОТКРЫТЬ БОЛЬШЕ ТЕКСТА')
    def _review_more_button_click(self, review):
        review_id = review.get_attribute('data-review-id')
        self.driver.execute_script(
            f'let review = document.querySelector("div[data-review-id={review_id}]");'
            f'let more = review.getElementsByClassName("w8nwRe")[0].click();')
        time.sleep(1)

    @error_catching('Добавление отзыва в список отзывов', False)
    def check_review(self, review):
        rating = self._get_review_rating(review)
        text = self._get_review_text(review)
        if text:
            self.review_list.append({
                'rating': rating,
                'text': text
            })
            return True
        return False

    @error_catching('Получение текста из отзыва')
    def _get_review_text(self, review):
        self._review_more_button_click(review)
        review_text_classes = ['wiI7pd', 'ODSEW-ShBeI-text']
        text = function_error_catching(
            func=lambda: review.find_element(By.CLASS_NAME, 'wiI7pd').get_attribute('innerText'),
            value='',
            message='Получение текста из элемента отзыва'
        )
        return text

    @error_catching('Получение рейтинга из отзыва')
    def _get_review_rating(self, review: webdriver):
        try:
            rating_classes = ['kvMYJc', 'ODSEW-ShBeI-H1e3jb']
            rating = review.find_element(By.CLASS_NAME, 'kvMYJc')
            available_rating = len(rating.find_elements(By.CLASS_NAME, 'hCCjke'))
            checked_rating = len(rating.find_elements(By.CLASS_NAME, 'vzX5Ic'))
            if available_rating > 5:
                rating_coefficent = available_rating / 5
                checked_rating /= rating_coefficent
            rating = int(checked_rating)
        except:
            try:
                rating = len(review.find_elements(By.CLASS_NAME, 'ODSEW-ShBeI-fI6EEc-active'))
            except Exception as e:
                print('Ошибка при получении звезд: ', e.__class__.__name__)
                rating = 1
        return rating

    @error_catching('Получение детального отзыва')
    def review_detail(self, review):
        exception = 0
        while exception < 3:
            checked = self.check_review(review)
            if checked:
                break
            exception += 1

    @error_catching('Закрытие отзывов')
    def close_review_pages(self):
        self.driver.execute_script(
            'let close_b = document.getElementsByClassName("VfPpkd-icon-Jh9lGc"); close_b[0].click()')
