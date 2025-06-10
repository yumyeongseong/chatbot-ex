import os

from dotenv import load_dotenv
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone


## [AI message 함수 정의] ##############################
def get_ai_meassge(user_meassge):
   
    ## 환경변수 읽어오기 ###########################################################
    load_dotenv()
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')

    ## 임베딩 -> 벡터 스토어(데이터베이스)에서 인덱스 가져오기 #####################
    ## 임베딩 모델 지정
    embedding = OpenAIEmbeddings(model='text-embedding-3-large')
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = 'law'

    ## 저장된 인덱스 가져오기 ######################################################
    database = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding,
    )

    ## RetrievalQA #################################################################
    llm = ChatOpenAI(model='gpt-4o')
    prompt = hub.pull('rlm/rag-prompt')

    def format_docs(docs):
        return '\n\n'.join(doc.page_content for doc in docs)

    qa_chain = (
        {
            'context': database.as_retriever() | format_docs,
            'question': RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # qa_chain.invoke('전세사기피해자 대상을 알려주세요.')
    ai_message = qa_chain.invoke(user_meassge)
    return ai_message

