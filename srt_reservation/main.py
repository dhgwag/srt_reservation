# -*- coding: utf-8 -*-
import os
import time
from random import randint
from datetime import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, WebDriverException
from config import *
import telegram

from srt_reservation.exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
from srt_reservation.validation import station_list

# Chromedriver 없을 시 처음에는 자동으로 설치합니다.
chromedriver_path = r'C:\workspace\chromedriver.exe'


class SRT:
    def __init__(self):
        self.login_id = user_id
        self.login_psw = user_pw

        self.dpt_stn = dpt_stn
        self.arr_stn = arr_stn
        self.dpt_dt = dpt_date
        self.dpt_tm = dpt_time
        self.token = telegram_token
        self.id = telegram_id

        self.from_idx = from_idx
        self.to_idx = to_idx
        self.business = business
        self.economy = economy
        self.reserve = reserve
        self.driver = None

        self.is_booked = False  # 예약 완료 되었는지 확인용
        self.cnt_refresh = 0  # 새로고침 회수 기록

        self.check_input()

    def telegram_logging(self, msg):
        if self.token != "" and self.id != "":
            bot = telegram.Bot(token=self.token)
            bot.sendMessage(chat_id=self.id, text=msg)

    def check_input(self):
        if self.dpt_stn not in station_list:
            raise InvalidStationNameError(f"출발역 오류. '{self.dpt_stn}' 은/는 목록에 없습니다.")
        if self.arr_stn not in station_list:
            raise InvalidStationNameError(f"도착역 오류. '{self.arr_stn}' 은/는 목록에 없습니다.")
        if not str(self.dpt_dt).isnumeric():
            raise InvalidDateFormatError("날짜는 숫자로만 이루어져야 합니다.")
        try:
            datetime.strptime(str(self.dpt_dt), '%Y%m%d')
        except ValueError:
            raise InvalidDateError("날짜가 잘못 되었습니다. YYYYMMDD 형식으로 입력해주세요.")

    def run_driver(self):
        try:
            self.driver = webdriver.Chrome(executable_path=chromedriver_path)
        except WebDriverException:
            self.driver = webdriver.Chrome(ChromeDriverManager().install())


    def login(self):
        self.driver.get('https://etk.srail.co.kr/cmc/01/selectLoginForm.do')

        self.driver.implicitly_wait(15)
        self.driver.find_element(By.ID, 'srchDvNm01').send_keys(str(self.login_id))
        self.driver.find_element(By.ID, 'hmpgPwdCphd01').send_keys(str(self.login_psw))
        self.driver.find_element(By.XPATH, '//*[@id="login-form"]/fieldset/div[1]/div[1]/div[2]/div/div[2]/input').click()
        self.driver.implicitly_wait(5)
        return self.driver

    def check_login(self):
        time.sleep(3)
        menu_text = self.driver.find_element(By.CSS_SELECTOR, "#wrap > div.header.header-e > div.global.clear > div").text
        if "환영합니다" in menu_text:
            self.telegram_logging("로그인 성공. 예약을 시도합니다")
            return True
        else:
            self.telegram_logging("로그인 실패했지만, 예약을 시도합니다")
            return False

    def go_search(self):
        # 기차 조회 페이지로 이동
        self.driver.get('https://etk.srail.kr/hpg/hra/01/selectScheduleList.do')
        self.driver.implicitly_wait(5)

        # 출발지 입력
        elm_dpt_stn = self.driver.find_element(By.ID, 'dptRsStnCdNm')
        elm_dpt_stn.clear()
        elm_dpt_stn.send_keys(self.dpt_stn)

        # 도착지 입력
        elm_arr_stn = self.driver.find_element(By.ID, 'arvRsStnCdNm')
        elm_arr_stn.clear()
        elm_arr_stn.send_keys(self.arr_stn)

        # 출발 날짜 입력
        elm_dpt_dt = self.driver.find_element(By.ID, "dptDt")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_dt)
        Select(self.driver.find_element(By.ID, "dptDt")).select_by_value(self.dpt_dt)

        # 출발 시간 입력
        elm_dpt_tm = self.driver.find_element(By.ID, "dptTm")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_tm)
        Select(self.driver.find_element(By.ID, "dptTm")).select_by_visible_text(self.dpt_tm)

        # 인원 수 입력
        elm_adult_cnt = self.driver.find_element(By.NAME, "psgInfoPerPrnb1")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_adult_cnt)
        Select(self.driver.find_element(By.NAME, "psgInfoPerPrnb1")).select_by_value(str(adult_cnt))

        elm_child_cnt = self.driver.find_element(By.NAME, "psgInfoPerPrnb5")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_child_cnt)
        Select(self.driver.find_element(By.NAME, "psgInfoPerPrnb5")).select_by_value(str(child_cnt))

        elm_old_cnt = self.driver.find_element(By.NAME, "psgInfoPerPrnb4")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_old_cnt)
        Select(self.driver.find_element(By.NAME, "psgInfoPerPrnb4")).select_by_value(str(old_cnt))

        print("기차를 조회합니다")
        print(f"출발역:{self.dpt_stn} , 도착역:{self.arr_stn}\n날짜:{self.dpt_dt}, 시간: {self.dpt_tm}시 이후\n{self.from_idx}부터 {self.to_idx}까지 기차 중 예약")
        print(f"특실 예약: {self.business}    일반실 예약: {self.economy}   예약 대기 사용: {self.reserve}")

        # 조회하기 버튼 클릭
        self.driver.find_element(By.XPATH, "//input[@value='조회하기']").click()
        self.driver.implicitly_wait(5)
        time.sleep(1)

    def refresh_search_result(self):
        while True:
            while '접속대기' in self.driver.page_source:
                pass
            time.sleep(.8)
            for i in range(self.from_idx, self.to_idx+1):
                try:
                    business_seat = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(6)").text
                    economy_seat = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7)").text
                    reservation = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8)").text
                except StaleElementReferenceException:
                    business_seat = "매진"
                    economy_seat = "매진"
                    reservation = "매진"

                if business and "예약하기" in business_seat:
                    print("예약 가능 클릭")

                    # Error handling in case that click does not work
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(6) > a").click()
                    except ElementClickInterceptedException as err:
                        print(err)
                        self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(6) > a").send_keys(Keys.ENTER)
                    finally:
                        self.driver.implicitly_wait(3)

                    # 예약이 성공하면
                    if self.driver.find_elements(By.ID, 'isFalseGotoMain'):
                        self.is_booked = True
                        print("예약 성공")
                        self.telegram_logging("예약 성공")

                        return self.driver
                    else:
                        print("잔여석 없음. 다시 검색")
                        self.driver.back()  # 뒤로가기
                        self.driver.implicitly_wait(5)

                if economy and "예약하기" in economy_seat:
                    print("예약 가능 클릭")

                    # Error handling in case that click does not work
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7) > a").click()
                    except ElementClickInterceptedException as err:
                        print(err)
                        self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7) > a").send_keys(Keys.ENTER)
                    finally:
                        self.driver.implicitly_wait(3)

                    # 예약이 성공하면
                    if self.driver.find_elements(By.ID, 'isFalseGotoMain'):
                        self.is_booked = True
                        print("예약 성공")
                        self.telegram_logging("예약 성공")

                        return self.driver
                    else:
                        print("잔여석 없음. 다시 검색")
                        self.driver.back()  # 뒤로가기
                        self.driver.implicitly_wait(5)

                if reserve and "신청하기" in reservation:
                    # Error handling in case that click does not work
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8) > a").click()
                    except ElementClickInterceptedException as err:
                        print(err)
                        self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8) > a").send_keys(Keys.ENTER)
                    finally:
                        self.driver.implicitly_wait(3)

                    # 예약이 성공하면
                    if self.driver.find_elements(By.ID, 'agree'):
                        print("예약 대기 완료")
                        self.telegram_logging("예약 대기 완료")
                        self.is_booked = True
                        return self.driver
                    else:
                        print("잔여석 없음. 다시 검색")
                        self.driver.back()  # 뒤로가기
                        self.driver.implicitly_wait(5)

            if not self.is_booked:
                time.sleep(randint(2, 4))  # 2~4초 랜덤으로 기다리기
                
                # 다시 조회하기
                submit = self.driver.find_element(By.XPATH, "//input[@value='조회하기']")
                self.driver.execute_script("arguments[0].click();", submit)
                self.cnt_refresh += 1
                print(f"새로고침 {self.cnt_refresh}회")
                self.driver.implicitly_wait(10)
                time.sleep(0.5)
            else:
                return self.driver

    def run(self):
        self.run_driver()
        self.login()
        self.check_login()
        self.go_search()
        self.refresh_search_result()


# if __name__ == "__main__":
#     srt_id = os.environ.get('srt_id')
#     srt_psw = os.environ.get('srt_psw')
#
#     srt = SRT("동탄", "동대구", "20220119", "08")
#     srt.run(srt_id, srt_psw)