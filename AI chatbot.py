import json
import ifc_exporter  # Import the module
import ollama
from ollama import chat
from typing import Dict, Callable
import streamlit as st

# Define the path to your IFC file
# Streamlit UI setup
st.set_page_config(page_title="IFC Model Chatbot", layout="wide")
st.title("🏗️ IFC Model Chatbot 🤖 (Powered by Llama 3.1)")

# File uploader for IFC file
ifc_path = st.file_uploader("📂 Upload your IFC file", type=["ifc"])

# Initialize data variables (these will be filled after the file is uploaded)
doors_df, windows_df, beams_df, columns_df, spaces_df, floors_df = None, None, None, None, None, None

# Process the uploaded IFC file
if ifc_path is not None:
    # Temporarily save the uploaded file to read it for extraction
    with open("uploaded.ifc", "wb") as f:
        f.write(ifc_path.getbuffer())
    
    # Call the extraction function from ifc_exporter
    doors_df, windows_df, beams_df, columns_df, spaces_df, floors_df = ifc_exporter.extract_ifc_data("uploaded.ifc")

    st.write("File uploaded and data extracted successfully!")
else:
    st.warning("Please upload an IFC file to begin.")

# Define all the functions with the data already extracted
def list_elements_type(element_type: str) -> str:
    element_type = element_type.lower()  # Normalize input to lowercase
    elements_dict = {
        "doors": doors_df["Name"].unique().tolist(),
        "columns": columns_df["Name"].unique().tolist(),
        "beams": beams_df["Name"].unique().tolist(),
        "windows": windows_df["Name"].unique().tolist(),
    }

    if element_type in elements_dict:
        return json.dumps({element_type: elements_dict[element_type]}, indent=4)
    else:
        return json.dumps({"error": "I have limited functions and can only retrieve information for types of doors, columns, beams and windows in your model."})

def list_all_elements_with_ids(element_type: str) -> str:
    """get all elements of a given type, listing Name first, then ID."""
    element_type = element_type.lower()  # Normalize input to lowercase
    
    elements_dict = {
        "doors": doors_df[["Name", "ID"]].to_dict(orient="records"),
        "columns": columns_df[["Name", "ID"]].to_dict(orient="records"),
        "beams": beams_df[["Name", "ID"]].to_dict(orient="records"),
        "windows": windows_df[["Name", "ID"]].to_dict(orient="records"),
    }

    if element_type in elements_dict:
        return json.dumps({element_type: elements_dict[element_type]}, indent=4)
    else:
        return json.dumps({"error": "I can currently only retrieve information for lists of doors, columns, beams and windows in your model."})

def list_spaces() -> str:
    if not spaces_df.empty and 'Name' in spaces_df.columns:
        space_names = spaces_df['Name'].dropna().unique().tolist()
        return json.dumps({'spaces': space_names})
    return json.dumps({'error': 'No rooms or spaces found in the model.'})

def get_space_area(space_name: str) -> str:
    if space_name in spaces_df.Name.values:
        return json.dumps({'area': f"{spaces_df[spaces_df.Name == space_name].Area.item()} m²"})
    return json.dumps({'error': 'Space or room not found. Please give the correct name of the room'})

def get_space_height(space_name: str) -> str:
    if space_name in spaces_df.Name.values:
        return json.dumps({'height': f"{spaces_df[spaces_df.Name == space_name].Height.item()} mm"})
    return json.dumps({'error': 'Space or room not found. Please give the correct name of the room'})

def get_space_location(space_name: str) -> str:
    if space_name in spaces_df.Name.values:
        return json.dumps({'location': spaces_df[spaces_df.Name == space_name].Location.item()})
    return json.dumps({'error': 'Space or room not found. Please give the correct name of the room'})

def get_window_width(window_name: str) -> str:
    # Filter windows based on window_name only and get the first occurrence
    window_data = windows_df[windows_df.Name == window_name]
    
    if not window_data.empty:
        return json.dumps({'width': f"{window_data.iloc[0].Width} mm"})  # Get the first match
    return json.dumps({'error': 'Window not found. Please give the correct name of the window'})

def get_window_height(window_name: str) -> str:
    # Filter windows based on window_name only and get the first occurrence
    window_data = windows_df[windows_df.Name == window_name]
    
    if not window_data.empty:
        return json.dumps({'height': f"{window_data.iloc[0].Height} mm"})  # Get the first match
    return json.dumps({'error': 'Window not found. Please give the correct name of the window'})

def get_window_location(window_name: str, window_id: str = None) -> str:
    if window_name in windows_df.Name.values:
        if window_id:
            # If ID is provided, get the location
            location = windows_df[(windows_df.Name == window_name) & (windows_df.ID == window_id)]
            if not location.empty:
                return json.dumps({'location': location.Location.item()})
            return json.dumps({'error': 'Window ID not found.'})
        else:
            # If only name is provided, prompt for ID
            return json.dumps({'error': f"Multiple windows with the name '{window_name}' found. Please provide the name including the ID of the window."})
    return json.dumps({'error': 'Window not found.'})

def get_door_width(door_name: str) -> str:
    # Filter doors based on door_name only and get the first occurrence
    door_data = doors_df[doors_df.Name == door_name]
    
    if not door_data.empty:
        return json.dumps({'width': f"{door_data.iloc[0].Width} mm"})  # Get the first match
    return json.dumps({'error': 'Door not found. Please give the correct name of the door'})

def get_door_height(door_name: str) -> str: 
    # Filter doors based on door_name only and get the first occurrence
    door_data = doors_df[doors_df.Name == door_name]
    
    if not door_data.empty:
        return json.dumps({'height': f"{door_data.iloc[0].Height} mm"})  # Get the first match
    return json.dumps({'error': 'Door not found. Please give the correct name of the door'})

def get_door_location(door_name: str, door_id: str = None) -> str:
    if door_name in doors_df.Name.values:
        if door_id:
            location = doors_df[(doors_df.Name == door_name) & (doors_df.ID == door_id)]
            if not location.empty:
                return json.dumps({'location': location.Location.item()})
            return json.dumps({'error': 'Door ID not found.'})
        else:
            return json.dumps({'error': f"Multiple doors with the name '{door_name}' found. Please provide the name and the ID of the door."})
    return json.dumps({'error': 'Door not found.'})

def get_beam_length(beam_name: str, beam_id: str = None) -> str:
    if beam_name in beams_df.Name.values:
        if beam_id:
            length = beams_df[(beams_df.Name == beam_name) & (beams_df.ID == beam_id)]
            if not length.empty:
                return json.dumps({'length': f"{length.Length.item()} mm"})
            return json.dumps({'error': 'Beam ID not found.'})
        else:
            return json.dumps({'error': f"Multiple beams with the name '{beam_name}' found. Please provide the name and the ID of the beam."})
    return json.dumps({'error': 'Beam not found. please give the correct name of the beam'})

def get_beam_volume(beam_name: str, beam_id: str = None) -> str:
    if beam_name in beams_df.Name.values:
        if beam_id:
            volume = beams_df[(beams_df.Name == beam_name) & (beams_df.ID == beam_id)]
            if not volume.empty:
                return json.dumps({'volume': f"{volume.Volume.item()} mm³"})
            return json.dumps({'error': 'Beam ID not found.'})
        else:
            return json.dumps({'error': f"Multiple beams with the name '{beam_name}' found. Please provide the ID of the beam."})
    return json.dumps({'error': 'Beam not found. please give the correct name of the beam'})

def get_beam_cross_section_area(beam_name: str) -> str:
    # Filter beams based on beam_name only and get the first occurrence
    beam_data = beams_df[beams_df.Name == beam_name]
    
    if not beam_data.empty:
        return json.dumps({'cross_section_area': f"{beam_data.iloc[0].Cross_Section_Area} mm²"})  # Get the first match
    return json.dumps({'error': 'Beam not found. please give the correct name of the beam'})

def get_beam_location(beam_name: str, beam_id: str = None) -> str:
    if beam_name in beams_df.Name.values:
        if beam_id:
            location = beams_df[(beams_df.Name == beam_name) & (beams_df.ID == beam_id)]
            if not location.empty:
                return json.dumps({'location': location.Location.item()})
            return json.dumps({'error': 'Beam ID not found.'})
        else:
            return json.dumps({'error': f"Multiple beams with the name '{beam_name}' found. Please provide the name including the ID of the beam."})
    return json.dumps({'error': 'Beam not found.'})

def get_column_length(column_name: str, column_id: str = None) -> str:
    if column_name in columns_df.Name.values:
        if column_id:
            length = columns_df[(columns_df.Name == column_name) & (columns_df.ID == column_id)]
            if not length.empty:
                return json.dumps({'length': f"{length.Length.item()} mm"})
            return json.dumps({'error': 'Column ID not found.'})
        else:
            return json.dumps({'error': f"Multiple columns with the name '{column_name}' found. Please provide the name and the ID of the column."})
    return json.dumps({'error': 'Column not found.'})

def get_column_cross_section_area(column_name: str) -> str:
    # Filter columns based on column_name only and get the first occurrence
    column_data = columns_df[columns_df.Name == column_name]
    
    if not column_data.empty:
        return json.dumps({'cross_section_area': f"{column_data.iloc[0].Cross_Section_Area} mm²"})  # Get the first match
    return json.dumps({'error': 'Column not found.please give the correct name of the column'})

def get_column_volume(column_name: str, column_id: str = None) -> str:
    if column_name in columns_df.Name.values:
        if column_id:
            volume = columns_df[(columns_df.Name == column_name) & (columns_df.ID == column_id)]
            if not volume.empty:
                return json.dumps({'volume': f"{volume.Volume.item()} mm³"})
            return json.dumps({'error': 'Column ID not found.'})
        else:
            return json.dumps({'error': f"Multiple columns with the name '{column_name}' found. Please provide the name and the ID of the column."})
    return json.dumps({'error': 'Column not found.'})

def get_column_location(column_name: str, column_id: str = None) -> str:
    if column_name in columns_df.Name.values:
        if column_id:
            location = columns_df[(columns_df.Name == column_name) & (columns_df.ID == column_id)]
            if not location.empty:
                return json.dumps({'location': location.Location.item()})
            return json.dumps({'error': 'Column ID not found.'})
        else:
            return json.dumps({'error': f"Multiple columns with the name '{column_name}' found. Please provide the name and the ID of the column."})
    return json.dumps({'error': 'Column not found.'})

def get_floor_elevation(floor_name: str) -> str:
    if floor_name in floors_df.Name.values:
        return json.dumps({'elevation': f"{floors_df[floors_df.Name == floor_name].Elevation.item()} mm"})
    return json.dumps({'error': 'Floor not found. please give the correct name of the floor'})

def list_floors() -> str:
    if not floors_df.empty:
        floor_names = floors_df['Name'].dropna().unique().tolist()
        return json.dumps({'floors': floor_names})
    return json.dumps({'error': 'No rooms or spaces found in the model.'})


# Mapping the functions with functools.partial to automatically include relevant data (like `spaces_df`, `windows_df`, etc.)
available_tools: Dict[str, Callable] = {
    'list_elements_type': list_elements_type,
    'list_all_elements_with_ids': list_all_elements_with_ids,
    'list_spaces': list_spaces,
    'get_space_area': get_space_area,
    'get_space_height': get_space_height,
    'get_space_location': get_space_location,
    'get_window_width': get_window_width,
    'get_window_height': get_window_height,
    'get_window_location': get_window_location,
    'get_door_width': get_door_width,
    'get_door_height': get_door_height,
    'get_door_location': get_door_location,
    'get_beam_length': get_beam_length,
    'get_beam_volume': get_beam_volume,
    'get_beam_cross_section_area': get_beam_cross_section_area,
    'get_beam_location': get_beam_location,
    'get_column_length': get_column_length,
    'get_column_cross_section_area': get_column_cross_section_area,
    'get_column_volume': get_column_volume,
    'get_column_location': get_column_location,
    'get_floor_elevation': get_floor_elevation,
    'list_floors': list_floors,
}

# Simulate a user query that would trigger a function call
user_query = st.text_input("Ask a question about the building model:")
messages = [{'role': 'user', 'content': user_query}]
response = ollama.chat(
    model='llama3.1',
    messages=messages,
    tools=[
        {
            "type": "function",
            "function": {
                "name": "list_elements_type",
                "description": "get the type of doors, columns, beams, or windows used in the project",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "element_type": {
                            "type": "string",
                            "description": "The type of element to get. Must be one of: 'doors', 'columns', 'beams', 'windows'."
                        }
                    },
                    "required": ["element_type"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_all_elements_with_ids",
                "description": "get a list of all doors, columns, beams or windows, including their IDs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "element_type": {
                            "type": "string",
                            "description": "The type of element to get. Must be one of: 'doors', 'columns', 'beams', 'windows'."
                        }
                    },
                    "required": ["element_type"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_spaces",
                "description": "get a list of all rooms or spaces available in the model.",
                "parameters": {
                "type": "object",
                "properties": {},
                "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_space_area",
                "description": "get the area of a space or room.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "space_name": {
                            "type": "string",
                            "description": "The name of the space or room (e.g., '1')."
                        }
                    },
                    "required": ["space_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_space_height",
                "description": "get the height of a room or space.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "space_name": {
                            "type": "string",
                            "description": "The name of the room (e.g., 'Room 101')."
                        }
                    },
                    "required": ["space_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_space_location",
                "description": "get the location of a room or space.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "space_name": {
                            "type": "string",
                            "description": "The name of the room or space (e.g., 'Room 101')."
                        }
                    },
                    "required": ["space_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_window_width",
                "description": "get the width of a window.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "window_name": {
                            "type": "string",
                            "description": "The name of the window."
                        }
                    },
                    "required": ["window_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_window_height",
                "description": "get the height of a window.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "window_name": {
                            "type": "string",
                            "description": "The name of the window"
                        }
                    },
                    "required": ["window_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_window_location",
                "description": "get the location of a window based on its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "window_name": {
                            "type": "string",
                            "description": "The name of the window"
                        },
                        "window_id": {
                            "type": "string",
                            "description": "The ID of the window"
                        }
                    },
                    "required": ["window_name", "window_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_door_width",
                "description": "get the width of a door.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "door_name": {
                            "type": "string",
                            "description": "The name of the door (e.g., 'Door A')."
                        }
                    },
                    "required": ["door_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_door_height",
                "description": "get the height of a door.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "door_name": {
                            "type": "string",
                            "description": "The name of the door (e.g., 'Door A')."
                        }
                    },
                    "required": ["door_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_door_location",
                "description": "get the location of a specific door based on its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "door_name": {
                            "type": "string",
                            "description": "The name of the door (e.g., 'Door B')."
                        },
                        "door_id": {
                            "type": "string",
                            "description": "The ID of the door (e.g., 'Door_B2')."
                        }
                    },
                    "required": ["door_name", "door_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_beam_length",
                "description": "get the length of a specific beam based on its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "beam_name": {
                            "type": "string",
                            "description": "The name of the beam (e.g., 'Beam 1')."
                        },
                        "beam_id": {
                            "type": "string",
                            "description": "The ID of the beam (e.g., 'Beam_1')."
                        }
                    },
                    "required": ["beam_name", "beam_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_beam_volume",
                "description": "get the volume of a specific beam based on its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "beam_name": {
                            "type": "string",
                            "description": "The name of the beam (e.g., 'Beam A')."
                        },
                        "beam_id": {
                            "type": "string",
                            "description": "The ID of the beam (e.g., 'Beam_1')."
                        }
                    },
                    "required": ["beam_name", "beam_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_beam_cross_section_area",
                "description": "get the cross-section area of a beam",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "beam_name": {
                            "type": "string",
                            "description": "The name of the beam (e.g., 'Beam A')."
                        }
                    },
                    "required": ["beam_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_beam_location",
                "description": "get the location of a specific beam based on its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "beam_name": {
                            "type": "string",
                            "description": "The name of the beam (e.g., 'Beam 1')."
                        },
                        "beam_id": {
                            "type": "string",
                            "description": "The ID of the beam (e.g., 'Beam_1')."
                        }
                    },
                    "required": ["beam_name", "beam_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_column_length",
                "description": "get the length of a specific column based on its name or ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "column_name": {
                            "type": "string",
                            "description": "The name of the column (e.g., 'Column B')."
                        },
                        "column_id": {
                            "type": "string",
                            "description": "The ID of the column (e.g., 'Column_3')."
                        }
                    },
                    "required": ["column_name", "column_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_column_cross_section_area",
                "description": "get the cross section area of a column.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "column_name": {
                            "type": "string",
                            "description": "The name of the column (e.g., 'Column B')."
                        }
                    },
                    "required": ["column_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_column_volume",
                "description": "get the volume of a specific column based on its name or ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "column_name": {
                            "type": "string",
                            "description": "The name of the column (e.g., 'Column B')."
                        },
                        "column_id": {
                            "type": "string",
                            "description": "The ID of the column (e.g., 'Column_3')."
                        }
                    },
                    "required": ["column_name", "column_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_column_location",
                "description": "get the location of a specific column based on its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "column_name": {
                            "type": "string",
                            "description": "The name of the column (e.g., 'Column 3')."
                        },
                        "column_id": {
                            "type": "string",
                            "description": "The ID of the column (e.g., 'Column_3')."
                        }
                    },
                    "required": ["column_name", "column_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_floor_elevation",
                "description": "get the elevation of a specific floor based on its name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "floor_name": {
                            "type": "string",
                            "description": "The name of the floor (e.g., 'Floor 1')."
                        }
                    },
                    "required": ["floor_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_floors",
                "description": "Retrieve a list of all rooms or spaces present in the model.",
                "parameters": {
                "type": "object",
                "properties": {},
                "required": []
                }
            }
        },
    ],
)

if response.message.tool_calls:
    for tool in response.message.tool_calls:
        if function_to_call := available_tools.get(tool.function.name):
            print('Calling functions:', tool.function.name)
            print('Arguments:', tool.function.arguments)
            output = function_to_call(**tool.function.arguments)
            print('Function output', output)
        else:
            print('Function', tool.function.name, 'not found')


# Only needed to chat with the model using the tool call results
if response.message.tool_calls:
  messages.append(response.message)
  messages.append({'role': 'system', 'content': 'If you receieve results from the tool, relay these results completely and write it all down. Do not assume units or other information not mentioned by the function output. If you recieve an error, write the exact error receieved and do not omit anything'})
  messages.append({'role': 'tool', 'content': str(output), 'name': tool.function.name})

  # Get final response from model with function outputs
  final_response = chat('llama3.1', messages=messages)
  st.write("### 🤖 AI Response:")
  st.write(final_response.message.content)

else:
    # Add a fallback message to handle questions not related to functions
    messages.append({'role': 'system', 'content':'You are an assistant with limited function and can ONLY retrieve information about floor elevations and some types, dimensions and locations of beams, columns, windows, doors, and rooms. If there is no query, say hi and introduce yourself but do not make up any names, and always list down your limited function.  If you are being asked a question unrelated to any predefined function. Answer the question VERY breifly, but redirect the user and offer your assistance in retrieving information from their 3d building model file.'})
    messages.append({'role': 'user', 'content': response.message.content})

    # Get the model's response to the random question
    final_response = chat('llama3.1', messages=messages)
    st.write("### 🤖 AI Response:")
    st.write(final_response.message.content)