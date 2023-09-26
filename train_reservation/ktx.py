# -*- coding: utf-8 -*-
import os
import time
from random import randint
from datetime import datetime
from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, WebDriverException
from config import *
import telegram

from train_reservation.exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
from train_reservation.validation import station_list


class KTX:
    def __init__(self):
        self.login_id = ktx_user_id
        self.login_psw = ktx_user_pw

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
        # if self.dpt_stn not in station_list:
        #     raise InvalidStationNameError(f"출발역 오류. '{self.dpt_stn}' 은/는 목록에 없습니다.")
        # if self.arr_stn not in station_list:
        #     raise InvalidStationNameError(f"도착역 오류. '{self.arr_stn}' 은/는 목록에 없습니다.")
        if not str(self.dpt_dt).isnumeric():
            raise InvalidDateFormatError("날짜는 숫자로만 이루어져야 합니다.")
        try:
            datetime.strptime(str(self.dpt_dt), '%Y%m%d')
        except ValueError:
            raise InvalidDateError("날짜가 잘못 되었습니다. YYYYMMDD 형식으로 입력해주세요.")

    def run_driver(self):
        self.driver = webdriver.Chrome()

    def login(self):
        self.driver.get('https://www.letskorail.com/korail/com/login.do')

        self.driver.implicitly_wait(15)
        self.driver.find_element(By.ID, 'txtMember').send_keys(str(self.login_id))
        self.driver.find_element(By.ID, 'txtPwd').send_keys(str(self.login_psw))
        self.driver.find_element(By.CLASS_NAME, 'btn_login').find_element(By.XPATH, './a/img').click()
        self.driver.implicitly_wait(5)
        return self.driver

    def check_login(self):
        time.sleep(3)
        menu_text = self.driver.find_element(By.CLASS_NAME, 'log_nm').text
        if "환영합니다" in menu_text:
            self.telegram_logging("로그인 성공. 예약을 시도합니다")
            return True
        else:
            self.telegram_logging("로그인 실패했지만, 예약을 시도합니다")
            return False

    def go_search(self):
        # 기차 조회 페이지로 이동
        self.driver.get('https://www.letskorail.com/ebizprd/EbizPrdTicketpr21100W_pr21110.do')
        self.driver.implicitly_wait(5)

        # 출발지 입력
        elm_dpt_stn = self.driver.find_element(By.ID, 'start')
        elm_dpt_stn.clear()
        elm_dpt_stn.send_keys(self.dpt_stn)

        # 도착지 입력
        elm_arr_stn = self.driver.find_element(By.ID, 'get')
        elm_arr_stn.clear()
        elm_arr_stn.send_keys(self.arr_stn)

        # 출발 날짜 입력
        elm_dpt_dt = self.driver.find_element(By.ID, "s_year")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_dt)
        Select(self.driver.find_element(By.ID, "s_year")).select_by_value(self.dpt_dt[0:4])
        elm_dpt_dt = self.driver.find_element(By.ID, "s_month")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_dt)
        Select(self.driver.find_element(By.ID, "s_month")).select_by_value(self.dpt_dt[4:6])
        elm_dpt_dt = self.driver.find_element(By.ID, "s_day")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_dt)
        Select(self.driver.find_element(By.ID, "s_day")).select_by_value(self.dpt_dt[6:8])

        # 출발 시간 입력
        elm_dpt_tm = self.driver.find_element(By.ID, "s_hour")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_tm)
        Select(self.driver.find_element(By.ID, "s_hour")).select_by_value(self.dpt_tm)

        # 인원 수 입력
        elm_adult_cnt = self.driver.find_element(By.ID, "peop01")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_adult_cnt)
        Select(self.driver.find_element(By.ID, "peop01")).select_by_value(str(adult_cnt))

        elm_child_cnt = self.driver.find_element(By.ID, "peop02")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_child_cnt)
        Select(self.driver.find_element(By.ID, "peop02")).select_by_value(str(child_cnt))

        elm_old_cnt = self.driver.find_element(By.ID, "peop03")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_old_cnt)
        Select(self.driver.find_element(By.ID, "peop03")).select_by_value(str(old_cnt))

        print("기차를 조회합니다")
        print(f"출발역:{self.dpt_stn} , 도착역:{self.arr_stn}\n날짜:{self.dpt_dt}, 시간: {self.dpt_tm}시 이후\n{self.from_idx}부터 {self.to_idx}까지 기차 중 예약")
        print(f"특실 예약: {self.business}    일반실 예약: {self.economy}   예약 대기 사용: {self.reserve}")

        # 조회하기 버튼 클릭
        self.driver.find_element(By.CLASS_NAME, 'btn_inq').find_element(By.XPATH, './a/img').click()
        self.driver.implicitly_wait(5)
        time.sleep(1)

    def refresh_search_result(self):
        while True:
            while '대기순서' in self.driver.page_source:
                pass
            
            for i in range(self.from_idx, self.to_idx+1):
                if business:
                    try:
                        business_seat = self.driver.find_element(By.ID, 'tableResult').find_element(By.XPATH, f"./tbody/tr[{i}]/td[5]/a[1]/img").get_attribute("alt")
                    except:
                        business_seat = "매진"
                if economy:
                    try:
                        economy_seat = self.driver.find_element(By.ID, 'tableResult').find_element(By.XPATH, f"./tbody/tr[{i}]/td[6]/a[1]/img").get_attribute("alt")
                    except:
                        economy_seat = "매진"
                if reserve:
                    try:
                        reservation = self.driver.find_element(By.ID, 'tableResult').find_element(By.XPATH, f"./tbody/tr[{i}]/td[10]/a[1]/img").get_attribute("alt")
                    except:
                        reservation = "매진"

                if business and "예약하기" in business_seat:
                    print("특실 예약 가능 클릭")

                    # Error handling in case that click does not work
                    try:
                        self.driver.find_element(By.ID, 'tableResult').find_element(By.XPATH, f"./tbody/tr[{i}]/td[5]/a[1]/img").click()
                    except ElementClickInterceptedException as err:
                        print(err)
                        self.driver.find_element(By.ID, 'tableResult').find_element(By.XPATH, f"./tbody/tr[{i}]/td[5]/a[1]/img").send_keys(Keys.ENTER)
                    finally:
                        self.driver.implicitly_wait(3)

                    try:  # 경고창
                        for i in range(3):
                            time.sleep(1)
                            WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                            alert = self.driver.switch_to.alert

                            # 확인하기
                            alert.accept()
                            time.sleep(.5)
                    except:
                        pass

                    # 예약이 성공하면
                    if self.driver.find_elements(By.ID, 'btn_recalc'):
                        self.is_booked = True
                        print("예약 성공")
                        self.telegram_logging("예약 성공")

                        return self.driver
                    else:
                        print("잔여석 없음. 다시 검색")
                        self.driver.back()  # 뒤로가기
                        self.driver.implicitly_wait(5)

                if economy and "예약하기" in economy_seat:
                    print("일반실 예약 가능 클릭")

                    # Error handling in case that click does not work
                    try:
                        self.driver.find_element(By.ID, 'tableResult').find_element(By.XPATH, f"./tbody/tr[{i}]/td[6]/a[1]/img").click()
                    except ElementClickInterceptedException as err:
                        print(err)
                        self.driver.find_element(By.ID, 'tableResult').find_element(By.XPATH, f"./tbody/tr[{i}]/td[6]/a[1]/img").send_keys(Keys.ENTER)
                    finally:
                        self.driver.implicitly_wait(3)

                    try:  # 경고창
                        for i in range(3):
                            time.sleep(1)
                            WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                            alert = self.driver.switch_to.alert

                            # 확인하기
                            alert.accept()
                            time.sleep(.5)
                    except:
                        pass

                    # 예약이 성공하면
                    if self.driver.find_elements(By.ID, 'btn_recalc'):
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
                        self.driver.find_element(By.ID, 'tableResult').find_element(By.XPATH, f"./tbody/tr[{i}]/td[10]/a[1]/img").click()
                    except ElementClickInterceptedException as err:
                        print(err)
                        self.driver.find_element(By.ID, 'tableResult').find_element(By.XPATH, f"./tbody/tr[{i}]/td[10]/a[1]/img").send_keys(Keys.ENTER)
                    finally:
                        self.driver.implicitly_wait(3)

                    try:  # 경고창
                        for i in range(3):
                            time.sleep(1)
                            WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                            alert = self.driver.switch_to.alert

                            # 확인하기
                            alert.accept()
                            time.sleep(.5)
                    except:
                        pass

                    # 예약이 성공하면
                    if self.driver.find_elements(By.ID, 'agree'):
                        # self.driver.find_element(By.ID, 'agree').click()
                        # self.driver.find_element(By.ID, 'smsY').click()
                        # result = self.driver.switch_to_alert()
                        # result.accept()
                        # self.driver.find_element(By.ID, 'phoneNum1').send_keys(phoneNoMid)
                        # self.driver.find_element(By.ID, 'phoneNum2').send_keys(phoneNoEnd)
                        # self.driver.find_element(By.ID, 'diffSeatN').click()
                        # self.driver.find_element(By.ID, 'moveTicketList').click()
                        # result2 = self.driver.switch_to_alert()
                        # result2.accept()

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
                self.driver.find_element(By.CLASS_NAME, 'btn_inq').find_element(By.XPATH, './a/img').click()
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
        input()


# if __name__ == "__main__":
#     srt_id = os.environ.get('srt_id')
#     srt_psw = os.environ.get('srt_psw')
#
#     srt = SRT("동탄", "동대구", "20220119", "08")
#     srt.run(srt_id, srt_psw)