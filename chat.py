import streamlit as st
from llm import stream_ai_message
import uuid


st.set_page_config(page_title='전세사기피해 상담 챗봇', page_icon='⚖️')
st.title('⚖️전세사기피해 상담 챗봇')

print('\n== start ==')
print('st.session_state ..', st.session_state)
##################################################################

# print('UUID>>>', uuid.uuid4())

## 세션 ID를 고유한 값으로 설정 ###################################
## [방법 1] F5 새로고침(F5)하면 새로 발급
# if 'session_id' not in st.session_state:
#     ## 세션 ID를 생성하여 저장
#     # st.session_state.session_id = str(uuid.uuid4())
#     st.session_state['session_id'] = str(uuid.uuid4())

#     ## 출력
#     print('st.session_state.session_id >>', st.session_state['session_id'])

## [방법 2] URL의 parameter에 저장
# query_params = st.query_params
# print('query_params >>', st.query_params)

# st.query_params.update({'age':39})

## Query prameter

print('st.query_param >>', st.query_params)
print('session_id 값 추출 1) >>', st.query_params['session_id'])
print('session_id 값 추출 2) >>', st.query_params.session_id)

query_params = st.query_params

if 'session_id' in query_params:
    session_id = query_params['session_id']
    print('URL에 session_id가 있다면, UUID를 가져와서 변수 저장')

else:
    session_id = str(uuid.uuid4())
    st.query_params.update({'session_id': session_id})
    print("URL에 session_id가 없다면, UUID를 생성하여 추가")



print('after) st.session_state ..', st.session_state)
##################################################################

## Streamlit 내부 세션에도 저장
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = session_id
    print('[Streamlit 내부 세션] st.session_state.session_id ..', st.session_state.session_id)
if 'message_list' not in st.session_state:
    st.session_state.message_list = []

## 이전 채팅 내용 화면에 출력(표시)
for message in st.session_state.message_list:
    with st.chat_message(message['role']):
        st.write(message['content'])

## 채팅 메시지 
placeholder='전세사기 피해와 관련된 질문을 해주세요.'

if user_question := st.chat_input(placeholder=placeholder): ## prompt 창
    ## 사용자 메시지
    with st.chat_message('user'):
        ## 사용자 메시지 화면 출력
        st.write(user_question)
    st.session_state.message_list.append({'role':'user','content':user_question})

    ## AI 메시지 
    with st.spinner('답변을 생성하는 중입니다.'):
        # ai_message = get_ai_message(user_question)

        # session_id = 'user-session'
        session_id = st.session_state.session_id
        ai_message = stream_ai_message(user_question, session_id=session_id)

        with st.chat_message('ai'):
            ## AI 메시지 화면 출력
            ai_message = st.write_stream(ai_message)
        st.session_state.message_list.append({'role':'ai', 'content': ai_message})