"""
Demonstration of laser and mirror.
"""

import sys


import optivis.scene as scene
import optivis.bench.components as components
# import optivis.view.canvas as canvas
import optivis.view.svg as svg



scene = scene.Scene(title="Example 1")

l1 = components.Laser(name="L1", tooltip="This is a laser")
m1 = components.SteeringMirror(name="M1", tooltip="This is a mirror")

scene.link(outputNode=l1.getOutputNode('out'), inputNode=m1.getInputNode('fr'), length=50)

scene.reference = l1

view = svg.Svg(scene)
view.export('scene.svg')
# gui = canvas.Simple(scene=scene)
# gui.show()
