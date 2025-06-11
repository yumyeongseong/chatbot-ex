import os

from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone


## 환경변수 읽어오기 ===================================================================
load_dotenv()


## LLM 함수 정의
def get_llm(model='gpt-4o'):
    llm = ChatOpenAI(model=model)
    return llm


## Database 함수 정의 =================================================================
def get_database():
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    
    ## 임베딩 모델 지정
    embedding = OpenAIEmbeddings(model='text-embedding-3-large')
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = 'law'

    ## 저장된 인덱스 가져오기 ========================================================
    database = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding,
    )
    
    return database

### Statefully manage chat history ###
store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

## retrievalQA 함수 정의 ==============================================================
def get_retrievalQA():
    LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')

    database = get_database()

   ### Contextualize question ###
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
    
    ## LLM 모델 지정
    llm = get_llm()

    # ## QA 체인 구성
    def format_docs(docs):
        return '\n\n'.join(doc.page_content for doc in docs)


    input_str = RunnableLambda(lambda x: x['input'])

    qa_chain = (
        {
            'context':input_str | database.as_retriever() | format_docs,
            'input': input_str,
            'chat_history': RunnableLambda(lambda x:x['chat_history'])
        }
        | qa_prompt
        | llm
        | StrOutputParser()
    )

    conversational_rag_chain = RunnableWithMessageHistory(
        qa_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    return conversational_rag_chain

## [AI message 함수 정의] ==================================
def get_ai_message(user_message, session_id='default'):
    qa_chain = get_retrievalQA()

    
    # ai_message = qa_chain.invoke(user_message)

    ai_message = qa_chain.invoke(
            {"input": user_message},
            config={"configurable": {"session_id": session_id}},
    )
    
    return ai_message


