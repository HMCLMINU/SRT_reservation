import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
import locale
from validation import *
import time
import threading

locale.setlocale(locale.LC_TIME, 'ko_KR.UTF-8')
 
class GUI:
    def __init__(self, root, srt):
        self.root = root
        self.srt = srt  # AppData 객체를 받음

        # GUI 설정
        self.root.title("SRT 예약하기")

        # 회원번호 입력
        tk.Label(root, text="회원번호 입력:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.id = tk.Entry(root)
        self.id.grid(row=0, column=1, padx=10, pady=10)

        # 비밀번호 입력
        tk.Label(root, text="비밀번호 입력:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.pw = tk.Entry(root)
        self.pw.grid(row=1, column=1, padx=10, pady=10)

        # 출발지 드롭다운 메뉴
        tk.Label(root, text="출발지:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.start = ttk.Combobox(root, values=station_list)
        self.start.set(station_list[0])  # 기본값으로 '수서' 설정
        self.start.grid(row=2, column=1, padx=10, pady=10)

        # 도착지 드롭다운 메뉴
        tk.Label(root, text="도착지:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.end = ttk.Combobox(root, values=dest_options)
        self.end.set(dest_options[2])  # 기본값으로 '광주송정' 설정
        self.end.grid(row=3, column=1, padx=10, pady=10)

        # 출발 시간 드롭다운 메뉴
        tk.Label(root, text="~시 이후:").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.start_time = ttk.Combobox(root, values=time_options)
        self.start_time.set(time_options[0])  # 기본값으로 '00' 설정
        self.start_time.grid(row=4, column=1, padx=10, pady=10)

        # 끝 시간 드롭다운 메뉴
        tk.Label(root, text="~시 이내:").grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.end_time = ttk.Combobox(root, values=et_options)
        self.end_time.set(et_options[0])  # 기본값으로 '06' 설정
        self.end_time.grid(row=5, column=1, padx=10, pady=10)

        # 객실 선택
        tk.Label(root, text="객실 선택:").grid(row=6, column=0, padx=10, pady=10, sticky="w")
        self.cabin = ttk.Combobox(root, values=cabin_options)
        self.cabin.set(cabin_options[1])  # 기본값으로 '특실' 설정
        self.cabin.grid(row=6, column=1, padx=10, pady=10)

        # 달력 위젯 만들기
        tk.Label(root, text="날짜를 선택하세요:").grid(row=7, column=0, padx=10, pady=10, sticky="w")
        self.cal = Calendar(root, selectmode="day", date_pattern="yyyy-mm-dd")  # 날짜 형식 설정
        self.cal.grid(row=7, column=1, padx=10, pady=10)

        # 제출 버튼
        self.btn_submit = tk.Button(root, text="제출", command=self.on_submit)
        self.btn_submit.grid(row=8, column=0, columnspan=2, pady=10)

        # 제출 결과를 보여줄 레이블
        self.label_result = tk.Label(root, text="")
        self.label_result.grid(row=9, column=0, columnspan=2, pady=10)

        # 예약 결과를 보여줄 레이블
        self.reserve_result = tk.Label(root, text="")
        self.reserve_result.grid(row=10, column=0, columnspan=2, pady=10)

    def on_submit(self):
        # 데이터를 AppData 객체에 저장
        self.srt.login_id = self.id.get()
        self.srt.login_psw = self.pw.get()
        self.srt.dpt_stn = self.start.get()
        self.srt.arr_stn = self.end.get()
        self.srt.dpt_tm = self.start_time.get()
        self.srt.end_tm = self.end_time.get()
        self.srt.seat_kind_str = self.cabin.get()

        year, month, day = self.cal.get_date().split('-')
        self.srt.dpt_dt = str(year)+str(month)+str(day)

        self.label_result.config(text=f"ID: {self.srt.login_id}\n PW: {self.srt.login_psw}\n 출발지: {self.srt.dpt_stn}\n도착지: {self.srt.arr_stn}\n"
                                f"출발 시간: {self.srt.dpt_tm}시 이후\n 종료 시간: {self.srt.end_tm}시 이내 \n 객실: {self.srt.seat_kind_str}\n 날짜: {self.srt.dpt_dt}\n"
                                f"SRT 예약을 시작합니다 ... \n")

        # self.srt.run()을 별도의 스레드에서 실행
        # time.sleep(2)
        booking_thread = threading.Thread(target=self.run_srt_booking)
        booking_thread.start()
            
    def run_srt_booking(self):
        # 이 부분에서 실제 예약 로직을 실행
        time.sleep(2)  # 예시로 2초간 대기
        self.srt.run()  # 실제 예약 실행

        # 예약 결과 처리 후 GUI 업데이트
        if self.srt.is_booked:
            self.update_result_label("예약 성공")
        else:
            self.update_result_label("예약 실패")

    def update_result_label(self, text):
        # GUI 업데이트는 메인 스레드에서 해야 하므로
        self.root.after(0, lambda: self.reserve_result.config(text=text))
