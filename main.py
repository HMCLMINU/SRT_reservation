import selenium
import time
import signal
import tkinter as tk

from random import randint

print(selenium.__version__)
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import *
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.options import Options

from exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
from validation import station_list
from gui import *

# service = Service(executable_path = ChromeDriverManager().install())
# service = Service()
# driver = webdriver.Chrome(service = service)
# driver.get('https://etk.srail.co.kr/cmc/01/selectLoginForm.do')
# driver.implicitly_wait(15)

# driver.find_element(By.ID, 'srchDvNm01').send_keys(str("1899758786"))
# driver.find_element(By.ID, 'hmpgPwdCphd01').send_keys(str("hmclab2020!@"))
# driver.find_element(By.CLASS_NAME, "submit.btn_pastel2.loginSubmit").send_keys(Keys.ENTER)

chrome_options = Options()
chrome_options.add_argument("--disable-popup-blocking")  # 팝업 및 알림 차단

class SRT:
    def __init__(self, dpt_stn="", arr_stn="", dpt_dt="", dpt_tm="", end_tm="", kind="", num_trains_to_check=8, want_reserve=False):
        """
        :param dpt_stn: SRT 출발역
        :param arr_stn: SRT 도착역
        :param dpt_dt: 출발 날짜 YYYYMMDD 형태 ex) 20220115
        :param dpt_tm: 출발 시간 hh 형태, 반드시 짝수 ex) 06, 08, 14, ...
        :param end_tm: 끝 시간 hh형태, 반드시 00:00형태 ...
        :param num_trains_to_check: 검색 결과 중 예약 가능 여부 확인할 기차의 수 ex) 2일 경우 상위 2개 확인
        :param want_reserve: 예약 대기가 가능할 경우 선택 여부
        :param seat_kind: 특실 or 일반실
        """
        self.login_id = None
        self.login_psw = None

        self.dpt_stn = dpt_stn
        self.arr_stn = arr_stn
        self.dpt_dt = dpt_dt
        self.dpt_tm = dpt_tm
        self.end_tm = end_tm
        self.seat_kind_str = kind

        if self.seat_kind_str == "일반실":
            self.seat_kind = 7
        elif self.seat_kind_str == "특실":
            self.seat_kind = 6
        else:
            print("잘못된 입력")

        self.num_trains_to_check = num_trains_to_check
        self.want_reserve = want_reserve
        self.driver = True

        self.is_booked = False  # 예약 완료 되었는지 확인용
        self.cnt_refresh = 0  # 새로고침 회수 기록
        
        self.check_input()
    
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
            self.driver = webdriver.Chrome(service = Service(), options=chrome_options)
        except WebDriverException:
            self.driver = webdriver.Chrome(service = Service(executable_path = ChromeDriverManager().install()), options=chrome_options)

    def set_log_info(self, login_id, login_psw):
        self.login_id = login_id
        self.login_psw = login_psw

    def login(self):
        self.driver.get('https://etk.srail.co.kr/cmc/01/selectLoginForm.do')
        self.driver.implicitly_wait(300)

        self.driver.find_element(By.ID, 'srchDvNm01').send_keys(str(self.login_id))
        self.driver.find_element(By.ID, 'hmpgPwdCphd01').send_keys(str(self.login_psw))
        self.driver.find_element(By.CLASS_NAME, "submit.btn_pastel2.loginSubmit").send_keys(Keys.ENTER)

    def go_search(self):
        self.driver.get('https://etk.srail.kr/hpg/hra/01/selectScheduleList.do')

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

        print("기차를 조회합니다")
        print(f"출발역:{self.dpt_stn} , 도착역:{self.arr_stn}\n날짜:{self.dpt_dt}, 시간: {self.dpt_tm}시 이후\n{self.num_trains_to_check}개의 기차 중 예약")
        print(f"예약 대기 사용: {self.want_reserve}")
        
        self.driver.find_element(By.CLASS_NAME, "btn_large.wx200.btn_burgundy_dark2.val_m.corner.inquery_btn").send_keys(Keys.ENTER)
        
    def book_ticket(self, str, seat, row, col):
        # seat는 일반석 검색 결과 텍스트
        if str in seat:
            print("예약 가능 합니다")
            # Error handling in case that click does not work
            try:
                self.driver.find_element(By.CSS_SELECTOR,
                                        f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({row}) > td:nth-child({col}) > a").send_keys(
                    Keys.ENTER)
                
            except ElementClickInterceptedException as err:
                print(err)
                self.driver.find_element(By.CSS_SELECTOR,
                                        f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({row}) > td:nth-child({col}) > a").send_keys(
                    Keys.ENTER)

            # 알람 처리
            if self.handle_alert():
                print("Alert detected and handled. Continuing...")

            # 예약이 성공하면
            if self.driver.find_elements(By.CLASS_NAME, 'btn_large.btn_blue_dark.val_m.mgr10'):
                self.is_booked = True
                print("예약 성공")
                return self.driver
            else:
                print("잔여석 없음. 다시 검색")
                self.driver.back()  # 뒤로가기 

    def handle_alert(self):
        try:
            # 알람 객체 가져오기
            alert = Alert(self.driver)
            print(f"Alert detected: {alert.text}")  # 알람 메시지 출력
            alert.accept()  # 알람 확인(닫기)
            return True  # 알람이 존재했음을 표시
        except NoAlertPresentException:
            # 알람이 없는 경우
            return False  # 알람이 없음을 표시
        
    def check_result(self):
        while True:
            for i in range(1, self.num_trains_to_check+1):
                try:
                    # 요소가 실제로 로드되었는지 확인, 최대 5분 기다림
                    departure_time = WebDriverWait(self.driver, 300).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(4) > em"))
                    ).text

                    if departure_time <= self.end_tm:
                        # print(f"출발 시간: {departure_time}")
                        
                        special_seat = WebDriverWait(self.driver, 300).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(6)"))
                        ).text

                        standard_seat = WebDriverWait(self.driver, 300).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7)"))
                        ).text

                        reservation = WebDriverWait(self.driver, 300).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8)"))
                        ).text

                except StaleElementReferenceException:
                    special_seat = "매진"
                    standard_seat = "매진"
                    reservation = "매진"

                if self.seat_kind_str == "일반실":
                    if self.book_ticket("예약하기", standard_seat, i, self.seat_kind):
                        return self.driver
                    
                elif self.seat_kind_str == "특실":
                    if self.book_ticket("예약 하기", special_seat, i, self.seat_kind):
                        return self.driver

                if self.want_reserve:
                    self.reserve_ticket(reservation, i)

            if self.is_booked:
                return self.driver
            else:
                # time.sleep(randint(1, 4))
                time.sleep(0.8)
                self.refresh_result()

    def refresh_result(self):
        self.driver.find_element(By.CLASS_NAME, "btn_large.wx200.btn_burgundy_dark2.val_m.corner.inquery_btn").send_keys(Keys.ENTER)
        # self.driver.execute_script("arguments[0].click();", submit)
        self.cnt_refresh += 1
        print(f"새로고침 {self.cnt_refresh}회")

    def reserve_ticket(self, reservation, i):
        if "신청하기" in reservation:
            print("예약 대기 완료")
            self.driver.find_element(By.CSS_SELECTOR,
                                     f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8) > a").send_keys(Keys.ENTER)
            self.is_booked = True
            return self.is_booked
            
    def run(self):
        self.run_driver()
        # GUI로 부터 받아옴
        # self.set_log_info(login_id, login_psw)
        self.login()
        self.go_search()
        self.check_result()


if __name__ == "__main__":
    
    root = tk.Tk()
    srt = SRT("수서", "광주송정", "20241207", "00", "10:00", "특실")
    gui = GUI(root, srt)  # GUIApp에 AppData 객체 전달
    root.mainloop()

    # srt_id = "1899758786"
    # srt_psw = "hmclab2020!@"

    # srt = SRT("수서", "광주송정", "20241207", "00", "10:00", "특실")
    # srt.run(srt_id, srt_psw)

    # print("결제 후 프로그램을 Enter를 눌러 프로그램을 종료하세요.")
    # input()  # 사용자가 Enter를 누를 때까지 대기
    # print("Program terminated.")