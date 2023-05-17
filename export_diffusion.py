bl_info = {
    "name": "Export Camera Animation to Deforum collab/webui",
    "author": "Michael Walker (@mwalk10)",
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

def roundZero(num, magnitude_thresh = 0.00001):
    if abs(num) > magnitude_thresh:
        return num
    else:
        return 0
        
def arr_to_keyframes(arr):
    keyframes = ""
    for i, val in enumerate(arr):
        val = roundZero(val)
        last_is_same = i > 0 and isclose(val, roundZero(arr[i-1]))
        next_is_same = (i+1) < len(arr) and isclose(val, roundZero(arr[i+1]))        
        omit = last_is_same and next_is_same        
        if not omit:
            keyframes += f"{i}:({val}),"
    return keyframes
        
def cameras_to_string(context, startFrame, endFrame, cameras, translation_scale = 50, output_camcode = True, output_json = False, output_raw_frames = False):
    scene = context.scene
    currentFrame = scene.frame_current    
    if len(cameras) == 0:
        print("Nothing selected!")
        return "No Cameras selected for export"
    export_string = ""
    for sel in cameras:
        scene.frame_set(startFrame)      
        translation_x = []
        translation_y = []
        translation_z = []
        rotation_3d_x = []
        rotation_3d_y = []
        rotation_3d_z = []       
        oldMat = sel.matrix_world.copy()
        oldRot = oldMat.to_quaternion()
        for frame in range(startFrame+1, endFrame):
            scene.frame_set(frame)            
            newMat = sel.matrix_world.copy() 
            newRot = newMat.to_quaternion()                   
            worldToLocal = newMat.inverted()
            wlRot = worldToLocal.to_quaternion()       
            posDiff = newMat.to_translation() - oldMat.to_translation()
            posDiffLocal = wlRot @ posDiff           
            translation_x.append(translation_scale*posDiffLocal.x)
            translation_y.append(translation_scale*posDiffLocal.y)
            translation_z.append(-translation_scale*posDiffLocal.z)           
            rotDiff = oldRot.rotation_difference(newRot).to_euler("XYZ")           
            rotation_3d_x.append(degrees(rotDiff.x))
            rotation_3d_y.append(degrees(-rotDiff.y))
            rotation_3d_z.append(degrees(-rotDiff.z))                       
            oldMat = newMat
            oldRot = newRot
        if not output_raw_frames:
            export_string += f"\nCamera Export: {sel.name}\n"      
            export_string += f'translation_x = "{arr_to_keyframes(translation_x)}" #@param {{type:"string"}}\n'
            export_string += f'translation_y = "{arr_to_keyframes(translation_y)}" #@param {{type:"string"}}\n'
            export_string += f'translation_z = "{arr_to_keyframes(translation_z)}" #@param {{type:"string"}}\n'
            export_string += f'rotation_3d_x = "{arr_to_keyframes(rotation_3d_x)}" #@param {{type:"string"}}\n'
            export_string += f'rotation_3d_y = "{arr_to_keyframes(rotation_3d_y)}" #@param {{type:"string"}}\n'
            export_string += f'rotation_3d_z = "{arr_to_keyframes(rotation_3d_z)}" #@param {{type:"string"}}\n'        
        if output_camcode:
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


def write_camera_data(context, filepath, start, end, cams, scale, output_camcode, output_json, output_raw_frames):
    print("running write_camera_data...")
    # Generate a string representation of the camera data. The function cameras_to_string is not defined in this snippet.
    outputString = cameras_to_string(context, start, end, cams, scale, output_camcode, output_json, output_raw_frames)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Export frames {start} - {end}\n")
        f.write(f"Export cameras {[c.name for c in cams]}\n")
        f.write(outputString)
    return {'FINISHED'}
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty
from bpy.types import Operator

def write_camera_data(context, filepath, start, end, cams, scale, output_camcode, output_json, output_raw_frames):
    print("running write_camera_data...")
    outputString = cameras_to_string(context, start, end, cams, scale, output_camcode, output_json, output_raw_frames)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Export frames {start} - {end}\n")
        f.write(f"Export cameras {[c.name for c in cams]}\n")
        f.write(outputString)
    return {'FINISHED'}
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty
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
    translation_scale: FloatProperty(default=50, name="Translation Scale", description = "Conversion factor between blender units and Diffusion units")
# Create the user interface    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Which Cameras")
        row = layout.row()
        row.props_enum(self, "which_cams")
        row = layout.row()
        row.label(text="Export Settings")                
        row = layout.row()
        row.label(text="Frames")
        if self.frame_start == -1:
            self.frame_start = bpy.context.scene.frame_start
        if self.frame_end == -1:
            self.frame_end = bpy.context.scene.frame_end
        row.prop(self, "frame_start")
        row.prop(self, "frame_end")
        row = layout.row()
        row.prop(self, "translation_scale")               
        row = layout.row()
        row.prop(self, "output_cam_code")
        row = layout.row()
        row.prop(self, "output_json")
        row = layout.row()
        row.prop(self, "output_raw_frames")

# Execute the main operation of the addon or script        
    def execute(self, context):
        export_cams = []
        if self.which_cams == "ACTIVE":
            export_cams = [context.scene.camera]
        elif self.which_cams == "SELECTED":
            export_cams = [cam for cam in context.selected_objects if cam.type == 'CAMERA']
        elif self.which_cams == "ALL":
            export_cams = [cam for cam in context.scene.objects if cam.type == 'CAMERA']
        return write_camera_data(context, self.filepath, self.frame_start, self.frame_end, export_cams, self.translation_scale, self.output_cam_code, self.output_json, self.output_raw_frames)
    

# Import a diffusion string from a file.
class ImportDiffusionString(Operator, ImportHelper):
    bl_idname = "import_scene.diffusion"  
    bl_label = "Import Diffusion"
    filename_ext = ".txt"
    filter_glob: StringProperty(
        default="*.txt",
        options={'HIDDEN'},
        maxlen=255, 
    )
classes = (
    ExportDiffusionString,
    ImportDiffusionString,
)

# register or unregister classes if this script is run as the main script
if __name__ == "__main__":
    from bpy.utils import register_class, unregister_class
    for cls in classes:
        register_class(cls)

# Execute the import operation
def execute(self, context):
    print("Executing import operator...")
    with open(self.filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    keyframe_data = json.loads(content)
    camera_obj = None
    for obj in context.scene.objects:
        if obj.type == 'CAMERA':
            camera_obj = obj
            break
    if camera_obj is None:
        bpy.ops.object.camera_add()
        camera_obj = bpy.context.active_object
    for frame, data in keyframe_data.items():
        camera_obj.location = data["location"]
        camera_obj.rotation_euler = data["rotation"]
        camera_obj.keyframe_insert(data_path="location", frame=frame)
        camera_obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    return write_camera_data(context, self.filepath, self.frame_start, self.frame_end, export_cams, 
    self.translation_scale, self.output_cam_code, self.output_json, self.output_raw_frames)

# Import option for Diffusion (.txt) files to the menu
def menu_func_import(self, context):
    self.layout.operator(ImportDiffusionString.bl_idname, text="Diffusion (.txt)")

# Export option for Diffusion (.txt) files to the menu
def menu_func_export(self, context):
    self.layout.operator(ExportDiffusionString.bl_idname, text="Diffusion (.txt)")

# Registers the operators and adds them to the import and export menus
def register():
    bpy.utils.register_class(ImportDiffusionString)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    bpy.utils.register_class(ExportDiffusionString)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

# Unregisters the operators and removes them from the import and export menus
def unregister():
    bpy.utils.unregister_class(ImportDiffusionString)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    bpy.utils.unregister_class(ExportDiffusionString)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
        
if __name__ == "__main__":
    register()