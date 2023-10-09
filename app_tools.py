from flask import Flask, request, jsonify, make_response, render_template, send_file, json
#from flask_sqlalchemy import SQLAlchemy 
 
import argparse

import os
import json
import multiline
import time

from sales_gpt_tools_cz import SalesGPT
from langchain.chat_models import ChatOpenAI
from traceback import print_exc, format_exc
from typing import Dict
from logger import time_logger

app = Flask(__name__)

cnt = 0
sales_agent_dict : Dict = {}

@app.route('/')
def index():
   #langchain_memory.set_user_id("abc123")
   return "Hello, World!"
   

@app.route('/index')
def index_html():
    """
    """
    return render_template('index.html')

@app.route('/chat.html')
def show_map():
    return send_file('/chat.html')

@time_logger
@app.route("/chatx", methods=["POST", "OPTIONS"])
def api_create_order():
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "POST": # The actual request following the preflight
        #order = OrderModel.create(...) # Whatever.
        try: 
            global cnt
            #global sales_agent
            global sales_agent_dict
            jjson = json.loads(request.get_data()) #json.loads(request.get_json(force=True, silent=True))
            print(f"REQUEST INPUT DATA {jjson}")
            msg = jjson['message']
            if msg.count("=") > 0:
                arr = msg.split("=")
                jjson['message'] = arr[0]
                jjson['chat_id'] = arr[1]
            else:
                # neni tam chat_id , dam default
                jjson['chat_id'] = 0
                jjson['message'] = jjson['message']
            print(f"REQUEST PARSED DATA {jjson}")

            human_input = jjson['message']
            if 'chat_id' in jjson.keys() and jjson['chat_id'] != 0:
                # chat_id je v requestu
                chat_id = int(jjson['chat_id'])
                if sales_agent_dict.get(chat_id) is not None:
                    #sales_agent = sales_agent_dict[chat_id]
                    print(f"OK nalezen agent chat_id: {chat_id} ")
                    print(f"DUMP sales_agent_dict= {sales_agent_dict}")
                    sales_agent = sales_agent_dict.get(chat_id)
                else:
                    # TODO ziskat chat z db a navazat
                    print(f"ERROR neexistuje  chat_id: {chat_id} v {sales_agent_dict}, startuju novy chat")
                    sales_agent = start_agent(config_path = 'agent_sales_setup_cz.json')
                    sales_agent.human_step("STARTED ROLE DUMSPANKU") #, sales_agent
            else:
                # jinak ho doplnime, spustim noveho agenta
                # sales_agent.chat_id = time.time() # pocet sekund jako unikantni id chatu
                # TODO - ?? jakeho spustit
                cnt = 0
                sales_agent = start_agent(config_path = 'agent_sales_setup_cz.json')
                sales_agent.human_step("STARTED ROLE DUMSPANKU") #, sales_agent

            print(f"HUMAN INPUT:  {human_input}")
            #human_input, sales_agent = process_commands(cmd = human_input, sales_agent = sales_agent)
            print(f"chatx SALES AGENT START {sales_agent}")
            cmd = human_input
            print(f"PROCESS COMMAND {cmd}", flush = True)
            if cmd.upper().count("/RESTART") > 0:
                print(f"RESTART {cmd}", flush=True)
                sales_agent.seed_agent()
                cnt = 0
                sales_agent.human_step("AGENT RESTARTED")
            elif cmd.upper().count("/ROLE PROFA") > 0:
                sales_agent = start_agent(config_path = 'agent_profa_setup_cz.json')
                cnt = 0
                sales_agent.human_step("START ROLE PROFA") #, sales_agent
            elif cmd.upper().count("/ROLE KEYMATE") > 0:
                sales_agent = start_agent(config_path = 'agent_sales_keymate_setup_cz.json')
                cnt = 0
                sales_agent.human_step("START ROLE KEYMATE") #, sales_agent
            elif cmd.upper().count("/ROLE DUMSPANKU") > 0:
                cnt = 0
                sales_agent = start_agent(config_path = 'agent_sales_setup_cz.json')
                sales_agent.human_step("STARTED ROLE DUMSPANKU") #, sales_agent

            elif cmd.upper().count("/ROLE ESTER") > 0:
                cnt = 0
                sales_agent = start_agent(config_path = 'agent_ester_setup_cz.json')
                sales_agent.human_step("STARTED ROLE ESTER")
            elif cmd.upper().count("/ROLE DOKLCHAT") > 0:
                cnt = 0
                sales_agent = start_agent(config_path = 'agent_sales_dokladovna_chat_setup_cz.json')
                sales_agent.human_step("STARTED ROLE DOKL CHAT")
            elif cmd.upper().count("/ROLE DOKLHOVOR") > 0:
                cnt = 0
                sales_agent = start_agent(config_path = 'agent_sales_dokladovna_hovor_setup_cz.json')
                sales_agent.human_step("STARTED ROLE DOKL HOVOR")
            else:
                sales_agent.human_step(human_input)

            #sales_agent.human_step(human_input)
            cnt=cnt+1
            add_msg = ""
            if cnt>=max_num_turns:
                add_msg = 'Dosažený maximální počet tahů - ukončení konverzace.'
                print(f"ADD MSG: {add_msg}")
            #TODO break
            # end conversation 
            step =  sales_agent.step()
            stage_id = sales_agent.determine_conversation_stage() #MS
            tool = sales_agent.check_tools()

            if '<END_OF_CALL>' in sales_agent.conversation_history[-1]:
                add_msg = f'{add_msg} Obchodní zástupce rozhodl, že je čas ukončit rozhovor.'
                print(f"ADD_MSG: {add_msg}")
            print(f"SALES STEP: {step} {add_msg} STAGE: {stage_id}")
            #order = { 'message' : f"cnt:{cnt} stage_id:{stage_id} = {step} {add_msg}" }
            order = { 'message' : f"{cnt} {step} {add_msg}", 'chat_id' : sales_agent.chat_id } 
            return _corsify_actual_response(jsonify(order))
        except Exception as e:
           tb_str = format_exc()
           print(f"ERROR chatx: {e}\n{tb_str}")
           order = { 'message' : f"ERROR chatx: {e}" , 'chat_id' : sales_agent.chat_id }
           return _corsify_actual_response(jsonify(order))
    else:
        raise RuntimeError("Weird - don't know how to handle method {}".format(request.method))
 
def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response




    """ end conversation 
   ##if '<END_OF_CALL>' in sales_agent.conversation_history[-1]:
   ##       print('Obchodní zástupce rozhodl, že je čas ukončit rozhovor.')
       #TODO break
   #human_input = input('Your response: ')
   #sales_agent.human_step(human_input)
   #print('='*10)
   m = langchain_memory._create_chat_memory()
   c = ConversationFlaskMemory(chat_memory=m, return_messages=True)
   conversation = ConversationChain(
       llm=llm,
       verbose=True,
       memory=c,
   )
   answer = conversation.predict(input=input)
   return jsonify({"message": answer})  
    """

@time_logger
def start_agent(config_path):
    """
    """
    global verbose
    global sales_agent_dict
    with open(config_path,'r') as f:
        config = json.load(f)
    with open(config['custom_prompt_file'], 'r') as f:
        config['custom_prompt'] = f.read()
    with open(config['stage_analyser_prompt_template_file'], 'r') as f:
        config['custom_stage_prompt'] = f.read()
    print(f'Loaged config {config_path} ', flush=True)
    
    print(f'Agent config {config}')
    sales_agent = SalesGPT.from_llm(llm, verbose=verbose, **config)
    sales_agent.config_path = config_path # jak identifikator profilu
    chat_id = sales_agent.seed_agent()
    sales_agent_dict[chat_id] = sales_agent
    print(f"START_AGENT SALES AGENT START chat_id: {chat_id} {sales_agent}")

    return sales_agent

   
if __name__ == '__main__':
   # import your OpenAI key (put in your .env file)
   with open('.env','r') as f:
       env_file = f.readlines()
   envs_dict = {key.strip("'") :value.strip("\n") for key, value in [(i.split('=')) for i in env_file]}
   os.environ['OPENAI_API_KEY'] = envs_dict['OPENAI_API_KEY']
  
   # Initialize argparse
   parser = argparse.ArgumentParser(description='Description of your program')
  
   # Add arguments
   parser.add_argument('--config', type=str, help='Path to agent config file', required = True)
   parser.add_argument('--verbose', type=bool, help='Verbosity', default=False)
   parser.add_argument('--max_num_turns', type=int, help='Maximum number of turns in the sales conversation', default=10)
  
   # Parse arguments
   args = parser.parse_args()
  
   # Access arguments
   config_path = args.config
   verbose = args.verbose
   max_num_turns = args.max_num_turns
  
   llm = ChatOpenAI(temperature=0.9, stop = "<END_OF_TURN>")
  
   #if config_path=='':
   #       print('No agent config specified, using a standard config', flush=True)
   #       sales_agent = SalesGPT.from_llm(llm, verbose=verbose)
   #       sales_agent.seed_agent()
   #else:
   #sales_agent = start_agent(config_path = config_path)
   """   #print(f"SALES AGENT START {sales_agent}")
       with open(config_path,'r') as f:
           config = json.load(f)
       with open(config['custom_prompt_file'], 'r') as f:
           config['custom_prompt'] = f.read()
       print(f'Loaged config {config_path} ', flush=True)
       print(f'Agent config {config}')
       sales_agent = SalesGPT.from_llm(llm, verbose=verbose, **config)
  
   sales_agent.seed_agent()   """
   app.run(debug=True, host='0.0.0.0',port=94)
