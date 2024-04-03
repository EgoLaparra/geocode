import argparse
import openai               # pip install openai
import tiktoken             # pip install tiktoken
import os
import json
import time
import re
import json

from requests.exceptions import ChunkedEncodingError

from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    wait_random_exponential,
)


# Tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

# OpenAI API Key
try:
    key_file = "api_key"
    with open(key_file) as f:
        OPENAI_API_KEY = f.read().strip()
    openai.api_key = OPENAI_API_KEY
except:
    pass

openai.api_key = openai.api_key or os.getenv("OPENAI_API_KEY")

# arg parser
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", type=str, default="parsed_data.txt")
    parser.add_argument("--output_folder", type=str, default="../gpt-4-output")
    parser.add_argument("--model", type=str, default="gpt-4-1106-preview")

    args = parser.parse_args()
    return args


# Get the number of tokens for a string, measured using tiktoken
def getTokenLength(strIn):
    tokens = tokenizer.encode(strIn)
    numTokens = len(tokens)
    return numTokens


# A wrapper for getResponseHelper, that continues to retry for large replies that timeout after 300 seconds.
def getResponse(prompt:str, maxTokensOut:int, model:str, maxRetries=4):
    numRetries = 0
    delay_base = 10
    totalResponse = ""
    while (numRetries <= maxRetries):
        responseStr, err = getResponseHelper(prompt, maxTokensOut, model)
        totalResponse += responseStr

        if err == '':
            print("Success -- break.")
            break
        elif err == 'TimeOut':
            print("getResponse: Retrying (attempt " + str(numRetries) + " / " + str(maxRetries) + ")")
            numRetries += 1
            #prompt += "####---BREAK---####\n" +     # Just for debugging
            prompt += responseStr
        elif err == 'RateLimitError':
            print("getResponse: Retrying (attempt " + str(numRetries) + " / " + str(maxRetries) + ")")
            delay = delay_base * (2 ** numRetries)
            numRetries += 1
            time.sleep(delay)
        else:
            # break if caught unknown error
            print(f"getResponse: {err}")
            break


    numTokens = getTokenLength(totalResponse)
    print("getResponse: Total tokens generated: " + str(numTokens))

    return totalResponse

# @retry(
#     reraise=True,
#     stop=stop_after_attempt(100),
#     wait=wait_exponential(multiplier=1, min=4, max=10),
#     retry=(
#         retry_if_exception_type(openai.error.Timeout)
#         | retry_if_exception_type(openai.error.APIError)
#         | retry_if_exception_type(openai.error.APIConnectionError)
#         | retry_if_exception_type(openai.error.RateLimitError)
#     ),
# )
def getResponseHelper(prompt:str, maxTokensOut:int, model:str):
    messages=[{"role": "system", "contant": "You are CodeGPT, a super-intelligent AI model that generates solutions to coding problems."},
               {"role": "user", "content": prompt}]

    # response = openai.ChatCompletion.create(
    #     model="gpt-4",
    #     max_tokens=100,
    #     temperature=0.1,
    #     top_p=1,
    #     frequency_penalty=0.0,
    #     presence_penalty=0.0,
    #     messages = messages)

    numPromptTokens = getTokenLength(prompt)
    if model == "gpt-4-32k":
        MODEL_MAX_TOKENS = 31000
    elif model == "gpt-4":
        MODEL_MAX_TOKENS = 8100
    else: # "gpt-4-1106-preview"
        MODEL_MAX_TOKENS = 4000
    # MODEL_MAX_TOKENS = 31000 if model == "gpt-4-32k" else 8100
    maxPossibleTokens = MODEL_MAX_TOKENS - numPromptTokens
    if (maxTokensOut > maxPossibleTokens):
        print("Warning: maxTokensOut is too large given the prompt length (" + str(numPromptTokens) + ").  Setting to max generation length of " + str(maxPossibleTokens))
        maxTokensOut = maxPossibleTokens

    # Record start time of request
    startTime = time.time()
    try:
        # Collect the stream
        collectedChunks = []
        collectedMessages = []
        responseStr = ""
        err = ""
        if openai.api_type == "azure":
            # When using the Azure API, we need to use engine instead of model argument.
            response = openai.ChatCompletion.create(
                engine=model,
                max_tokens=maxTokensOut,
                temperature=0.0,
                top_p=1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                messages=[{"role": "user", "content": prompt}],
                stream=True    # Stream the response, with the hopes of preventing timeouts
            )
        else:
            response = openai.ChatCompletion.create(
                #model="gpt-3.5-turbo",
                model=model,      # 8k token limit
                #model="gpt-4-32k-0314",
                max_tokens=maxTokensOut,
                temperature=0.0,
                top_p=1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                messages=[{"role": "user", "content": prompt}],
                stream=True    # Stream the response, with the hopes of preventing timeouts
            )




        for chunk in response:
            # Calculate time since start of request
            deltaTime = time.time() - startTime

            collectedChunks.append(chunk)
            chunkMessage = chunk['choices'][0]['delta']
            collectedMessages.append(chunkMessage)

            if "content" in chunkMessage:
                responseStr += chunkMessage["content"]

            # Display progress
            numTokens = getTokenLength(responseStr)
            # Calculate transmission rate
            if (deltaTime > 0):
                transmissionRate = numTokens / deltaTime
            else:
                transmissionRate = 0

            # Update every 25 tokens
            if (numTokens % 25 == 0):
                # Display to 2 decimal places
                transmissionRate = round(transmissionRate, 2)
                deltaTime = round(deltaTime, 2)
                print("Received " + str(numTokens) + " tokens after " + str(deltaTime) + " seconds (" + str(transmissionRate) + " tokens/sec)")
    except openai.error.RateLimitError as e:
        print(e)
        err = "RateLimitError"
        return responseStr, err
    except openai.error.Timeout as e:
        print(e)
        err = "TimeOut"
        return responseStr, err
    # When timeout, we practically received this error instead of the openai timeout error
    except ChunkedEncodingError as e:
        print(e)
        err = "TimeOut"
        return responseStr, err
    except openai.error.APIError as e:
        #Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e}")
        return responseStr, "APIError"
    except openai.error.APIConnectionError as e:
        #Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        return responseStr, "APIConnectionError"
    except openai.error.InvalidRequestError as e:
        #Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API invalid Request: {e}")
        return responseStr, "InvalidRequestError"
    except openai.error.ServiceUnavailableError as e:
        #Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API sevice unavailable: {e}")
        return responseStr, "ServiceUnavailableError"



    # Print final rate
    deltaTime = time.time() - startTime
    numTokens = getTokenLength(responseStr)
    # Calculate transmission rate
    if (deltaTime > 0):
        transmissionRate = numTokens / deltaTime
    else:
        transmissionRate = 0
    # Display to 2 decimal places
    transmissionRate = round(transmissionRate, 2)
    deltaTime = round(deltaTime, 2)
    print("SUMMARY: Received a total of " + str(numTokens) + " tokens after " + str(deltaTime) + " seconds (" + str(transmissionRate) + " tokens/sec)")

    #return response
    return responseStr, err


# Load a python program from a file into a string, and count its tokens using tiktoken
def loadProgram(filename):
    programStr = ""
    with open(filename, 'r') as f:
        programStr = f.read()

        lines = programStr.splitlines()
        program = ""
        for line in lines:
            program += line + "\n"


    tokens = tokenizer.encode(programStr)
    numTokens = len(tokens)

    return program, numTokens


# Postprocessing model response, keep only the code chunck ```python ```
def postProcess(raw_response):
    raw_code_lines = raw_response.split('\n')
    code_all = ''
    start = False
    # found_main = False
    for n, line in enumerate(raw_code_lines):
        if line.strip() == '```':
            if not start:
                code_all = '\n'.join(raw_code_lines[:n])
            break

        if start:
            code_all += line
            code_all += '\n'

        if line.strip() == "```python":
            start = True

    if code_all == '':
        code_all = raw_response

    return code_all

# Parse the parser preprocessing output to get the input data
def parse_input(data_file):
    data_all = []
    data_filtered = []
    ids = []
    ids_filtered = []
    with open(data_file) as f:
        data = []
        data_id = ''
        for line in f:
            if line.strip() == "" and len(data)>0:
                sentence = " ".join(data)
                assert data_id != ''
                if "TARGET" in sentence:
                    data_filtered.append((data_id, sentence))
                data_all.append((data_id, sentence))
                data = []
                data_id = ''
            elif line.strip().startswith("[INPUT]"):
                data.append(line.strip()[7:])
            elif not line.startswith('\t') and line.strip() != "":
                data_id = line.strip()

    return data_all, data_filtered

def clean_response(raw_response):
    response_out = raw_response

    # Remove white spaces
    response_out = response_out.replace(' ', '')

    # # wrap reference ids with SimpleLocation and GeoLocation
    # all_refs = re.findall(r'OSM[0-9_]+', raw_response)
    # for ref in set(all_refs):
    #     response_out = response_out.replace(ref, f"GeoLocation({ref[3:]})")

    # clean up quotes around units and geocardinals
    units_to_clean = ["KM", "MI", "NMI", "S","N","E","W","SW","SE","NW","NE","C"]
    units_to_clean_lower = [u.lower() for u in units_to_clean]
    units_to_clean += units_to_clean_lower
    for unit in units_to_clean:
        if f"\"{unit}\"" in response_out:
            response_out = response_out.replace(f"\"{unit}\"", unit)
        if f"'{unit}'" in response_out:
            response_out = response_out.replace(f"'{unit}'", unit)

    return response_out




#
#   Main
#


def main():
    args = parse_args()

    # _, filtered = parse_input(args.input_file)

    with open(args.input_file) as f:
        lines = f.readlines()

    filtered = []
    for line in lines:
        data_id, data = line.split("\t")
        if "TARGET" not in data:
            print(line)
            continue
        else:
            filtered.append((data_id.strip(), data.strip()))


    responses = {}
    i = 0
    # while i<len(filtered):
    while i<10:
        # 'DeveloperGPT' prompt from @skirano
        prompt = "You are DeveloperGPT, the most advanced AI developer tool on the planet.  You answer any coding question, and provide real useful example code using code blocks.  Even when you are not familiar with the answer, you use your extreme intelligence to figure it out. \n"

        prompt += "Given a text description of the target location, your task is to describe the position of the target location by generating operators that describes the relation between reference locations and the target location.\n"
        prompt += "Here are the pre-defined operators. These operators are Python functions, you should call these functions following Python syntax. \n"
        prompt += "GeoCardinal(s): The input string s represents a direction. s can be N, S, E, W, NE, NW, SE, SW, C. C is short for center."
        prompt += "SubLocation(r1, geocardinal): The target is inside the reference location r1. geocardinal is None or an output from the GeoCardinal operator. It represents the target's relative location inside r1. For example, SubLocation(r1, GeoCardinal(NW)) means the target is in the north-western part of r1. geocardinal should be None if not specified in the text.\n"
        prompt += "Between(r1, r2): The target is between reference location r1 and r2.\n"
        prompt += "Intersection(r1, r2, ...): The target region in the intersection of all reference locations r1, r2... in the arguments.\n"
        prompt += "Union(r1, r2, ...): The target region is the union of reference locations r1, r2... in the arguments.\n"
        prompt += "Adjacent(r1): The target location shares some part of the border with the reference location r1.\n"
        prompt += "Distance(r1, D, U, geocardinal): The distance between the target and the reference r1 is D, and the unit of D is U. geocardinal is None or an output from the GeoCardinal operator. It represents the target's relative location inside r1. For example, Distance(r1, D, 'KM', GeoCardinal(SE)) means the target is D KM south-east of r1. The unit can only be 'KM', 'MI' or 'NMI'. Note U should be a Python string so there should be quotes. geocardinal should be None if not specified in the text.\n"

        prompt += "Here are two examples, in which TARGET represents the target location and OSMXXXX represents reference locations. Note that you do not need to use all reference locations. Do not use locations that are not reference locations as your operator arguments. Do not use TARGET in your response.\n"

        prompt += "Example 1:\n"
        prompt += "The TARGET was the residence of Vestal Virgins, located behind the circular OSM1001 at the eastern edge of the OSM1002, between the OSM1003 and the OSM1004.\n"
        prompt += "The expected output is:\n"
        prompt += "Intersection(Intersection(Adjacent(OSM1001), SubLocation(OSM1002, GeoCardinal(E))),Between(OSM1003, OSM1004)).\n"
        prompt += "\n"

        prompt += "Example 2:\n"
        prompt += "The ruins of TARGET, the 12th century family castle of the counts of Sayn and Sayn-Wittgenstein, are in Sayn, part of the borough of OSM1001 on the OSM1002, between OSM1003 and OSM1004 in the county of OSM1005 in the German state of OSM1006.\n"
        prompt += "The expected output is:\n"
        prompt += "SubLocation(OSM1001)\n"

        prompt += "Example 3. Note the geocardinal in SubLocation is relative to reference location, not the target location:\n"
        prompt += "TARGET is a lake in OSM1795721 and OSM1795711 counties in west-central OSM316967611_165471. The town of OSM151758007_137058 is situated on the southwest shore of the lake.\n"
        prompt += "The expected output is:\n"
        prompt += "Intersection(Union(SubLocation(OSM1795721), SubLocation(OSM1795711)), Adjacent(OSM151758007_137058, GeoCardinal(NE)))\n"

        prompt += "Example 4:\n"
        prompt += "TARGET is a nuclear power plant located in the town of OSM1001 in OSM1002's OSM1003, on the southern shore of the OSM1004, some 70 kilometres (43 mi) to the west of the city centre of OSM1005.\n"
        prompt += "The expected output is:\n"
        prompt += "Intersection(SubLocation(OSM1001), Adjacent(OSM1004, GeoCardinal(S)), Distance(OSM1005, 70, 'KM', GeoCardinal(W)))\n"

        prompt += "Example 5:\n"
        prompt += "TARGET is a gulf that connects the OSM1002 with the OSM1003, which then runs to the OSM1004. It borders OSM1005 and OSM1006 on the north, OSM1007 on the south, and the OSM1008 on the west.\n"
        prompt += "The expected output is:\n"
        prompt += "Intersection(Between(OSM1002, OSM1003), Union(Adjacent(OSM1005, GeoCardinal(S)), Adjacent(OSM1006, GeoCardinal(S))), Adjacent(OSM1007, GeoCardinal(N)),Adjacent(OSM1008, GeoCardinal(E)))\n"

        prompt += "Example 6:\n"
        prompt += "The early fifteenth century TARGET, spans the OSM1002 at OSM1003, OSM1004. It is an arch bridge with seventeen arches, originally built from limestone and sandstone. The TARGET underwent significant changes in the 19th century, with a widening project in 1818 that used wood being superseded in 1874 with the use of brick. It is Grade I listed and a Scheduled Ancient Monument.\n"
        prompt += "The expected output is:\n"
        prompt += "Intersection(SubLocation(OSM1002), OSM1003)\n"

        prompt += "Example 7:\n"
        prompt += "Located on the southwestern slopes of the OSM1001 mountains, TARGET is noted for its attractive scenery. TARGET is located approximately 10 km to the west of OSM1002. OSM1003, the state capital of OSM1006, is about 25 km away, while the OSM1004, the state capital of OSM1005, is about 30 km away.\n"
        prompt += "The expected output is:\n"
        prompt += "Intersection(SubLocation(OSM1001, GeoCardinal(S)), Distance(OSM1002, 10, 'KM', GeoCardinal(W)), Distance(OSM1003, 25, 'KM'), Distance(OSM1005, 30, 'KM'))\n"

        prompt += "Example 8:\n"
        prompt += "TARGET is located in OSM1001. The nuclear power plant is located 40 miles (64 km) southwest of OSM1002 and about 60 miles (97 km) southwest of OSM1003. It relies on nearby OSM1004 for cooling water. The plant has about 1,300 employees and is operated by Luminant Generation, a subsidiary of Vistra Energy. </p>\n"
        prompt += "The expected output is:\n"
        prompt += "Intersection(SubLocation(OSM1001), Distance(OSM1002, 40, 'MI', GeoCardinal(SW)), Distance(OSM1003, 60, 'MI', GeoCardinal(SW)), Adjacent(OSM1004))\n"



        prompt += "Parse the sentence below. Response with only the operators:\n"
        prompt += filtered[i][1]



        # # DEBUG: Dump prompt to file
        # print(f"Writing prompt to file ({args.output_folder}/{fileout_prefix}_prompt_out.txt)")
        # with open(os.path.join(args.output_folder, f'{fileout_prefix}_prompt_out.txt'), 'w') as f:
        #     f.write(prompt)
        print(prompt)
        # try:
        response = getResponse(prompt, model=args.model, maxTokensOut=8000)
        #response = getResponse(prompt, maxTokensOut=1000)
        print(response)

        numTokens = getTokenLength(response)
        print("")
        print("Responded with " + str(numTokens) + " tokens.")
        print("")
        time.sleep(5)

        programOut = response       # Streaming version
        print(response)
        responses[filtered[i][0]] = (filtered[i][1], response)
        i += 1
            # print (f"Saving response to: {args.output_folder}/{fileout_prefix}_generation.py")
            # with open(os.path.join(args.output_folder,f"{fileout_prefix}_generation.py"), 'w') as f:
            #     f.write(programOut)
        # except Exception as e:
        #     print("RATE LIMIT")
        #     print(e)
        #     time.sleep(10)
        #     continue

    with open(os.path.join(args.output_folder, "11_21_01.json"), "w") as f:
        json.dump(responses, f)

    with open(os.path.join(args.output_folder, "11_21_01_for_eval.txt"), "w") as f:
        for key, value in responses.items():
            response = clean_response(value[1])
            f.write(key)
            f.write(f'\t{response}')
            f.write('\n')

if __name__ == "__main__":
    main()
