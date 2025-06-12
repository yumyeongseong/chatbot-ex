import streamlit as st
from llm import stream_ai_message


st.set_page_config(page_title='전세사기피해 상담 챗봇', page_icon='⚖️')
st.title('⚖️전세사기피해 상담 챗봇')

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

        session_id = 'user-session'
        ai_message = stream_ai_message(user_question, session_id=session_id)

        with st.chat_message('ai'):
            ## AI 메시지 화면 출력
            ai_message = st.write_stream(ai_message)
        st.session_state.message_list.append({'role':'ai', 'content': ai_message})