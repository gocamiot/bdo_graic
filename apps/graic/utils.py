import requests, re, os
import markdown2
from datetime import datetime
from apps.graic.models import AIPrePrompt, Graic, Chat, Agent
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import connection
from django.core.files import File

from openai import OpenAI

client = OpenAI(
    api_key=getattr(settings, 'OPENAI_API_KEY')
)

def pre_prompt_func(current_datetime):
    pre_prompt_qs = AIPrePrompt.objects.first()
    if not pre_prompt_qs:
        pre_prompt_qs = AIPrePrompt.objects.create()
    
    if isinstance(current_datetime, str):
        try:
            current_datetime = datetime.fromisoformat(current_datetime)
        except ValueError:
            current_datetime = datetime.now()

    formatted_date = current_datetime.strftime("%B %d, %Y")
    formatted_time = current_datetime.strftime("%I:%M %p")

    pre_prompt = (
        f"You are an {pre_prompt_qs.role}\n"
        f"Your name is {pre_prompt_qs.name}\n"
        f"Today's date is {formatted_date}\n"
        f"Current time is {formatted_time}\n"
    )

    return pre_prompt

def api_engine(prompt, is_online=False, llm="openai"):
    if not is_online:
        try:
            response = requests.post(
                'http://74.50.126.211:8001/chat',
                json={'prompt': prompt},
                timeout=600
            ).json().get('response', '')
        except requests.exceptions.RequestException as e:
            print(f"Error calling local API: {e}")
            response = ""
    else:
        if llm == "deepseek":
            try:
                response = requests.post(
                    'https://api.deepseek.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {settings.DEEPSEEK_API_KEY}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'deepseek-chat',
                        'messages': [{'role': 'user', 'content': prompt}],
                        'temperature': 0.7
                    },
                    timeout=600
                ).json()
                response = response.get('choices', [{}])[0].get('message', {}).get('content', '')

            except requests.exceptions.RequestException as e:
                print(f"Error calling DeepSeek API: {e}")
                response = ""
            
        elif llm == "openai":
            try:
                completion = client.chat.completions.create(
                    model="gpt-5-mini",
                    store=True,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                response = completion.choices[0].message.content
            except requests.exceptions.RequestException as e:
                print(f"Error calling OpenAI API: {e}")
                response = ""
        else:
            response = "Invalid llm"
    
    return response


def get_agents_from_db():
    agents = Agent.objects.all()
    agents_dict = {}

    for agent in agents:
        agents_dict[agent.name] = {
            "mcp": agent.manifest,
            "system_prompt": agent.system_prompt or "",
            "llm": agent.llm or "",
            "online": agent.online,
        }
    return agents_dict

def pick_agent_with_llm(prompt):
    agents = get_agents_from_db()
    orchestration_agent, _ = Agent.objects.get_or_create(
        name='orchestration_agent',
        defaults={
            'manifest': 'todo', 'system_prompt': 'todo', 'llm': 'openai'
        }
    )

    router_prompt = "Classify the user request into one of these agents:\n"
    for name, data in agents.items():
        router_prompt += f'- "{name}": {data["mcp"]}\n'

    router_prompt += f'\nUser prompt: "{prompt}"\n\nAnswer with only one word: one of {", ".join(agents.keys())}.'

    result = api_engine(router_prompt, is_online=orchestration_agent.online, llm=orchestration_agent.llm)

    for agent_name in agents.keys():
        if agent_name.lower() in result.lower():
            return agent_name

    return list(agents.keys())[0] if agents else None

def get_agent(agent_name: str):
    try:
        agent = Agent.objects.get(name=agent_name)
        return {
            "instruction": agent.manifest,
            "system_prompt": agent.system_prompt or "",
            "llm": agent.llm or "openai",
            "online": agent.online,
        }
    except Agent.DoesNotExist:
        return {
            "instruction": "You are an assistant. Answer the user query clearly.",
            "system_prompt": "",
            "llm": "openai",
            "online": True,
        }

def get_last_responses_summary(user_id, chat_id, last_n=4, llm="openai", is_online=True):
    chat = get_object_or_404(Chat, uuid=chat_id)
    last_responses = (
        Graic.objects.filter(user_id=user_id, chat=chat)
        .order_by('-id')[:last_n]
    )

    if not last_responses:
        return ""

    combined_text = ""
    for resp in reversed(last_responses):
        combined_text += f"Prompt: {resp.prompt}\nResponse: {resp.response}\n\n"

    summary_prompt = f"""
    Summarize the following conversation between user and assistant in a concise way, highlighting the key points:

    {combined_text}

    Summary:
    """

    summary = api_engine(summary_prompt, is_online=is_online, llm=llm)
    return summary.strip()

def aggregate_responses(final_response, prompt, user_id, chat_id, metadata, generated_file_path=None):
    chat = Chat.objects.get(uuid=chat_id)
    thinking_text = re.search(r'<think>(.*?)</think>', final_response, re.DOTALL)
    thinking_text = thinking_text.group(1).strip() if thinking_text else None
    cleaned_response = re.sub(r'<think>.*?</think>', '', final_response, flags=re.DOTALL)
    html_response = markdown2.markdown(cleaned_response, extras=["fenced-code-blocks"])

    graic = Graic.objects.create(
        user_id=user_id,
        chat=chat,
        time_take=metadata.get('time_taken'),
        is_dt=metadata.get('is_dt'),
        summary_response=metadata.get('summary_response'),
        prompt=prompt,
        response=html_response,
        thinking=thinking_text
    )
    
    if generated_file_path:
        agent_data = get_agent('sql_agent')
        filename_prompt = (
            f"Provide a short filename (without extension) for the following user request:\n"
            f"User Prompt: {prompt}\n"
            f"Filename should be concise, alphanumeric, and use underscores instead of spaces."
        )
        suggested_name = api_engine(filename_prompt, agent_data['online'], agent_data['llm']).strip()

        safe_name = re.sub(r"[^\w\-]", "_", suggested_name)
        final_filename = f"{safe_name or 'generated_file'}_{graic.id}.xlsx"

        with open(generated_file_path, 'rb') as f:
            graic.generated_file.save(final_filename, File(f))
        os.remove(generated_file_path)

    return html_response


# import spacy

# nlp = spacy.load("en_core_web_sm")

# WHITELIST_TERMS = {"sap", "api", "sql", "jwt", "ssl", "grc", "audit", "risk"}

def extract_keywords(text: str):
    return
    # doc = nlp(text)
    # keywords = set()

    # for ent in doc.ents:
    #     if ent.label_ in ("PERSON", "ORG", "GPE"):
    #         keywords.add(ent.text.lower())

    # for token in doc:
    #     if token.pos_ in ("NOUN", "PROPN", "VERB", "ADJ"):
    #         if not token.is_stop and token.is_alpha:
    #             keywords.add(token.lemma_.lower())

    # text_lower = text.lower()
    # for term in WHITELIST_TERMS:
    #     if term in text_lower:
    #         keywords.add(term)

    # return " ".join(sorted(keywords))


def extract_keywords_llm(text: str):
    prompt = f"Extract keywords from the text : {text}. As a response only return the keywords, no extra definations"
    response = api_engine(prompt, is_online=True, llm="openai")

    return response.lower()


# def extract_keywords(text: str):
#     doc = nlp(text)
#     keywords = [ent.text for ent in doc.ents if ent.label_ in ("ORG", "GPE", "PERSON")]
#     return " ".join(keywords)


# def extract_keywords(text: str, max_keywords: int = 5, ngram_size: int = 2) -> str:
#     kw_extractor = yake.KeywordExtractor(lan="en", n=ngram_size, top=max_keywords, dedupLim=0.9)
#     keywords = kw_extractor.extract_keywords(text)
#     seen = set()
#     cleaned = []
#     for kw, score in keywords:
#         if kw not in seen:
#             seen.add(kw)
#             cleaned.append(kw)
#     return " ".join(cleaned)

# import nltk
# from nltk.corpus import stopwords
# from nltk.tokenize import word_tokenize
# from collections import Counter
# import string

# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('averaged_perceptron_tagger')

# def extract_keywords(text: str, max_keywords: int = 5, ngram_size: int = 2) -> str:
#     # 1. Tokenize text
#     tokens = word_tokenize(text.lower())
    
#     # 2. Remove punctuation and stopwords
#     stop_words = set(stopwords.words("english"))
#     tokens = [t for t in tokens if t not in stop_words and t not in string.punctuation]
    
#     # 3. POS tagging - keep only nouns/adjectives (optional but improves relevance)
#     tagged_tokens = nltk.pos_tag(tokens)
#     filtered_tokens = [word for word, pos in tagged_tokens if pos.startswith('NN') or pos.startswith('JJ')]
    
#     # 4. Count frequencies
#     freq = Counter(filtered_tokens)
    
#     # 5. Form n-grams
#     ngrams = []
#     for i in range(len(filtered_tokens) - ngram_size + 1):
#         ngram = " ".join(filtered_tokens[i:i+ngram_size])
#         ngrams.append(ngram)
    
#     # Combine single words and ngrams
#     all_candidates = filtered_tokens + ngrams
#     candidate_freq = Counter(all_candidates)
    
#     # 6. Return top keywords
#     top_keywords = [kw for kw, _ in candidate_freq.most_common(max_keywords)]
    
#     return " ".join(top_keywords)


def search_model_vector(model, prompt_vector, fields, snapshot_value=None):
    field_list = ', '.join([f't."{field}"' for field in fields])
    table_name = model._meta.db_table

    query = f"""
        WITH q AS (
            SELECT '{prompt_vector}'::vector AS v
        )
        SELECT 
            t."ID",
            {field_list},
            ROUND(1 - (t.hash_data <=> q.v)::numeric, 3) AS similarity
        FROM public."{table_name}" t, q
    """
    
    if snapshot_value:
        query += f" WHERE loader_instance={snapshot_value}"
    
    query += " ORDER BY t.hash_data <=> q.v;"

    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
    
    return results


def search_model_fts(model, search_text, snapshot_value=None, fts_func='plainto_tsquery'):
    exclude_fields = ["loader_instance", "json_data", "hash_data", "fts"]

    table_name = model._meta.db_table.lower()
    fields = [f.name for f in model._meta.fields if f.name not in exclude_fields]
    field_list = ', '.join([f't."{field}"' for field in fields])

    search_text_escaped = search_text.replace("'", "''")

    query = f"""
        SELECT 
            t."ID",
            {field_list},
            ts_rank(t.fts, {fts_func}('english', '{search_text_escaped}')) AS rank
        FROM public."{table_name}" t
        WHERE t.fts @@ {fts_func}('english', '{search_text_escaped}')
    """

    if snapshot_value:
        query += f" AND t.loader_instance={snapshot_value}"

    query += " ORDER BY rank DESC;"

    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

    return results

