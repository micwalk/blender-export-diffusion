bl_info = {
    "name": "Export Camera Animation to Diffusion Notebook String",
    "author": "Michael Walker (@mwalk10)",
    "version": (1, 1, 4),
    "blender": (3, 3, 0),
    "location": "File > Export > Diffusion Notebook String",
    "description": "Export camera animations formatted for use in Deforum diffusion collab notebook animations.",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}


import bpy
from math import degrees
from mathutils import Vector
from bpy import context
from math import isclose
import json

def roundZero(num, magnitude_thresh = 0.00001):
    if abs(num) > magnitude_thresh:
        return num
    else:
        return 0
        
def arr_to_keyframes(arr):
    keyframes = ""
    for i, val in enumerate(arr):
        val = roundZero(val)
        #if we previously had a zero, then we can stop emitting zeroes until right before the next nonzero
        last_is_same = i > 0 and isclose(val, roundZero(arr[i-1]))
        next_is_same = (i+1) < len(arr) and isclose(val, roundZero(arr[i+1]))
        
        omit = last_is_same and next_is_same
        
        if not omit:
            keyframes += f"{i}:({val}),"
    return keyframes
        
def cameras_to_string(context, startFrame, endFrame, cameras, translation_scale = 50, output_camcode = True, output_json = False,):
    # get the current selection
    scene = context.scene
    currentFrame = scene.frame_current
    
    if len(cameras) == 0:
        print("Nothing selected!")
        return "No Cameras selected for export"

    export_string = ""
    
    # iterate through the selected objects
    for sel in cameras:
        #init
        scene.frame_set(startFrame)
        
        translation_x = []
        translation_y = []
        translation_z = []
        rotation_3d_x = []
        rotation_3d_y = []
        rotation_3d_z = []
        
        oldMat = sel.matrix_world.copy()
        oldRot = oldMat.to_quaternion()
        
        #cycle trough all the animated frames
        for frame in range(startFrame+1, endFrame):
            #Update animation frame to grab values from
            scene.frame_set(frame)
            
            newMat = sel.matrix_world.copy() #local to world matrix
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
        
        #Done looping over frames, now to format for print
        export_string += f"\nCamera Export: {sel.name}\n"
        
        
        export_string += f'translation_x = "{arr_to_keyframes(translation_x)}" #@param {{type:"string"}}\n'
        export_string += f'translation_y = "{arr_to_keyframes(translation_y)}" #@param {{type:"string"}}\n'
        export_string += f'translation_z = "{arr_to_keyframes(translation_z)}" #@param {{type:"string"}}\n'
        export_string += f'rotation_3d_x = "{arr_to_keyframes(rotation_3d_x)}" #@param {{type:"string"}}\n'
        export_string += f'rotation_3d_y = "{arr_to_keyframes(rotation_3d_y)}" #@param {{type:"string"}}\n'
        export_string += f'rotation_3d_z = "{arr_to_keyframes(rotation_3d_z)}" #@param {{type:"string"}}\n'
        
        if output_camcode:
            export_string += f'cam_code:\n(translation_x,translation_y,translation_z,rotation_3d_x,rotation_3d_y,rotation_3d_z) = ("{arr_to_keyframes(translation_x)}", "{arr_to_keyframes(translation_y)}", "{arr_to_keyframes(translation_z)}", "{arr_to_keyframes(rotation_3d_x)}", "{arr_to_keyframes(rotation_3d_y)}", "{arr_to_keyframes(rotation_3d_z)}")\n'
        
        if output_json:
            jsondict = {
                "translation_x" : translation_x,
                "translation_y" : translation_y,
                "translation_z" : translation_z,
                "rotation_3d_x" : rotation_3d_x,
                "rotation_3d_y" : rotation_3d_y,
                "rotation_3d_z" : rotation_3d_z}
            export_string += f"JSON:\n {json.dumps(jsondict)}\n"
        
        export_string += "\n"
                
    #Done saving all cameras, restore original animation frame
    scene.frame_set(currentFrame)
    return export_string

def write_camera_data(context, filepath, start, end, cams, scale, output_camcode, output_json):
    print("running write_camera_data...")
    outputString = cameras_to_string(context, start, end, cams, scale, output_camcode, output_json)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Export frames {start} - {end}\n")
        f.write(f"Export cameras {[c.name for c in cams]}\n")
        f.write(outputString)
    return {'FINISHED'}


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty
from bpy.types import Operator


class ExportDiffusionString(Operator, ExportHelper):
    """Export animation keyframes in the format of Deforum Diffusion camera animation keyframes"""
    bl_idname = "export_scene.diffusion"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Diffusion"

    # ExportHelper mixin class uses this
    filename_ext = ".txt"

    filter_glob: StringProperty(
        default="*.txt",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )


#    animation_mode: EnumProperty(
#        name="Animation Mode",
#        description="2d or 3d. (only 3d supported currently)",
#        items=(
#            ('3D', "3d", "3d Camera Movement"),
#        ),
#        default='3D',
#    )
    
    output_json: BoolProperty(name="Output JSON", default=False)
    output_cam_code: BoolProperty(name="Output cam_code", default=True)
    
    frame_start: IntProperty(name="Start", default=-1)
    frame_end: IntProperty(name="End", default=-1)#bpy.context.scene.frame_end
    
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

#        row = layout.row()
#        row.prop(self, "animation_mode")        
        row = layout.row()
        row.prop(self, "translation_scale")        
        
        row = layout.row()
        row.prop(self, "output_cam_code")
        row = layout.row()
        row.prop(self, "output_json")
        
    def execute(self, context):
        export_cams = []
        if self.which_cams == "ACTIVE":
            export_cams = [context.scene.camera]
        elif self.which_cams == "SELECTED":
            export_cams = [cam for cam in context.selected_objects if cam.type == 'CAMERA']
        elif self.which_cams == "ALL":
            export_cams = [cam for cam in context.scene.objects if cam.type == 'CAMERA']
        return write_camera_data(context, self.filepath, self.frame_start, self.frame_end, export_cams, 
        self.translation_scale, self.output_cam_code, self.output_json)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportDiffusionString.bl_idname, text="Diffusion Notebook String")


# Register and add to the "file selector" menu (required to use F3 search "Text Export Operator" for quick access).
def register():
    bpy.utils.register_class(ExportDiffusionString)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportDiffusionString)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_scene.diffusion('INVOKE_DEFAULT')
