
# IntelliQ

## Introduction
IntelliQ is an open-source project aimed at providing a multi-turn question-and-answer system based on large language models (LLM). This system combines advanced intent recognition and slot filling technologies to enhance the depth of understanding and accuracy of responses in dialogue systems. This project offers a flexible and efficient solution for the developer community to build and optimize various conversational applications.

**Project source link:** https://github.com/answerlink/IntelliQ

## Features
1. **Multi-turn Dialogue Management:** Handles complex dialogue scenarios, supporting continuous multi-turn interactions.
2. **Intent Recognition:** Accurately determines the intent of user input, with support for custom intent extensions.
3. **Slot Filling:** Dynamically identifies and fills critical information (e.g., time, location, objects, etc.).
4. **Interface Slot Technology:** Directly integrates with external APIs for real-time data retrieval and processing.
5. **Adaptive Learning:** Continuously learns from user interactions, optimizing response accuracy and speed.
6. **Ease of Integration:** Offers detailed API documentation and supports integration with multiple programming languages and platforms.

## Customization for Chatbot in Procurement Scenarios

### Key Custom Modules
- **scene_config\scene_prompts.py**
  
  Defines the basic AI settings for slot filling, role definitions, and behavior constraints.

- **scene_config\scene_templates.py**
  
  Specifies the detailed dialogue scenarios. AI automatically identifies the corresponding scenarios through descriptions to trigger slot filling tasks and guide users to complete all slots under the corresponding scenario.

### Adjustments for LLM Output Processing and Data Extraction/Integration
- **utils\helpers.py**

```python
# JSON processing improvements based on procurement scenarios
def extract_json_from_string(input_string):
    # Use non-greedy matching to improve extraction and avoid truncating nested structures
    matches = re.findall(r'\{.*?\}', input_string, re.DOTALL)
    valid_jsons = []
    for match in matches:
        try:
            json_obj = json.loads(match)
            valid_jsons.append(json_obj)
        except json.JSONDecodeError:
            continue  # Skip if invalid JSON
    return valid_jsons
```

- **Format Conversion for Procurement Lists:**
  
  Generates a well-formed output format for API calls:

```python
def prepare_json_data_for_api(json_data):
    # Modify the value format of specific entries in json_data
    for item in json_data:
        if item.get("name") == "Procurement Content List":
            current_value = item.get("value", "")
            # Process the string and structure it as a formatted list
            item["value"] = [{"item": "example_item", "quantity": "1 unit"}]
    return json_data
```

## Configuration Modifications
Configuration items are located in `config/__init__.py`:
- **GPT_URL:** Can be modified to the proxy address for OpenAI.
- **API_KEY:** Replace with your ChatGPT API key.

## Startup
```bash
python app.py
```
Start the application using the command above.

#### For visual debugging, open `demo/user_input.html` in your browser or visit `127.0.0.1:5000`.
