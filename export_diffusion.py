bl_info = {
    "name": "Export Camera Animation to Deforum collab/webui",
    "author": "Michael Walker (@mwalk10) / Kewk (@KewkD)",
    "version": (1, 2, 0),
    "blender": (3, 5, 1),
    "location": "File > Export > Diffusion Notebook String",
    "description": "Export camera animations formatted for use in Deforum: collab and Webui's",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}


import bpy
from bpy_extras.io_utils import ImportHelper
from math import degrees
from math import isclose
import json
import re

# Define a function to round small numbers to zero, with a customisable threshold
def roundZero(num, magnitude_thresh = 0.00001):
    # If the absolute value of the number is greater than the threshold
    if abs(num) > magnitude_thresh:
        # Return the original number
        return num
    else:
        # Otherwise, return 0
        return 0

# Define a function to convert an array into a string of keyframes
def arr_to_keyframes(arr):
    # Initialize an empty string to store the keyframes
    keyframes = ""
    # Enumerate over the array (i will be the index, val will be the value at that index)
    for i, val in enumerate(arr):
        # Round the current value to zero if it's smaller than the threshold
        val = roundZero(val)
        # Check if the current value is close to the previous one
        last_is_same = i > 0 and isclose(val, roundZero(arr[i-1]))
        # Check if the current value is close to the next one
        next_is_same = (i+1) < len(arr) and isclose(val, roundZero(arr[i+1]))        
        # Determine if the current value should be omitted (it's the same as both the previous and next values)
        omit = last_is_same and next_is_same        
        # If the current value shouldn't be omitted
        if not omit:
            # Add it to the keyframes string, formatted as "index:(value),"
            keyframes += f"{i}:({val}),"
    # Return the keyframes string
    return keyframes

        
# This function transforms camera data to a string representation.
def cameras_to_string(context, startFrame, endFrame, cameras, translation_scale = 50, output_camcode = True, output_json = False, output_raw_frames = False):
    # Get the current scene
    scene = context.scene
    # Save the current frame
    currentFrame = scene.frame_current

    # If no cameras are selected, print a message and return
    if len(cameras) == 0:
        print("Nothing selected!")
        return "No Cameras selected for export"
    
    # Initialize an empty string for the export
    export_string = ""
    
    # Loop over all selected cameras
    for sel in cameras:
        # Set the scene frame to the start frame
        scene.frame_set(startFrame)

        # Initialize lists to store translation and rotation values
        translation_x = []
        translation_y = []
        translation_z = []
        rotation_3d_x = []
        rotation_3d_y = []
        rotation_3d_z = []

        # Save the current camera's world matrix and rotation
        oldMat = sel.matrix_world.copy()
        oldRot = oldMat.to_quaternion()

        # Loop over all frames from start to end
        for frame in range(startFrame+1, endFrame):
            # Set the scene frame to the current frame
            scene.frame_set(frame)

            # Save the current camera's world matrix and rotation
            newMat = sel.matrix_world.copy() 
            newRot = newMat.to_quaternion()

            # Get the inverse of the new world matrix and its rotation
            worldToLocal = newMat.inverted()
            wlRot = worldToLocal.to_quaternion()

            # Calculate the difference in position between the old and new frames
            posDiff = newMat.to_translation() - oldMat.to_translation()
            posDiffLocal = wlRot @ posDiff

            # Store the scaled translation values
            translation_x.append(translation_scale*posDiffLocal.x)
            translation_y.append(translation_scale*posDiffLocal.y)
            translation_z.append(-translation_scale*posDiffLocal.z)

            # Calculate the difference in rotation between the old and new frames
            rotDiff = oldRot.rotation_difference(newRot).to_euler("XYZ")

            # Store the rotation values in degrees
            rotation_3d_x.append(degrees(rotDiff.x))
            rotation_3d_y.append(degrees(-rotDiff.y))
            rotation_3d_z.append(degrees(-rotDiff.z))

            # Update the old matrix and rotation for the next frame
            oldMat = newMat
            oldRot = newRot

        # Check if raw frames should be output
        if not output_raw_frames:
            # Add camera export data to the export string
            export_string += f"\nCamera Export: {sel.name}\n"      
            for var, label in zip([translation_x, translation_y, translation_z, rotation_3d_x, rotation_3d_y, rotation_3d_z],
                                  ['translation_x', 'translation_y', 'translation_z', 'rotation_3d_x', 'rotation_3d_y', 'rotation_3d_z']):
                export_string += f'{label} = "{arr_to_keyframes(var)}" #@param {{type:"string"}}\n'

        # Check if camera code should be output
        if output_camcode:
            # Add camera code to the export string
            export_string += f'cam_code:\n(translation_x,translation_y,translation_z,rotation_3d_x,rotation_3d_y,rotation_3d_z) = ("{arr_to_keyframes(translation_x)}", "{arr_to_keyframes(translation_y)}", "{arr_to_keyframes(translation_z)}", "{arr_to_keyframes(rotation_3d_x)}", "{arr_to_keyframes(rotation_3d_y)}", "{arr_to_keyframes(rotation_3d_z)}")\n'
        
        # Check if JSON data should be output
        if output_json:
            # Create a dictionary with all the camera data
            jsondict = {
                "translation_x" : translation_x,
                "translation_y" : translation_y,
                "translation_z" : translation_z,
                "rotation_3d_x" : rotation_3d_x,
                "rotation_3d_y" : rotation_3d_y,
                "rotation_3d_z" : rotation_3d_z}
            
            # Add the JSON representation of the dictionary to the export string
            export_string += f"JSON:\n {json.dumps(jsondict)}\n"

        # Check if raw frame data should be output
        if output_raw_frames:
            # Create a dictionary with all the raw frame data
            raw_frames = {
                "translation_x": translation_x,
                "translation_y": translation_y,
                "translation_z": translation_z,
                "rotation_3d_x": rotation_3d_x,
                "rotation_3d_y": rotation_3d_y,
                "rotation_3d_z": rotation_3d_z
            }

            # Loop over all items in the dictionary
            for key, arr in raw_frames.items():
                # Initialize the string for raw frames
                raw_frame_str = ""  
                last_val = None
                for i, val in enumerate(arr):
                    # Check if the value has changed from the last frame
                    if last_val is None or not isclose(val, last_val):
                        # Add the frame index and value to the raw frame string
                        raw_frame_str += f"{i}:({val}),"
                    last_val = val
                # Remove the trailing comma from the raw frame string
                raw_frame_str = raw_frame_str.rstrip(",")
                # Add the raw frames for the current item to the export string
                export_string += f"\nRaw frames for {key}:\n{raw_frame_str}\n"

        # Add a newline to the export string
        export_string += "\n"

    # Restore the original frame
    scene.frame_set(currentFrame)

    # Return the export string
    return export_string

# Write camera data to a file.
def write_camera_data(context, filepath, start, end, cams, scale, output_camcode, output_json, output_raw_frames):
    # Log the start of the function
    print("running write_camera_data...")
    
    # Generate a string representation of the camera data. The function cameras_to_string is not defined in this snippet.
    outputString = cameras_to_string(context, start, end, cams, scale, output_camcode, output_json, output_raw_frames)
    
    # Open the output file
    with open(filepath, 'w', encoding='utf-8') as f:
        # Write the frame range to the file
        f.write(f"Export frames {start} - {end}\n")
        
        # Write the names of the cameras to the file
        f.write(f"Export cameras {[c.name for c in cams]}\n")
        
        # Write the generated camera data string to the file
        f.write(outputString)
    
    # Return a status indicating that the function has finished
    return {'FINISHED'}

# Import the ExportHelper class from the bpy_extras.io_utils module. This is a helper class for creating export operators in Blender.
from bpy_extras.io_utils import ExportHelper

# Import various property types from the bpy.props module. These are used to create properties for Blender operators.
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty

# Import the Operator class from the bpy.types module. This is the base class for all operator types in Blender.
from bpy.types import Operator


# Define the ExportDiffusionString class, which is a type of Blender operator for exporting scene data.
class ExportDiffusionString(Operator, ExportHelper):
    
    # The bl_idname attribute represents the unique identifier for this operator.
    bl_idname = "export_scene.diffusion"
    
    # The bl_label attribute represents the name that will be displayed in the user interface for this operator.
    bl_label = "Export Diffusion"
    
    # The filename_ext attribute represents the default file extension for exported files.
    filename_ext = ".txt"
    
    # A string property that represents the type of files that can be selected in the file browser.
    # Default is set to "*.txt" and is hidden from the user interface.
    filter_glob: StringProperty(
        default="*.txt",
        options={'HIDDEN'},
        maxlen=255, 
    )
    
    # A boolean property to decide whether to output data in JSON format. Default is set to False.
    output_json: BoolProperty(name="Output JSON", default=False)
    
    # A boolean property to decide whether to output camera code. Default is set to False.
    output_cam_code: BoolProperty(name="Output cam_code", default=False)
    
    # A boolean property to decide whether to output raw frames. Default is set to True.
    output_raw_frames: BoolProperty(name="Output Raw Frames", default=True)    
    
    # An integer property representing the start frame for export. Default is set to -1.
    frame_start: IntProperty(name="Start", default=-1)
    
    # An integer property representing the end frame for export. Default is set to -1.
    frame_end: IntProperty(name="End", default=-1)    
    
    # An enumerated property representing which cameras to export. Options include the active camera,
    # selected cameras only, or all cameras in the scene. Default is set to the active camera.
    which_cams: EnumProperty(
        name="Which Cams",
        description="Which cameras to exprot",
        items=(
            ('ACTIVE', "Active", "Scene's active camera"),
            ('SELECTED', "Selected", "Selected cameras only"),
            ('ALL', "All", "All cameras in scene"),
        ),
        default='ACTIVE',
    )
    
    # A float property representing the conversion factor between Blender units and Diffusion units.
    # Default is set to 50.
    translation_scale: FloatProperty(default=50, name="Translation Scale", description = "Conversion factor between blender units and Diffusion units")
    
# This function is responsible for creating the user interface
def draw(self, context):
    layout = self.layout  # get the layout for the current context
    
    # create a new row and add a label
    row = layout.row()
    row.label(text="Which Cameras")
    
    # create a new row and add a property for choosing cameras
    row = layout.row()
    row.props_enum(self, "which_cams")
    
    # create a new row and add a label
    row = layout.row()
    row.label(text="Export Settings")                
    
    # create a new row and add a label
    row = layout.row()
    row.label(text="Frames")
    
    # set default values for frame_start and frame_end if they are not set
    if self.frame_start == -1:
        self.frame_start = bpy.context.scene.frame_start
    if self.frame_end == -1:
        self.frame_end = bpy.context.scene.frame_end
    
    # create a new row and add properties for frame_start and frame_end
    row.prop(self, "frame_start")
    row.prop(self, "frame_end")
    
    # create a new row and add a property for translation_scale
    row = layout.row()
    row.prop(self, "translation_scale")               
    
    # create a new row and add a property for output_cam_code
    row = layout.row()
    row.prop(self, "output_cam_code")
    
    # create a new row and add a property for output_json
    row = layout.row()
    row.prop(self, "output_json")
    
    # create a new row and add a property for output_raw_frames
    row = layout.row()
    row.prop(self, "output_raw_frames")
        

# This function is responsible for executing the main operation of the addon or script
def execute(self, context):
    export_cams = []  # initialize an empty list for cameras to be exported
    
    # decide which cameras to export based on the selected option
    if self.which_cams == "ACTIVE":
        export_cams = [context.scene.camera]  # get the active camera
    elif self.which_cams == "SELECTED":
        # get all selected objects that are cameras
        export_cams = [cam for cam in context.selected_objects if cam.type == 'CAMERA']
    elif self.which_cams == "ALL":
        # get all objects in the scene that are cameras
        export_cams = [cam for cam in context.scene.objects if cam.type == 'CAMERA']
        
    # call the write_camera_data function with the specified parameters
    return write_camera_data(context, self.filepath, self.frame_start, self.frame_end, export_cams, self.translation_scale, self.output_cam_code, self.output_json, self.output_raw_frames)

# This class is responsible for importing a diffusion string from a file.
# It extends from both a Blender Operator and ImportHelper, which provides a file dialog for importing files.
class ImportDiffusionString(Operator, ImportHelper):
    bl_idname = "import_scene.diffusion"  # the unique identifier for this operator
    bl_label = "Import Diffusion"  # the label for this operator
    filename_ext = ".txt"  # the extension of files that can be imported by this operator

    # A Blender StringProperty to specify the types of files that can be imported
    filter_glob: StringProperty(
        default="*.txt",  # default value is any txt file
        options={'HIDDEN'},  # this property is hidden
        maxlen=255,  # maximum length of the string is 255
    )

# tuple of classes to be registered
classes = (
    ExportDiffusionString,
    ImportDiffusionString,
)

# register or unregister classes if this script is run as the main script
if __name__ == "__main__":
    from bpy.utils import register_class, unregister_class
    for cls in classes:
        register_class(cls)  # register each class

# This function is responsible for executing the import operation
def execute(self, context):
    print("Executing import operator...")  # log to console
    with open(self.filepath, 'r', encoding='utf-8') as f:  # open the selected file
        content = f.read()  # read the file content
    keyframe_data = json.loads(content)  # parse the file content as JSON

    camera_obj = None
    for obj in context.scene.objects:  # iterate over all objects in the scene
        if obj.type == 'CAMERA':  # if the object is a camera
            camera_obj = obj  # use it as the camera object
            break

    if camera_obj is None:  # if no camera object was found
        bpy.ops.object.camera_add()  # add a new camera object
        camera_obj = bpy.context.active_object  # use the newly added camera as the camera object

    for frame, data in keyframe_data.items():  # iterate over all items in the keyframe data
        camera_obj.location = data["location"]  # set the location of the camera object
        camera_obj.rotation_euler = data["rotation"]  # set the rotation of the camera object
        camera_obj.keyframe_insert(data_path="location", frame=frame)  # insert a location keyframe
        camera_obj.keyframe_insert(data_path="rotation_euler", frame=frame)  # insert a rotation keyframe

    # It's unclear what this return statement does without context about write_camera_data function.
    # Assuming it writes camera data to somewhere.
    return write_camera_data(context, self.filepath, self.frame_start, self.frame_end, export_cams, 
    self.translation_scale, self.output_cam_code, self.output_json, self.output_raw_frames)


# Import option for Diffusion (.txt) files to the menu
def menu_func_import(self, context):
    # Add the operator to the layout
    self.layout.operator(ImportDiffusionString.bl_idname, text="Diffusion (.txt)")

# Export option for Diffusion (.txt) files to the menu
def menu_func_export(self, context):
    # Add the operator to the layout
    self.layout.operator(ExportDiffusionString.bl_idname, text="Diffusion (.txt)")

# Registers the operators and adds them to the import and export menus
def register():
    # Register the ImportDiffusionString operator
    bpy.utils.register_class(ImportDiffusionString)
    # Add the import function to the File > Import menu
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    # Register the ExportDiffusionString operator
    bpy.utils.register_class(ExportDiffusionString)
    # Add the export function to the File > Export menu
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

# Unregisters the operators and removes them from the import and export menus
def unregister():
    # Unregister the ImportDiffusionString operator
    bpy.utils.unregister_class(ImportDiffusionString)
    # Remove the import function from the File > Import menu
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    # Unregister the ExportDiffusionString operator
    bpy.utils.unregister_class(ExportDiffusionString)
    # Remove the export function from the File > Export menu
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

        
if __name__ == "__main__":
    register()