import os

from dotenv import load_dotenv
from langchain.chains import (create_history_aware_retriever,
                              create_retrieval_chain)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone


## 환경변수 읽어오기 ===================================================================
load_dotenv()

## LLM 생성 ============================================================================
def get_llm(model='gpt-4o'):
    llm = ChatOpenAI(model=model)
    return llm

## Embedding 설정 + Vector Store Index 가져오기 =========================================
def get_database():
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    
    ## 임베딩 모델 지정
    embedding = OpenAIEmbeddings(model='text-embedding-3-large')
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = 'law'

    ## 저장된 인덱스 가져오기 ==========================================================
    database = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding,
    )
    
    return database

## 세션별 히스토리 저장 ================================================================
store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

## 히스토리 기반 리트리버 ==============================================================
def get_history_retriever(llm, retriever):
    ### Contextualize question ###
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
    )

    return history_aware_retriever

def get_qa_prompt():
    system_prompt = (
        '''
        [identity]
        - 당신은 전세사기피해 법률 전문가 입니다.
        - [context]를 참고하여 사용자의 질문에 답변하세요.
        - 답변 할 때  '< xx법 xx조 xx항>' 형식으로 문단 마지막에 표시하세요.
        - 항목별로 표시해서 답변해주세요.
        - 전세사기피해 법률 이외에는 '답변 할 수 없습니다.' 답변하세요.

        [context]
        {context}
        '''
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    return qa_prompt

## 전체 chain 구성 ===============================================================
def build_conversational_chain():
    LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')

    ## LLM 모델 지정
    llm = get_llm()

    ## vector store에서 index 정보
    database = get_database()
    retriever = database.as_retriever(search_kwargs={'k':2})

    history_aware_retriever= get_history_retriever(llm,retriever)
    
    qa_prompt = get_qa_prompt()
    
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key='answer',
    ).pick('answer')

    return conversational_rag_chain

## [AI message 함수 정의] ==================================
def stream_ai_message(user_message, session_id='default'):
    qa_chain = build_conversational_chain()

    
    # ai_message = qa_chain.invoke(user_message)

    ai_message = qa_chain.stream(
            {"input": user_message},
            config={"configurable": {"session_id": session_id}},
    )
    print(f'대화이력 >> {get_session_history(session_id)}')
    print("==" * 60 + '\n')
    print(f'[stream_session_id 함수 내 출력 ] >> {session_id}')

    return ai_message


