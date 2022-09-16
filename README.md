# blender-export-diffusion
A Blender Add-on to add and a new export format to generate camera animation strings for the Deforum Diffusion notebook format. 

Deforum Notebook GH: https://github.com/deforum/stable-diffusion
Deforum Notebook Colab: https://colab.research.google.com/github/deforum/stable-diffusion/blob/main/Deforum_Stable_Diffusion.ipynb

# Installation
Download/clone the repo, or just the file `export_diffusion.py`. In Blender go to `Edit > Preferences > Add-ons`, click `Install` and select the `export_diffusion.py` file. You should then see a new add-on in the list called "Export Camera Animation to Diffusion Notebook String". Click the checkbox to enable. There should now be a new entry under `File > Export > Diffusion Notebook String`.

# Export Settings 
* Which Cameras
    * Active -- The single camera currently designated as "active" -- AKA the one shown in the render preview.
    * Selected -- Only selected cameras
    * All -- All cameras in scene
* Start Frame - Which frame to start from, inclusive. Note: the first frame will always be exporteds as frame 0
* End Frame - Which frame to stop at, exclusive. 
* Translation Scale -- How much to multiply blender world units by for the translate x,y,z values.

# Usage Notes
After exporting, open the text file. All exported cameras will have their own block of strings. The strings are designed as python code you can copy/paste as a block into the notebook animation section.

For best results, set your Blender framerate and frame counts to match your notebook settings.
For more rapid testing, this animation preview notebook is great: https://colab.research.google.com/github/pharmapsychotic/ai-notebooks/blob/main/pharmapsychotic_AnimationPreview.ipynb

# Author & License
MIT license.
Written by Michael Walker <micwalk@gmail.com> Twitter: [@mwalk10](twitter.com/mwalk10)

