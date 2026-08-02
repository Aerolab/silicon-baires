"""Verifies the full geometry-nodes path from Python."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bpy, blib

R = str(pathlib.Path(__file__).resolve().parents[1] / "renders")

blib.reset()
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1)
host = bpy.context.object
bpy.ops.object.shade_smooth()

ng, gin, gout = blib.gn_tree("Scatter", inputs=[("Density", "NodeSocketFloat", 300.0),
                                                ("Size", "NodeSocketFloat", 0.06)])
n = ng.nodes
dist = n.new("GeometryNodeDistributePointsOnFaces"); dist.location = (-350, 0)
dist.distribute_method = "POISSON"
print("DIST SOCKETS:", blib.sockets(dist))

inst = n.new("GeometryNodeInstanceOnPoints"); inst.location = (0, 0)
ico = n.new("GeometryNodeMeshIcoSphere"); ico.location = (-350, -300)
ico.inputs["Subdivisions"].default_value = 2
join = n.new("GeometryNodeJoinGeometry"); join.location = (350, 0)
# GOTCHA: GN instances do NOT inherit the host object materials
setmat = n.new("GeometryNodeSetMaterial"); setmat.location = (150, -150)

L = ng.links.new
L(gin.outputs["Geometry"], dist.inputs["Mesh"])
L(gin.outputs["Density"], dist.inputs["Density Max"])
L(gin.outputs["Size"], ico.inputs["Radius"])
L(dist.outputs["Points"], inst.inputs["Points"])
L(dist.outputs["Rotation"], inst.inputs["Rotation"])
L(ico.outputs["Mesh"], inst.inputs["Instance"])
L(inst.outputs["Instances"], setmat.inputs["Geometry"])
L(setmat.outputs["Geometry"], join.inputs["Geometry"])
L(gin.outputs["Geometry"], join.inputs["Geometry"])
L(join.outputs["Geometry"], gout.inputs["Geometry"])

mod = blib.gn_apply(host, ng, Density=800.0, Size=0.05)

verde = blib.pbr("Verde", (0.15, 0.6, 0.35), roughness=0.35)
naranja = blib.pbr("Naranja", (0.95, 0.45, 0.1), roughness=0.25)
setmat.inputs["Material"].default_value = naranja
blib.assign(host, verde)
blib.hdri(strength=0.5)
blib.three_point()
blib.camera(azimuth=40, elevation=18)
blib.report()
print("OUT:", blib.render(f"{R}/test_geonodes.png", "CYCLES", samples=128,
                          resolution=(800, 600), view_transform="AgX"))
