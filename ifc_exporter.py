import ifcopenshell
import pandas as pd

# Function to separate Name and ID from the element name
def separate_name_and_id(element_name):
    parts = element_name.split(":")
    if len(parts) > 1:
        # The first part is the Name, the last part is the ID
        name = ":".join(parts[:-1])  # Join all parts except the last one as Name
        element_id = parts[-1]       # The last part is considered the ID
    else:
        # If no ID is found, the whole string is considered the Name
        name = parts[0]
        element_id = "N/A"  # ID not available
    
    return name, element_id

def extract_ifc_data(ifc_path):
    try:
        model = ifcopenshell.open(ifc_path)
        if model is None:
            return None, None, None, None, None, None, None  # Ensure return values match

        # Retrieve the unit system used in the project
        units = model.by_type("IfcUnitAssignment")
        unit_factors = {
            "length": 1,  # Default for length unit (meter, millimeter, etc.)
            "area": 1,    # Default for area (m², cm², etc.)
            "volume": 1   # Default for volume (m³, cm³, etc.)
        }

        if units:
            unit_assignment = units[0]  # Usually only one unit assignment in most IFC files
            for unit in unit_assignment.Units:
                if unit.is_a("IfcSIUnit"):
                    if unit.UnitType == "LENGTHUNIT":
                        if unit.Name == "MILLIMETER":
                            unit_factors["length"] = 1000  # Millimeter scale
                        elif unit.Name == "CENTIMETER":
                            unit_factors["length"] = 100  # Centimeter scale
                        elif unit.Name == "METER":
                            unit_factors["length"] = 1  # Meter scale
                    elif unit.UnitType == "AREAUNIT":
                        if unit.Name == "SQUARE_METER":
                            unit_factors["area"] = 1  # Square meter scale
                        elif unit.Name == "SQUARE_CENTIMETER":
                            unit_factors["area"] = 10000  # Square centimeter scale
                    elif unit.UnitType == "VOLUMEUNIT":
                        if unit.Name == "CUBIC_METER":
                            unit_factors["volume"] = 1  # Cubic meter scale
                        elif unit.Name == "CUBIC_CENTIMETER":
                            unit_factors["volume"] = 1000000  # Cubic centimeter scale

        # Function to get level information
        def get_level(element):
            for rel in model.by_type("IfcRelContainedInSpatialStructure"):
                if element in rel.RelatedElements and rel.RelatingStructure.is_a("IfcBuildingStorey"):
                    return rel.RelatingStructure.Name
            return "Unknown"
        
        # Function to get correct floor level for spaces
        def get_space_level(space):
            for rel in model.by_type("IfcRelAggregates"):  # Check aggregation relationships
                if space in rel.RelatedObjects and rel.RelatingObject.is_a("IfcBuildingStorey"):
                    return rel.RelatingObject.Name  # Return floor name
            return "Unknown"
        
        doors = model.by_type("IfcDoor") 
        windows = model.by_type("IfcWindow") 
        beams = model.by_type("IfcBeam") 
        columns = model.by_type("IfcColumn") 
        spaces = model.by_type("IfcSpace")  
        floors = model.by_type("IfcBuildingStorey")  

        door_data, window_data, beam_data, column_data, space_data, floor_data = [], [], [], [], [], []

        # Function to extract dimensions directly from IfcWindow, IfcDoor, IfcBeam, IfcColumn
        def extract_dimensions_directly(element, data_dict):
            if hasattr(element, "OverallHeight") and element.OverallHeight is not None:
                # Convert height to correct units based on the factor
                data_dict["Height"] = f"{element.OverallHeight * unit_factors['length']} mm"  # Ensure it's in millimeters
            else:
                data_dict["Height"] = "Unknown"

            if hasattr(element, "OverallWidth") and element.OverallWidth is not None:
                # Convert width to correct units based on the factor
                data_dict["Width"] = f"{element.OverallWidth * unit_factors['length']} mm"  # Ensure it's in millimeters
            else:
                data_dict["Width"] = "Unknown"

            return data_dict

        # Extract Window Data
        for window in windows:
            window_info = {
                "Name": window.Name if window.Name else "Unnamed Window",
                "Location": get_level(window),
                "Width": "Unknown",
                "Height": "Unknown"
            }
            # Separate Name and ID from the window's name
            window_info["Name"], window_info["ID"] = separate_name_and_id(window_info["Name"])
            window_info = extract_dimensions_directly(window, window_info)
            window_data.append(window_info)
        

        # Extract Door Data
        for door in doors:
            door_info = {
                "Name": door.Name if door.Name else "Unnamed Door",
                "Location": get_level(door),
                "Width": "Unknown",
                "Height": "Unknown"
            }        
            # Separate Name and ID from the door's name
            door_info["Name"], door_info["ID"] = separate_name_and_id(door_info["Name"])
            door_info = extract_dimensions_directly(door, door_info)
            door_data.append(door_info)

        # Extract Beam Data
        for beam in beams:
            beam_info = {
                "Name": beam.Name if beam.Name else "Unnamed Beam", 
                "Location": get_level(beam),
                "Length": "Unknown",
                "Cross Section Area": "Unknown",
                "Volume": "Unknown"
            }

            # Separate the Name and ID from the beam's name
            beam_info["Name"], beam_info["ID"] = separate_name_and_id(beam_info["Name"])

            for rel in model.by_type("IfcRelDefinesByProperties"):
                if beam in rel.RelatedObjects:
                    prop_set = rel.RelatingPropertyDefinition
                    if prop_set.is_a("IfcElementQuantity"):
                        for quantity in prop_set.Quantities:
                            if quantity.is_a("IfcQuantityLength"):
                                beam_info["Length"] = f"{quantity.LengthValue * unit_factors['length']} mm"
                            elif quantity.is_a("IfcQuantityArea"):
                                 if "CrossSectionArea" in quantity.Name:  # or you may use a more specific name check if required
                                    beam_info["Cross Section Area"] = f"{quantity.AreaValue * unit_factors['area']} m²"
                            elif quantity.is_a("IfcQuantityVolume"):
                                beam_info["Volume"] = f"{quantity.VolumeValue * unit_factors['volume']} m³"
            beam_data.append(beam_info)

        for column in columns:
            column_info = {
                "Name": column.Name if column.Name else "Unnamed Column",
                "Location": get_level(column),
                "Length": "Unknown",
                "Cross Section Area": "Unknown",
                "Volume": "Unknown"
            }
            # Separate Name and ID from the column's name
            column_info["Name"], column_info["ID"] = separate_name_and_id(column_info["Name"])

            if hasattr(column, "OverallHeight") and column.OverallHeight is not None:
                column_info["Height"] = f"{column.OverallHeight * unit_factors['length']} mm"
            if hasattr(column, "OverallWidth") and column.OverallWidth is not None:
                column_info["Width"] = f"{column.OverallWidth * unit_factors['length']} mm"
            for rel in model.by_type("IfcRelDefinesByProperties"):
                if column in rel.RelatedObjects:
                    prop_set = rel.RelatingPropertyDefinition
                    if prop_set.is_a("IfcElementQuantity"):
                        for quantity in prop_set.Quantities:
                            if quantity.is_a("IfcQuantityLength"):
                                column_info["Length"] = f"{quantity.LengthValue * unit_factors['length']} mm"
                            elif quantity.is_a("IfcQuantityArea"):
                                if "CrossSectionArea" in quantity.Name:  # or you may use a more specific name check if required
                                    column_info["Cross Section Area"] = f"{quantity.AreaValue * unit_factors['area']} m²"
                            elif quantity.is_a("IfcQuantityVolume"):
                                column_info["Volume"] = f"{quantity.VolumeValue * unit_factors['volume']} mm³"
            column_data.append(column_info)


        # Extract space data
        for space in spaces:
            space_info = {
                "Type": space.LongName if space.LongName else "Unnamed Space",
                "Name": space.Name if space.Name else "Unnamed Space",
                "Location": get_space_level(space),
                "Area" : "Unknown",
                "Height": "Unknown"
            }

            # Check the space's quantities (area and height only)
            for rel in model.by_type("IfcRelDefinesByProperties"):
                if space in rel.RelatedObjects:
                    prop_set = rel.RelatingPropertyDefinition
                    
                    if prop_set.is_a("IfcElementQuantity"):
                        for quantity in prop_set.Quantities:
                            if quantity.is_a("IfcQuantityArea"):
                                # Convert area to m²
                                space_info["Area"] = f"{quantity.AreaValue * unit_factors['area']} m²"  # Conversion to m²
                            elif quantity.is_a("IfcQuantityLength"):
                                # Convert height to mm
                                space_info["Height"] = f"{quantity.LengthValue * unit_factors['length']} mm"  # Conversion to mm

            # Add the space data only if Area and Height are found
            if "Area" in space_info and "Height" in space_info:
                space_data.append(space_info)

        # Extract floor data with elevation and unit
        for floor in floors:
            floor_info = {
                "Name": floor.Name if floor.Name else "Unnamed Floor",
                "Elevation": "Unknown"
        }

        # If Elevation exists, convert and add unit
            if hasattr(floor, "Elevation") and floor.Elevation is not None:
                # Check the unit factor for length (if your length unit is meters)
                floor_info["Elevation"] = f"{floor.Elevation * unit_factors['length']} mm"  # Convert to millimeters

            floor_data.append(floor_info)
        
        # Convert to DataFrames
        door_df = pd.DataFrame(door_data)
        window_df = pd.DataFrame(window_data)
        beam_df = pd.DataFrame(beam_data)
        column_df = pd.DataFrame(column_data)
        space_df = pd.DataFrame(space_data)
        floor_df = pd.DataFrame(floor_data)

        return door_df, window_df, beam_df, column_df, space_df, floor_df
    except Exception as e:
        return f"Error processing IFC file: {str(e)}", None, None, None, None, None
