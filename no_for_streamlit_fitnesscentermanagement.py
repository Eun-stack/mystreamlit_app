# 표준 라이브러리
import os
from collections import defaultdict
from datetime import datetime, timedelta, time
# 배포
import streamlit as st
# 데이터베이스
from supabase import create_client, Client
import uuid
# 환경변수
from dotenv import load_dotenv
#이메일 발송
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


#---------- 로컬에서 streamlit 실행 ----------
# cd 97-develop
# streamlit run FitnessCenterManagement.py


#---------- .env 파일 로드 ----------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

email_sender = os.getenv("GMAIL_EMAIL")
email_password = os.getenv("GMAIL_APP_PASSWORD")
smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT"))

#---------- 테이블 구조 ----------
#"""데이터베이스에 SQL문으로 직적 생성해야 함."""
#"""왜래키 조건을 중간에 추가해서 CREATE의 수정이 필요함"
membersT = '''
CREATE TABLE members (
    member_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    phone TEXT UNIQUE CHECK (phone ~ '^010\d{8}$'),
    membership_registration DATE,
    membership_expiration DATE,
    membership_level TEXT;
    email TEXT UNIQUE CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
    CONSTRAINT chk_members_phone_format CHECK (phone ~ '^010\d{8}$'),
    CONSTRAINT chk_members_membership_dates CHECK (membership_expiration >= membership_registration)
    CONSTRAINT chk_members_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
);'''


trainersT = '''
CREATE TABLE trainers (
    trainer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    phone TEXT,
    contract_start DATE,
    contract_end DATE,
    CONSTRAINT chk_trainers_contract_dates CHECK (contract_end >= contract_start)
);'''


gym_logsT = '''
CREATE TABLE gym_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    member_id UUID,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP
);
'''

add_pt_reservationT = '''
CREATE TABLE pt_reservations (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trainer_id UUID,
    member_id UUID,
    reservation_start TIMESTAMP,
    reservation_end TIMESTAMP,
    CONSTRAINT chk_reservation_datetime CHECK (reservation_end >= reservation_start)
);
'''

#---------- 예약 겹침 검사 ----------
def is_time_overlap(start1, end1, start2, end2):
    return max(start1, start2) < min(end1, end2)

#---------- PT 예약 가능 여부 검사 ----------
def check_pt_availability(trainer_id, member_id, new_start, new_end):
    trainer_data = supabase.table("pt_reservations").select("*").eq("trainer_id", trainer_id).execute()
    member_data = supabase.table("pt_reservations").select("*").eq("member_id", member_id).execute()

    for r in trainer_data.data:
        r_start = datetime.fromisoformat(r['reservation_start'])
        r_end = datetime.fromisoformat(r['reservation_end'])
        if is_time_overlap(r_start, r_end, new_start, new_end):
            return False
    for r in member_data.data:
        r_start = datetime.fromisoformat(r['reservation_start'])
        r_end = datetime.fromisoformat(r['reservation_end'])
        if is_time_overlap(r_start, r_end, new_start, new_end):
            return False
    return True

#---------- 전체 회원 목록 ----------
def load_members():
    return supabase.table("members").select("*").execute().data or []

#---------- 전체 트레이너 목록 ----------
def load_trainers():
    return supabase.table("trainers").select("*").execute().data or []

#---------- 예약 ----------
def add_pt_reservation(trainer_id, member_id, start_dt, end_dt):
    if not check_pt_availability(trainer_id, member_id, start_dt, end_dt):
        st.error("예약 시간이 겹칩니다. 다른 시간으로 선택해주세요.")
        return False
    supabase.table("pt_reservations").insert({
        "trainer_id": trainer_id,
        "member_id": member_id,
        "reservation_start": start_dt.isoformat(),
        "reservation_end": end_dt.isoformat()
    }).execute()
    st.success("PT 예약이 완료되었습니다.")
    return True

#---------- 트레이너 예약 시간표 ----------
def get_trainer_schedule(trainer_id, start_date, end_date):
    res = supabase.table("pt_reservations").select("*") \
        .eq("trainer_id", trainer_id) \
        .gte("reservation_start", start_date.isoformat()) \
        .lte("reservation_end", end_date.isoformat()) \
        .execute()

    reservations = res.data or []
    schedule = defaultdict(list)
    for r in reservations:
        start = datetime.fromisoformat(r['reservation_start'])
        end = datetime.fromisoformat(r['reservation_end'])
        schedule[start.date()].append((start, end, r['member_id']))

    for day in schedule:
        schedule[day].sort()
    return schedule

#---------- 이메일 발송 ----------
def send_email(recipient, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.sendmail(email_sender, recipient, msg.as_string())
        return True
    except Exception as e:
        st.error(f"이메일 전송 실패: {e}")
        return False


#---------- Streamlit 시작 ----------
st.title("🏋️ 피트니스센터 관리 시스템")

menu = st.sidebar.selectbox("메뉴 선택", [
    "회원 관리", "트레이너 관리", "운동 기록", "PT 예약", 
    "트레이너별PT 스케줄표", "회원별PT 스케쥴표", "이메일 발송"  # 추가됨
])

#---------- 회원 관리 ----------
if menu == "회원 관리":
    st.header("회원 목록")
    members = load_members()
    member_map = {m['member_id']: m for m in members}

    # 회원 리스트 표시
    for m in members:
        st.write(
            f"- {m['name']} / 전화: {m['phone']} / 이메일: {m.get('email', '없음')} / "
            f"등록일: {m['membership_registration']} / 만료일: {m['membership_expiration']} / "
            f"등급: {m.get('membership_level', '없음')}"
        )

    membership_levels = ["실버", "골드", "플래티넘", "다이아몬드"]

    # 회원 등록
    st.subheader("회원 등록")
    with st.form("member_form"):
        name = st.text_input("이름")
        phone = st.text_input("전화번호 (010xxxxxxxx)")
        email = st.text_input("이메일")  # ✅ 이메일 필드 추가
        reg_date = st.date_input("등록일", datetime.today())
        exp_date = st.date_input("만료일", datetime.today() + timedelta(days=30))
        membership_level = st.selectbox("멤버십 등급", membership_levels, index=0)
        submitted = st.form_submit_button("등록")

        if submitted:
            if exp_date < reg_date:
                st.error("만료일은 등록일 이후여야 합니다.")
            else:
                supabase.table("members").insert({
                    "name": name,
                    "phone": phone,
                    "email": email,  # ✅ 이메일 저장
                    "membership_registration": reg_date.isoformat(),
                    "membership_expiration": exp_date.isoformat(),
                    "membership_level": membership_level
                }).execute()
                st.success("회원 등록 완료")

    # 회원 정보 수정
    st.subheader("회원 정보 수정")
    selected_member_id = st.selectbox(
        "수정할 회원 선택",
        list(member_map.keys()),
        format_func=lambda x: member_map[x]['name']
    )

    if selected_member_id:
        member = member_map[selected_member_id]
        with st.form("edit_member_form"):
            edit_name = st.text_input("이름", member['name'])
            edit_phone = st.text_input("전화번호 (010xxxxxxxx)", member['phone'])
            edit_email = st.text_input("이메일", member.get('email', ''))  # ✅ 이메일 입력창
            edit_reg_date = st.date_input(
                "등록일",
                datetime.fromisoformat(member['membership_registration']) if member['membership_registration'] else datetime.today()
            )
            edit_exp_date = st.date_input(
                "만료일",
                datetime.fromisoformat(member['membership_expiration']) if member['membership_expiration'] else datetime.today() + timedelta(days=30)
            )

            current_level = member.get('membership_level')
            if current_level not in membership_levels:
                current_level = '실버'

            edit_membership_level = st.selectbox(
                "멤버십 등급", membership_levels, index=membership_levels.index(current_level)
            )

            edit_submitted = st.form_submit_button("수정 저장")
            if edit_submitted:
                if edit_exp_date < edit_reg_date:
                    st.error("만료일은 등록일 이후여야 합니다.")
                else:
                    supabase.table("members").update({
                        "name": edit_name,
                        "phone": edit_phone,
                        "email": edit_email,  # ✅ 이메일 저장
                        "membership_registration": edit_reg_date.isoformat(),
                        "membership_expiration": edit_exp_date.isoformat(),
                        "membership_level": edit_membership_level
                    }).eq("member_id", selected_member_id).execute()
                    st.success("회원 정보가 수정되었습니다.")

#---------- 트레이너 관리 ----------
elif menu == "트레이너 관리":
    st.header("트레이너 목록")
    trainers = load_trainers()
    trainer_map = {t['trainer_id']: t for t in trainers}

    for t in trainers:
        st.write(
            f"- {t['name']} / 전화: {t['phone']} / 계약: {t['contract_start']} ~ {t['contract_end']}"
        )

    st.subheader("트레이너 등록")
    with st.form("trainer_form"):
        name = st.text_input("이름")
        phone = st.text_input("전화번호")
        contract_start = st.date_input("계약 시작일", datetime.today())
        contract_end = st.date_input("계약 종료일", datetime.today() + timedelta(days=365))
        submitted = st.form_submit_button("등록")
        if submitted:
            if contract_end < contract_start:
                st.error("계약 종료일은 시작일 이후여야 합니다.")
            else:
                supabase.table("trainers").insert({
                    "name": name,
                    "phone": phone,
                    "contract_start": contract_start.isoformat(),
                    "contract_end": contract_end.isoformat()
                }).execute()
                st.success("트레이너 등록 완료")

    # 트레이너 정보 수정
    st.subheader("트레이너 정보 수정")
    selected_trainer_id = st.selectbox(
        "수정할 트레이너 선택",
        list(trainer_map.keys()),
        format_func=lambda x: trainer_map[x]['name']
    )

    if selected_trainer_id:
        trainer = trainer_map[selected_trainer_id]
        with st.form("edit_trainer_form"):
            edit_name = st.text_input("이름", trainer['name'])
            edit_phone = st.text_input("전화번호", trainer['phone'])
            edit_contract_start = st.date_input(
                "계약 시작일",
                datetime.fromisoformat(trainer['contract_start']) if trainer['contract_start'] else datetime.today()
            )
            edit_contract_end = st.date_input(
                "계약 종료일",
                datetime.fromisoformat(trainer['contract_end']) if trainer['contract_end'] else datetime.today() + timedelta(days=365)
            )

            edit_submitted = st.form_submit_button("수정 저장")
            if edit_submitted:
                if edit_contract_end < edit_contract_start:
                    st.error("계약 종료일은 시작일 이후여야 합니다.")
                else:
                    supabase.table("trainers").update({
                        "name": edit_name,
                        "phone": edit_phone,
                        "contract_start": edit_contract_start.isoformat(),
                        "contract_end": edit_contract_end.isoformat()
                    }).eq("trainer_id", selected_trainer_id).execute()
                    st.success("트레이너 정보가 수정되었습니다.")

#---------- 헬스장 출입 기록 ----------
elif menu == "운동 기록":
    st.header("헬스장 출입 등록")
    members = load_members()
    member_map = {m['name']: m['member_id'] for m in members}

    st.subheader("헬스장 출입 기록 조회")
    selected_member = st.selectbox("회원 선택 (조회용)", list(member_map.keys()), key="log_view")
    logs = supabase.table("gym_logs").select("*").eq("member_id", member_map[selected_member]).order("check_in_time", desc=True).execute().data
    if logs:
        for log in logs:
            in_time = datetime.fromisoformat(log['check_in_time']).strftime("%Y-%m-%d %H:%M")
            out_time = datetime.fromisoformat(log['check_out_time']).strftime("%Y-%m-%d %H:%M")
            st.write(f"- {in_time} ~ {out_time}")
    else:
        st.write("헬스장 출입 기록이 없습니다.")

    st.markdown("---")
    st.subheader("헬스장 출입 등록")
    selected_member_reg = st.selectbox("회원 선택 (등록용)", list(member_map.keys()), key="log_reg")
    check_in_date = st.date_input("입장 날짜", datetime.today())
    check_in_time = st.time_input("입장 시간", time(9, 0), key="in_time")
    check_out_date = st.date_input("퇴장 날짜", datetime.today())
    check_out_time = st.time_input("퇴장 시간", time(10, 0), key="out_time")
    check_in = datetime.combine(check_in_date, check_in_time)
    check_out = datetime.combine(check_out_date, check_out_time)

    if st.button("저장"):
        if check_out < check_in:
            st.error("퇴장 시간은 입장 시간 이후여야 합니다.")
        else:
            supabase.table("gym_logs").insert({
                "member_id": member_map[selected_member_reg],
                "name": selected_member_reg,
                "check_in_time": check_in.isoformat(),
                "check_out_time": check_out.isoformat()
            }).execute()
            st.success("출입 기록 저장 완료")

#---------- PT 예약 ----------
elif menu == "PT 예약":
    st.header("PT 예약 등록")
    members = load_members()
    trainers = load_trainers()
    member_map = {m['name']: m['member_id'] for m in members}
    trainer_map = {t['name']: t['trainer_id'] for t in trainers}

    selected_trainer = st.selectbox("트레이너 선택", list(trainer_map.keys()))
    selected_member = st.selectbox("회원 선택", list(member_map.keys()))

    st.subheader("예약 시간 선택")
    start_date = st.date_input("예약 시작 날짜", datetime.today())
    start_time = st.time_input("예약 시작 시간", time(9, 0))
    end_date = st.date_input("예약 종료 날짜", datetime.today())
    end_time = st.time_input("예약 종료 시간", time(10, 0))

    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)

    if st.button("예약 등록"):
        if end_dt <= start_dt:
            st.error("예약 종료 시간은 시작 시간 이후여야 합니다.")
        else:
            add_pt_reservation(
                trainer_map[selected_trainer],
                member_map[selected_member],
                start_dt,
                end_dt
            )

#---------- 트레이너별PT 스케줄표 ----------
elif menu == "트레이너별PT 스케줄표":
    st.header("트레이너별 PT 스케줄표 (60일)")
    trainers = load_trainers()
    trainer_map = {t['name']: t['trainer_id'] for t in trainers}
    selected_trainer = st.selectbox("트레이너 선택", list(trainer_map.keys()), key="calendar")

    today = datetime.today().date()
    end_day = today + timedelta(days=60)
    schedule = get_trainer_schedule(trainer_map[selected_trainer], today, end_day)

    korean_weekdays = ["일", "월", "화", "수", "목", "금", "토"]

    def get_korean_weekday(d):
        # datetime.weekday(): 월=0, ..., 일=6
        return korean_weekdays[(d.weekday() + 1) % 7]

    html = """
    <style>
    table.schedule-table {
        border-collapse: collapse;
        width: 100%;
        table-layout: fixed;
    }
    table.schedule-table th, table.schedule-table td {
        border: 1px solid #999;
        padding: 8px;
        vertical-align: top;
        text-align: left;
        word-wrap: break-word;
        max-width: 120px;
    }
    table.schedule-table th {
        background-color: #f2f2f2;
    }
    .reservation {
        background-color: #4caf50;
        color: white;
        padding: 2px 4px;
        margin: 2px 0;
        border-radius: 3px;
        display: block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 0.9em;
    }
    </style>
    """

    html += '<table class="schedule-table">'

    # 헤더: 요일 (일요일부터 토요일까지)
    html += '<tr>'
    for wd in korean_weekdays:
        html += f"<th>{wd}</th>"
    html += '</tr>'

    # 60일치 날짜를 7일씩 끊어서 출력
    for week_start in range(0, 60, 7):
        html += "<tr>"
        for i in range(7):
            d = today + timedelta(days=week_start + i)
            if d > end_day:
                html += "<td></td>"
                continue

            day_str = d.strftime("%m/%d")
            html += f"<td><b>{day_str}</b><br>"

            if d in schedule:
                for res in schedule[d]:
                    start_time = res[0].strftime("%H:%M")
                    end_time = res[1].strftime("%H:%M")
                    html += f'<span class="reservation">{start_time}~{end_time}</span>'
            else:
                html += '<span style="color:#888;">- 예약 없음 -</span>'

            html += "</td>"
        html += "</tr>"

    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)

#---------- 회원별PT 스케줄표 ----------
elif menu == "회원별PT 스케쥴표":
    st.header("회원별 PT 예약 스케줄표 (60일)")
    members = load_members()
    member_map = {m['name']: m['member_id'] for m in members}
    selected_member = st.selectbox("회원 선택", list(member_map.keys()), key="member_schedule")

    today = datetime.today().date()
    end_day = today + timedelta(days=60)

    # 회원 예약 스케줄 조회 함수 (트레이너 이름 포함)
    def get_member_schedule(member_id, start_date, end_date):
        data = supabase.table("pt_reservations")\
            .select("reservation_start, reservation_end, trainer_id, trainers(name)")\
            .eq("member_id", member_id)\
            .gte("reservation_start", start_date.isoformat())\
            .lte("reservation_start", end_date.isoformat())\
            .order("reservation_start")\
            .execute()


        res_list = data.data or []
        schedule = {}
        for r in res_list:
            start_dt = datetime.fromisoformat(r['reservation_start'])
            end_dt = datetime.fromisoformat(r['reservation_end'])
            date_key = start_dt.date()
            trainer_name = r['trainers']['name'] if r.get('trainers') else "알 수 없음"
            if date_key not in schedule:
                schedule[date_key] = []
            schedule[date_key].append((start_dt, end_dt, trainer_name))
        return schedule

    schedule = get_member_schedule(member_map[selected_member], today, end_day)

    korean_weekdays = ["일", "월", "화", "수", "목", "금", "토"]

    def get_korean_weekday(d):
        return korean_weekdays[(d.weekday() + 1) % 7]

    html = """
    <style>
    table.schedule-table {
        border-collapse: collapse;
        width: 100%;
        table-layout: fixed;
    }
    table.schedule-table th, table.schedule-table td {
        border: 1px solid #999;
        padding: 8px;
        vertical-align: top;
        text-align: left;
        word-wrap: break-word;
        max-width: 140px;
    }
    table.schedule-table th {
        background-color: #f2f2f2;
    }
    .reservation {
        background-color: #2196f3;
        color: white;
        padding: 2px 4px;
        margin: 2px 0;
        border-radius: 3px;
        display: block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 0.85em;
    }
    .trainer-name {
        font-weight: bold;
        font-size: 0.8em;
        color: #81b6fc;
    }
    </style>
    """

    html += '<table class="schedule-table">'

    # 헤더 - 요일 (일~토)
    html += '<tr>'
    for wd in korean_weekdays:
        html += f"<th>{wd}</th>"
    html += '</tr>'

    # 60일치 날짜, 7일씩 행 출력
    for week_start in range(0, 60, 7):
        html += "<tr>"
        for i in range(7):
            d = today + timedelta(days=week_start + i)
            if d > end_day:
                html += "<td></td>"
                continue

            day_str = d.strftime("%m/%d")
            html += f"<td><b>{day_str}</b><br>"

            if d in schedule:
                for res in schedule[d]:
                    start_time = res[0].strftime("%H:%M")
                    end_time = res[1].strftime("%H:%M")
                    trainer_name = res[2]
                    html += (
                        f'<span class="reservation">{start_time}~{end_time}</span>'
                        f'<div class="trainer-name">{trainer_name}</div>'
                    )
            else:
                html += '<span style="color:#888;">- 예약 없음 -</span>'

            html += "</td>"
        html += "</tr>"

    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)

#---------- 이메일발송 ----------
elif menu == "이메일 발송":
    st.header("📨 이메일 발송")
    
    members = load_members()
    member_map = {m['name']: m for m in members}
    member_names = list(member_map.keys())

    all_selected = st.checkbox("모든 회원에게 보내기")
    
    if all_selected:
        selected_members = member_names
    else:
        selected_members = st.multiselect("회원 선택", member_names)

    subject = st.text_input("제목")
    body = st.text_area("내용", height=200)
    
    if st.button("이메일 발송"):
        if not subject or not body:
            st.warning("제목과 내용을 모두 입력해주세요.")
        elif not selected_members:
            st.warning("발송할 대상을 선택해주세요.")
        else:
            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(email_sender, email_password)

                sent_count = 0
                skipped = []

                for name in selected_members:
                    member = member_map[name]
                    email = member.get('email')

                    if not email:
                        skipped.append(name)
                        continue

                    msg = MIMEMultipart()
                    msg["From"] = email_sender
                    msg["To"] = email
                    msg["Subject"] = subject

                    msg.attach(MIMEText(body, "plain"))
                    server.sendmail(email_sender, email, msg.as_string())
                    sent_count += 1

                server.quit()

                st.success(f"✅ 이메일 {sent_count}건 발송 완료!")
                if skipped:
                    st.warning(f"❗ 이메일 주소가 없어 발송되지 않은 회원: {', '.join(skipped)}")

            except Exception as e:
                st.error(f"이메일 발송 실패: {str(e)}")