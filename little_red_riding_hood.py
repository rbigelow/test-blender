"""
Little Red Riding Hood — Anime Battle Heroine
Blender Python Script (bpy API)

Run this script inside Blender's Scripting workspace (Text Editor → Run Script)
or via the command line:
    blender --background --python little_red_riding_hood.py

Requirements: Blender 3.x or 4.x
"""

import bpy
import bmesh
import math
import mathutils
from mathutils import Vector, Matrix

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def clear_scene():
    """Remove every object, mesh, armature, material, and action in the scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=True)
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.armatures):
        bpy.data.armatures.remove(block)
    for block in list(bpy.data.materials):
        bpy.data.materials.remove(block)
    for block in list(bpy.data.actions):
        bpy.data.actions.remove(block)
    for block in list(bpy.data.curves):
        bpy.data.curves.remove(block)


def get_or_create_collection(name, parent=None):
    """Return (and link into the scene) a named collection."""
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
    parent_col = parent if parent else bpy.context.scene.collection
    if col.name not in [c.name for c in parent_col.children]:
        parent_col.children.link(col)
    return col


def link_to_collection(obj, collection):
    """Move obj from Scene Collection into the target collection."""
    if obj.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(obj)
    for col in obj.users_collection:
        col.objects.unlink(obj)
    collection.objects.link(obj)


def set_active(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def deselect_all():
    bpy.ops.object.select_all(action="DESELECT")


def add_subsurf(obj, levels=2, render_levels=3):
    mod = obj.modifiers.new("Subdivision", "SUBSURF")
    mod.levels = levels
    mod.render_levels = render_levels
    return mod


def add_solidify(obj, thickness=0.02):
    mod = obj.modifiers.new("Solidify", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 1.0
    return mod


def smooth_shade(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------

def build_collections():
    root = get_or_create_collection("LittleRedRidingHood")
    col_mesh = get_or_create_collection("Mesh", parent=root)
    col_body = get_or_create_collection("Body", parent=col_mesh)
    col_clothing = get_or_create_collection("Clothing", parent=col_mesh)
    col_accessories = get_or_create_collection("Accessories", parent=col_mesh)
    col_armature = get_or_create_collection("Armature", parent=root)
    col_controls = get_or_create_collection("Controls", parent=root)
    return {
        "root": root,
        "mesh": col_mesh,
        "body": col_body,
        "clothing": col_clothing,
        "accessories": col_accessories,
        "armature": col_armature,
        "controls": col_controls,
    }


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

def make_material_skin():
    """Smooth anime complexion with slight subsurface scattering."""
    mat = bpy.data.materials.new("MAT_Skin")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    bsdf.inputs["Base Color"].default_value = (0.98, 0.85, 0.76, 1.0)
    bsdf.inputs["Subsurface Weight"].default_value = 0.25
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.3)
    bsdf.inputs["Roughness"].default_value = 0.5
    bsdf.inputs["Specular IOR Level"].default_value = 0.3

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_material_cloak():
    """Deep red fabric with subtle roughness variation."""
    mat = bpy.data.materials.new("MAT_Cloak")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (900, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (600, 0)
    bsdf.inputs["Base Color"].default_value = (0.55, 0.02, 0.02, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.8
    bsdf.inputs["Specular IOR Level"].default_value = 0.1
    bsdf.inputs["Sheen Weight"].default_value = 0.4
    bsdf.inputs["Sheen Roughness"].default_value = 0.6

    # Fabric noise for subtle texture
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (0, -200)
    noise.inputs["Scale"].default_value = 80.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.7

    mix_rgb = nodes.new("ShaderNodeMixRGB")
    mix_rgb.location = (300, 0)
    mix_rgb.blend_type = "MULTIPLY"
    mix_rgb.inputs["Fac"].default_value = 0.15
    mix_rgb.inputs["Color1"].default_value = (0.55, 0.02, 0.02, 1.0)

    links.new(noise.outputs["Color"], mix_rgb.inputs["Color2"])
    links.new(mix_rgb.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_material_hair():
    """Toon-style hair with anisotropic highlights."""
    mat = bpy.data.materials.new("MAT_Hair")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (800, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (500, 0)
    bsdf.inputs["Base Color"].default_value = (0.08, 0.04, 0.02, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Specular IOR Level"].default_value = 0.9
    bsdf.inputs["Anisotropic"].default_value = 0.8
    bsdf.inputs["Anisotropic Rotation"].default_value = 0.1

    # Toon highlight band via colour ramp
    layer_weight = nodes.new("ShaderNodeLayerWeight")
    layer_weight.location = (0, 100)
    layer_weight.inputs["Blend"].default_value = 0.6

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (200, 100)
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    mix = nodes.new("ShaderNodeMixRGB")
    mix.location = (400, 0)
    mix.blend_type = "ADD"
    mix.inputs["Fac"].default_value = 0.35

    links.new(layer_weight.outputs["Facing"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs["Color2"])
    mix.inputs["Color1"].default_value = (0.08, 0.04, 0.02, 1.0)
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_material_tunic():
    """Dark charcoal tunic."""
    mat = bpy.data.materials.new("MAT_Tunic")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    bsdf.inputs["Base Color"].default_value = (0.12, 0.10, 0.10, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_material_boots():
    """Brown leather boots."""
    mat = bpy.data.materials.new("MAT_Boots")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    bsdf.inputs["Base Color"].default_value = (0.22, 0.10, 0.05, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.7
    bsdf.inputs["Specular IOR Level"].default_value = 0.3

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_material_sword():
    """Polished steel blade with sharp specular."""
    mat = bpy.data.materials.new("MAT_Sword")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    bsdf.inputs["Base Color"].default_value = (0.75, 0.75, 0.80, 1.0)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.08
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    bsdf.inputs["Anisotropic"].default_value = 0.6

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_material_wolf_armor():
    """Gunmetal wolf-themed armor plate."""
    mat = bpy.data.materials.new("MAT_WolfArmor")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    bsdf.inputs["Base Color"].default_value = (0.18, 0.18, 0.20, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.85
    bsdf.inputs["Roughness"].default_value = 0.4
    bsdf.inputs["Specular IOR Level"].default_value = 0.7

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_material_eye():
    """Bright anime eye — emissive iris."""
    mat = bpy.data.materials.new("MAT_Eye")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    bsdf.inputs["Base Color"].default_value = (0.02, 0.35, 0.70, 1.0)
    bsdf.inputs["Emission Color"].default_value = (0.04, 0.60, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 0.8
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Specular IOR Level"].default_value = 0.9

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_material_basket():
    """Woven wicker basket."""
    mat = bpy.data.materials.new("MAT_Basket")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    bsdf.inputs["Base Color"].default_value = (0.55, 0.38, 0.18, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.9

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ---------------------------------------------------------------------------
# Mesh helpers — base shapes
# ---------------------------------------------------------------------------

def create_uv_sphere(name, location, radius=1.0, segments=16, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, segments=segments, ring_count=rings, location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def create_cylinder(name, location, radius=1.0, depth=1.0, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=depth, vertices=verts, location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def create_cube(name, location, size=1.0):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def apply_scale(obj):
    deselect_all()
    set_active(obj)
    bpy.ops.object.transform_apply(scale=True)


# ---------------------------------------------------------------------------
# Body meshes
# ---------------------------------------------------------------------------

def build_head(collections, mat_skin, mat_eye):
    """Anime head: slightly large cranium, small chin, big eye sockets."""
    deselect_all()
    bm = bmesh.new()

    # Build head from a UV sphere then squash/stretch verts
    bmesh.ops.create_uvsphere(
        bm, u_segments=20, v_segments=16, radius=0.13
    )
    # Flatten chin area — move bottom verts up slightly
    for v in bm.verts:
        if v.co.z < -0.09:
            v.co.z = v.co.z * 0.6 + 0.01
        # Slightly widen cheeks
        if -0.04 < v.co.z < 0.03:
            v.co.x *= 1.08
            v.co.y *= 1.08
        # Inflate cranium
        if v.co.z > 0.07:
            v.co.z *= 1.15
            v.co.x *= 1.05
            v.co.y *= 1.05

    mesh = bpy.data.meshes.new("Mesh_Head")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Head", mesh)
    obj.location = (0, 0, 1.62)
    smooth_shade(obj)
    add_subsurf(obj, levels=2, render_levels=3)
    obj.data.materials.append(mat_skin)
    collections["body"].objects.link(obj)

    # --- Eyes (left & right) ---
    for side, sign in (("L", 1), ("R", -1)):
        eye = create_uv_sphere(
            f"Eye_{side}", (sign * 0.04, -0.10, 1.645), radius=0.022, segments=12, rings=8
        )
        eye.data.materials.append(mat_eye)
        smooth_shade(eye)
        link_to_collection(eye, collections["body"])

    return obj


def build_body(collections, mat_skin, mat_tunic):
    """Torso with proper proportion for anime female figure."""
    deselect_all()
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.14)

    # Stretch to torso shape
    for v in bm.verts:
        v.co.z *= 2.5          # elongate
        if v.co.z > 0.12:      # shoulders — widen
            v.co.x *= 1.2
        if -0.05 < v.co.z < 0.12:  # waist — narrow
            v.co.x *= 0.72
            v.co.y *= 0.72
        if v.co.z < -0.05:     # hips — widen
            v.co.x *= 1.15
            v.co.y *= 0.85

    mesh = bpy.data.meshes.new("Mesh_Torso")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Torso", mesh)
    obj.location = (0, 0, 1.33)
    smooth_shade(obj)
    add_subsurf(obj, levels=2)
    obj.data.materials.append(mat_tunic)
    collections["body"].objects.link(obj)
    return obj


def build_neck(collections, mat_skin):
    neck = create_cylinder("Neck", (0, 0, 1.52), radius=0.038, depth=0.09, verts=12)
    smooth_shade(neck)
    add_subsurf(neck, levels=1)
    neck.data.materials.append(mat_skin)
    link_to_collection(neck, collections["body"])
    return neck


def build_arms(collections, mat_skin):
    arm_objs = []
    for side, sign in (("L", 1), ("R", -1)):
        # Upper arm
        ua = create_cylinder(
            f"UpperArm_{side}",
            (sign * 0.20, 0, 1.42),
            radius=0.035, depth=0.22, verts=10
        )
        ua.rotation_euler = (0, math.radians(90), 0)
        apply_scale(ua)
        smooth_shade(ua)
        add_subsurf(ua, levels=1)
        ua.data.materials.append(mat_skin)
        link_to_collection(ua, collections["body"])
        arm_objs.append(ua)

        # Elbow sphere for smooth deformation
        elbow = create_uv_sphere(
            f"Elbow_{side}", (sign * 0.32, 0, 1.42), radius=0.036, segments=10, rings=8
        )
        smooth_shade(elbow)
        elbow.data.materials.append(mat_skin)
        link_to_collection(elbow, collections["body"])

        # Forearm
        fa = create_cylinder(
            f"Forearm_{side}",
            (sign * 0.44, 0, 1.42),
            radius=0.030, depth=0.22, verts=10
        )
        fa.rotation_euler = (0, math.radians(90), 0)
        apply_scale(fa)
        smooth_shade(fa)
        add_subsurf(fa, levels=1)
        fa.data.materials.append(mat_skin)
        link_to_collection(fa, collections["body"])
        arm_objs.append(fa)

        # Hand — simple oval
        hand = create_uv_sphere(
            f"Hand_{side}", (sign * 0.56, 0, 1.42), radius=0.032, segments=12, rings=8
        )
        hand.scale = (1.0, 0.7, 0.6)
        apply_scale(hand)
        smooth_shade(hand)
        hand.data.materials.append(mat_skin)
        link_to_collection(hand, collections["body"])
        arm_objs.append(hand)

    return arm_objs


def build_legs(collections, mat_skin):
    leg_objs = []
    for side, sign in (("L", 1), ("R", -1)):
        # Thigh
        thigh = create_cylinder(
            f"Thigh_{side}",
            (sign * 0.09, 0, 1.10),
            radius=0.055, depth=0.32, verts=12
        )
        smooth_shade(thigh)
        add_subsurf(thigh, levels=1)
        thigh.data.materials.append(mat_skin)
        link_to_collection(thigh, collections["body"])
        leg_objs.append(thigh)

        # Knee sphere
        knee = create_uv_sphere(
            f"Knee_{side}", (sign * 0.09, 0, 0.93), radius=0.050, segments=10, rings=8
        )
        smooth_shade(knee)
        knee.data.materials.append(mat_skin)
        link_to_collection(knee, collections["body"])

        # Shin
        shin = create_cylinder(
            f"Shin_{side}",
            (sign * 0.09, 0, 0.75),
            radius=0.042, depth=0.32, verts=12
        )
        smooth_shade(shin)
        add_subsurf(shin, levels=1)
        shin.data.materials.append(mat_skin)
        link_to_collection(shin, collections["body"])
        leg_objs.append(shin)

        # Foot
        foot = create_uv_sphere(
            f"Foot_{side}", (sign * 0.09, 0.04, 0.58), radius=0.050, segments=12, rings=8
        )
        foot.scale = (0.6, 1.4, 0.45)
        apply_scale(foot)
        smooth_shade(foot)
        foot.data.materials.append(mat_skin)
        link_to_collection(foot, collections["body"])
        leg_objs.append(foot)

    return leg_objs


# ---------------------------------------------------------------------------
# Hair
# ---------------------------------------------------------------------------

def build_hair(collections, mat_hair):
    """Long, flowing hair as a stylised shell."""
    deselect_all()
    bm = bmesh.new()

    # Main hair volume — elongated sphere behind/over head
    bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=14, radius=0.16)
    for v in bm.verts:
        v.co.z += 0.06          # shift up to cap
        v.co.y -= 0.04          # shift back
        v.co.z *= 2.0           # elongate downward for long hair
        if v.co.z < 0:
            v.co.z *= 1.4       # extra length at bottom
        # Side flares for anime hair
        if abs(v.co.x) > 0.08 and v.co.z < 0.1:
            v.co.x *= 1.25

    mesh = bpy.data.meshes.new("Mesh_Hair")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Hair", mesh)
    obj.location = (0, 0, 1.62)
    smooth_shade(obj)
    add_subsurf(obj, levels=2)
    obj.data.materials.append(mat_hair)
    collections["body"].objects.link(obj)

    # Hair bangs — front fringe plate
    bm2 = bmesh.new()
    bmesh.ops.create_uvsphere(bm2, u_segments=12, v_segments=8, radius=0.14)
    for v in bm2.verts:
        if v.co.y > 0:
            bm2.verts.remove(v)

    mesh2 = bpy.data.meshes.new("Mesh_Bangs")
    bm2.to_mesh(mesh2)
    bm2.free()

    bangs = bpy.data.objects.new("Bangs", mesh2)
    bangs.location = (0, -0.02, 1.72)
    smooth_shade(bangs)
    add_subsurf(bangs, levels=2)
    bangs.data.materials.append(mat_hair)
    collections["body"].objects.link(bangs)

    return obj


# ---------------------------------------------------------------------------
# Clothing
# ---------------------------------------------------------------------------

def build_cloak(collections, mat_cloak):
    """Red hooded cloak — cape + hood."""
    deselect_all()
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=16, radius=0.38)

    # Remove front half to create open cape silhouette
    to_remove = [v for v in bm.verts if v.co.y < -0.05]
    bmesh.ops.delete(bm, geom=to_remove, context="VERTS")

    for v in bm.verts:
        v.co.z -= 0.10           # drop cloak
        v.co.z *= 3.0            # lengthen to ankle
        if v.co.z < -0.6:        # flare at hem
            v.co.x *= 1.2
            v.co.y *= 1.2
        # Shoulder bump
        if v.co.z > 0.15:
            v.co.z *= 1.1

    mesh = bpy.data.meshes.new("Mesh_Cloak")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Cloak", mesh)
    obj.location = (0, 0.02, 1.50)
    smooth_shade(obj)
    add_subsurf(obj, levels=2)
    obj.data.materials.append(mat_cloak)
    collections["clothing"].objects.link(obj)

    # Hood — hemisphere sitting on head
    bm_h = bmesh.new()
    bmesh.ops.create_uvsphere(bm_h, u_segments=16, v_segments=10, radius=0.20)
    to_remove = [v for v in bm_h.verts if v.co.z < 0]
    bmesh.ops.delete(bm_h, geom=to_remove, context="VERTS")
    for v in bm_h.verts:
        v.co.y += 0.02
        v.co.z *= 0.75

    mesh_h = bpy.data.meshes.new("Mesh_Hood")
    bm_h.to_mesh(mesh_h)
    bm_h.free()

    hood = bpy.data.objects.new("Hood", mesh_h)
    hood.location = (0, 0, 1.70)
    smooth_shade(hood)
    add_subsurf(hood, levels=2)
    hood.data.materials.append(mat_cloak)
    collections["clothing"].objects.link(hood)

    return obj, hood


def build_tunic(collections, mat_tunic):
    """Form-fitting battle tunic under the cloak."""
    deselect_all()
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.155)
    for v in bm.verts:
        v.co.z *= 2.3
        if v.co.z > 0.10:
            v.co.x *= 1.18     # shoulder width
        if -0.06 < v.co.z < 0.10:
            v.co.x *= 0.78
            v.co.y *= 0.78
        if v.co.z < -0.06:
            v.co.x *= 1.05
            v.co.y *= 0.88

    mesh = bpy.data.meshes.new("Mesh_Tunic")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Tunic", mesh)
    obj.location = (0, 0, 1.33)
    smooth_shade(obj)
    add_subsurf(obj, levels=2)
    obj.data.materials.append(mat_tunic)
    collections["clothing"].objects.link(obj)
    return obj


def build_boots(collections, mat_boots):
    """Knee-high leather boots."""
    boot_objs = []
    for side, sign in (("L", 1), ("R", -1)):
        # Shaft
        shaft = create_cylinder(
            f"BootShaft_{side}",
            (sign * 0.09, 0, 0.68),
            radius=0.052, depth=0.34, verts=12
        )
        smooth_shade(shaft)
        add_subsurf(shaft, levels=1)
        shaft.data.materials.append(mat_boots)
        link_to_collection(shaft, collections["clothing"])
        boot_objs.append(shaft)

        # Sole / toe
        toe = create_uv_sphere(
            f"BootToe_{side}",
            (sign * 0.09, 0.06, 0.56),
            radius=0.055, segments=12, rings=8
        )
        toe.scale = (0.65, 1.5, 0.4)
        apply_scale(toe)
        smooth_shade(toe)
        toe.data.materials.append(mat_boots)
        link_to_collection(toe, collections["clothing"])
        boot_objs.append(toe)

    return boot_objs


def build_gloves(collections, mat_boots):
    """Short tactical gloves."""
    glove_objs = []
    for side, sign in (("L", 1), ("R", -1)):
        glove = create_uv_sphere(
            f"Glove_{side}", (sign * 0.56, 0, 1.42), radius=0.036, segments=10, rings=8
        )
        glove.scale = (1.0, 0.72, 0.62)
        apply_scale(glove)
        smooth_shade(glove)
        glove.data.materials.append(mat_boots)
        link_to_collection(glove, collections["clothing"])
        glove_objs.append(glove)
    return glove_objs


# ---------------------------------------------------------------------------
# Accessories
# ---------------------------------------------------------------------------

def build_sword(collections, mat_sword):
    """Hidden sword — starts concealed, rig control reveals it."""
    deselect_all()
    bm = bmesh.new()

    # Blade — thin elongated hexagonal prism
    verts_data = [
        (0.0, -0.006,  0.0),
        (0.0,  0.006,  0.0),
        (0.003, 0.0,   0.0),
        (-0.003, 0.0,  0.0),
        (0.0, -0.004,  0.60),
        (0.0,  0.004,  0.60),
        (0.0,  0.0,    0.65),   # tip
    ]
    faces_data = [
        (0, 2, 4), (2, 5, 4), (2, 1, 5), (1, 3, 5),
        (3, 0, 4), (3, 4, 5), (4, 5, 6),
        (0, 1, 2), (0, 3, 1),
    ]
    bm_verts = [bm.verts.new(co) for co in verts_data]
    bm.verts.ensure_lookup_table()
    for f in faces_data:
        try:
            bm.faces.new([bm_verts[i] for i in f])
        except Exception:
            pass

    mesh = bpy.data.meshes.new("Mesh_Sword")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Sword", mesh)
    obj.location = (0.08, 0.05, 1.30)   # hidden along cloak lining
    obj.rotation_euler = (0, 0, math.radians(10))
    smooth_shade(obj)
    obj.data.materials.append(mat_sword)
    collections["accessories"].objects.link(obj)

    # Guard (cross-piece)
    guard = create_cube("SwordGuard", (0.08, 0.05, 1.30), size=0.04)
    guard.scale = (2.0, 0.3, 0.15)
    apply_scale(guard)
    guard.data.materials.append(mat_sword)
    link_to_collection(guard, collections["accessories"])

    # Hide sword initially (concealed)
    obj.hide_viewport = False   # shown; rig control will drive visibility
    obj.hide_render = False

    return obj, guard


def build_basket(collections, mat_basket, mat_sword):
    """Wicker basket with hidden sword compartment motif."""
    basket = create_cylinder(
        "Basket", (-0.42, 0, 1.38), radius=0.08, depth=0.10, verts=14
    )
    smooth_shade(basket)
    basket.data.materials.append(mat_basket)
    link_to_collection(basket, collections["accessories"])

    # Basket handle
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.025)
    for v in bm.verts:
        v.co.y *= 0.3
        v.co.z *= 1.8
    mesh = bpy.data.meshes.new("Mesh_BasketHandle")
    bm.to_mesh(mesh)
    bm.free()

    handle = bpy.data.objects.new("BasketHandle", mesh)
    handle.location = (-0.42, 0, 1.465)
    smooth_shade(handle)
    handle.data.materials.append(mat_basket)
    collections["accessories"].objects.link(handle)

    return basket, handle


def build_wolf_armor(collections, mat_wolf):
    """Stylised wolf-skull shoulder pauldron hinting at the antagonist."""
    deselect_all()
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=0.09)

    # Flatten into pauldron shape
    for v in bm.verts:
        v.co.z *= 0.55
        v.co.y *= 0.6
        # Ear spikes for wolf motif
        if v.co.z > 0.04 and abs(v.co.x) < 0.02:
            v.co.z += 0.05
            v.co.z *= 1.4

    mesh = bpy.data.meshes.new("Mesh_WolfArmor")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("WolfPauldron", mesh)
    obj.location = (0.22, 0, 1.46)
    smooth_shade(obj)
    add_subsurf(obj, levels=1)
    obj.data.materials.append(mat_wolf)
    collections["accessories"].objects.link(obj)
    return obj


# ---------------------------------------------------------------------------
# Armature / Rig
# ---------------------------------------------------------------------------

BONE_POSITIONS = {
    # (head, tail)
    "Root":           ((0.0,  0.0, 0.00), (0.0,  0.0, 0.10)),
    "Spine_01":       ((0.0,  0.0, 1.08), (0.0,  0.0, 1.22)),
    "Spine_02":       ((0.0,  0.0, 1.22), (0.0,  0.0, 1.36)),
    "Spine_03":       ((0.0,  0.0, 1.36), (0.0,  0.0, 1.50)),
    "Chest":          ((0.0,  0.0, 1.50), (0.0,  0.0, 1.58)),
    "Neck":           ((0.0,  0.0, 1.58), (0.0,  0.0, 1.68)),
    "Head":           ((0.0,  0.0, 1.68), (0.0,  0.0, 1.82)),
    # Left arm
    "Shoulder_L":     ((0.05, 0.0, 1.56), (0.12, 0.0, 1.56)),
    "UpperArm_L":     ((0.12, 0.0, 1.54), (0.32, 0.0, 1.46)),
    "LowerArm_L":     ((0.32, 0.0, 1.46), (0.52, 0.0, 1.42)),
    "Hand_L":         ((0.52, 0.0, 1.42), (0.60, 0.0, 1.40)),
    # Right arm (mirrored)
    "Shoulder_R":     ((-0.05, 0.0, 1.56), (-0.12, 0.0, 1.56)),
    "UpperArm_R":     ((-0.12, 0.0, 1.54), (-0.32, 0.0, 1.46)),
    "LowerArm_R":     ((-0.32, 0.0, 1.46), (-0.52, 0.0, 1.42)),
    "Hand_R":         ((-0.52, 0.0, 1.42), (-0.60, 0.0, 1.40)),
    # IK targets for arms
    "IK_Hand_L":      ((0.60, -0.08, 1.40), (0.60, -0.14, 1.40)),
    "IK_Hand_R":      ((-0.60, -0.08, 1.40), (-0.60, -0.14, 1.40)),
    # Left leg
    "Hip_L":          ((0.07, 0.0, 1.08), (0.09, 0.0, 0.95)),
    "Thigh_L":        ((0.09, 0.0, 1.08), (0.09, 0.0, 0.75)),
    "Shin_L":         ((0.09, 0.0, 0.75), (0.09, 0.0, 0.59)),
    "Foot_L":         ((0.09, 0.0, 0.59), (0.09, 0.08, 0.55)),
    "Toe_L":          ((0.09, 0.08, 0.55), (0.09, 0.14, 0.54)),
    # Right leg
    "Hip_R":          ((-0.07, 0.0, 1.08), (-0.09, 0.0, 0.95)),
    "Thigh_R":        ((-0.09, 0.0, 1.08), (-0.09, 0.0, 0.75)),
    "Shin_R":         ((-0.09, 0.0, 0.75), (-0.09, 0.0, 0.59)),
    "Foot_R":         ((-0.09, 0.0, 0.59), (-0.09, 0.08, 0.55)),
    "Toe_R":          ((-0.09, 0.08, 0.55), (-0.09, 0.14, 0.54)),
    # IK targets for legs
    "IK_Foot_L":      ((0.09, 0.0, 0.02), (0.09, -0.06, 0.02)),
    "IK_Foot_R":      ((-0.09, 0.0, 0.02), (-0.09, -0.06, 0.02)),
    # Sword control bone — drives sword visibility / deployment
    "Sword_Deploy":   ((0.08, 0.05, 1.28), (0.08, 0.05, 1.60)),
}

BONE_PARENTS = {
    "Spine_01":   "Root",
    "Spine_02":   "Spine_01",
    "Spine_03":   "Spine_02",
    "Chest":      "Spine_03",
    "Neck":       "Chest",
    "Head":       "Neck",
    "Shoulder_L": "Chest",
    "UpperArm_L": "Shoulder_L",
    "LowerArm_L": "UpperArm_L",
    "Hand_L":     "LowerArm_L",
    "Shoulder_R": "Chest",
    "UpperArm_R": "Shoulder_R",
    "LowerArm_R": "UpperArm_R",
    "Hand_R":     "LowerArm_R",
    "Hip_L":      "Spine_01",
    "Thigh_L":    "Hip_L",
    "Shin_L":     "Thigh_L",
    "Foot_L":     "Shin_L",
    "Toe_L":      "Foot_L",
    "Hip_R":      "Spine_01",
    "Thigh_R":    "Hip_R",
    "Shin_R":     "Thigh_R",
    "Foot_R":     "Shin_R",
    "Toe_R":      "Foot_R",
    "Sword_Deploy": "Chest",
}

# IK constraint definitions: (bone, subtarget, chain_count)
IK_CONSTRAINTS = [
    ("LowerArm_L", "IK_Hand_L", 2),
    ("LowerArm_R", "IK_Hand_R", 2),
    ("Shin_L",     "IK_Foot_L", 2),
    ("Shin_R",     "IK_Foot_R", 2),
]


def build_armature(collections):
    """Create the full character armature with IK controls."""
    deselect_all()
    arm_data = bpy.data.armatures.new("Armature_LittleRed")
    arm_data.display_type = "OCTAHEDRAL"
    arm_obj = bpy.data.objects.new("Armature_LittleRed", arm_data)
    arm_obj.show_in_front = True
    collections["armature"].objects.link(arm_obj)

    set_active(arm_obj)
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = arm_data.edit_bones

    created = {}
    for bname, (head, tail) in BONE_POSITIONS.items():
        eb = edit_bones.new(bname)
        eb.head = Vector(head)
        eb.tail = Vector(tail)
        created[bname] = eb

    # Set parents
    for child, parent in BONE_PARENTS.items():
        if child in created and parent in created:
            created[child].parent = created[parent]

    # Mark IK target bones as non-deforming
    for bname in ("IK_Hand_L", "IK_Hand_R", "IK_Foot_L", "IK_Foot_R", "Sword_Deploy"):
        if bname in created:
            created[bname].use_deform = False

    bpy.ops.object.mode_set(mode="POSE")
    pose_bones = arm_obj.pose.bones

    # Add IK constraints
    for bone_name, target_name, chain in IK_CONSTRAINTS:
        if bone_name in pose_bones:
            pb = pose_bones[bone_name]
            ik = pb.constraints.new("IK")
            ik.target = arm_obj
            ik.subtarget = target_name
            ik.chain_count = chain

    # Custom bone shapes for clarity — use simple visual indicators
    # (octahedra already default; a sphere for IK targets would need custom obj)
    for bone_name in ("IK_Hand_L", "IK_Hand_R", "IK_Foot_L", "IK_Foot_R"):
        if bone_name in pose_bones:
            pose_bones[bone_name].custom_shape_scale_xyz = (0.5, 0.5, 0.5)

    # Sword Deploy bone — custom scale to make it prominent
    if "Sword_Deploy" in pose_bones:
        pose_bones["Sword_Deploy"].custom_shape_scale_xyz = (1.5, 1.5, 1.5)
        pose_bones["Sword_Deploy"].bone_group_index = -1

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def add_armature_modifiers(arm_obj, mesh_objects):
    """Add armature modifier to every mesh and auto-weight paint."""
    deselect_all()
    for obj in mesh_objects:
        if obj is None:
            continue
        obj.select_set(True)

    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    except RuntimeError:
        # Fallback: parent with empty groups then add modifier manually
        for obj in mesh_objects:
            if obj is None:
                continue
            if obj.modifiers.get("Armature") is None:
                mod = obj.modifiers.new("Armature", "ARMATURE")
                mod.object = arm_obj
            obj.parent = arm_obj

    deselect_all()


# ---------------------------------------------------------------------------
# Control shapes (custom bone shapes)
# ---------------------------------------------------------------------------

def build_control_shapes(collections):
    """Create simple mesh objects used as custom bone shape visuals."""
    shapes = {}

    # Circle widget for IK handles
    deselect_all()
    bpy.ops.mesh.primitive_circle_add(vertices=16, radius=0.08, fill_type="NOTHING")
    circle = bpy.context.active_object
    circle.name = "WGT_Circle"
    link_to_collection(circle, collections["controls"])
    circle.hide_viewport = True
    shapes["circle"] = circle

    # Arrow widget for sword deploy control
    deselect_all()
    bpy.ops.mesh.primitive_arrow_add() if hasattr(bpy.ops.mesh, "primitive_arrow_add") else None
    # Fall back to a cone
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.06, radius2=0.0, depth=0.14)
    cone = bpy.context.active_object
    cone.name = "WGT_SwordDeploy"
    link_to_collection(cone, collections["controls"])
    cone.hide_viewport = True
    shapes["sword"] = cone

    return shapes


def assign_control_shapes(arm_obj, shapes):
    """Assign widget meshes to specific pose bones."""
    deselect_all()
    set_active(arm_obj)
    bpy.ops.object.mode_set(mode="POSE")
    pb = arm_obj.pose.bones

    for bone_name in ("IK_Hand_L", "IK_Hand_R", "IK_Foot_L", "IK_Foot_R"):
        if bone_name in pb and shapes.get("circle"):
            pb[bone_name].custom_shape = shapes["circle"]

    if "Sword_Deploy" in pb and shapes.get("sword"):
        pb["Sword_Deploy"].custom_shape = shapes["sword"]

    bpy.ops.object.mode_set(mode="OBJECT")


# ---------------------------------------------------------------------------
# Sword visibility driver
# ---------------------------------------------------------------------------

def add_sword_driver(arm_obj, sword_obj, guard_obj):
    """
    Drive the sword's Z scale from the Sword_Deploy bone's Y rotation.
    When the bone is rotated 90 degrees the sword is fully revealed.
    """
    for driven_obj in (sword_obj, guard_obj):
        if driven_obj is None:
            continue
        driven_obj.driver_remove("scale", 2)
        fcurve = driven_obj.driver_add("scale", 2)
        drv = fcurve.driver
        drv.type = "SCRIPTED"

        var = drv.variables.new()
        var.name = "deploy"
        var.type = "SINGLE_PROP"
        target = var.targets[0]
        target.id_type = "OBJECT"
        target.id = arm_obj
        target.data_path = 'pose.bones["Sword_Deploy"].rotation_euler[1]'

        # Scale 0 → 1 as bone rotates 0 → π/2
        drv.expression = "min(1.0, max(0.0, deploy / (3.14159 * 0.5)))"


# ---------------------------------------------------------------------------
# Idle pose
# ---------------------------------------------------------------------------

def set_idle_pose(arm_obj):
    """Apply a subtle, relaxed idle stance with slight hip tilt."""
    deselect_all()
    set_active(arm_obj)
    bpy.ops.object.mode_set(mode="POSE")
    pb = arm_obj.pose.bones

    def set_rot(name, xyz_deg):
        if name in pb:
            pb[name].rotation_mode = "XYZ"
            pb[name].rotation_euler = tuple(math.radians(a) for a in xyz_deg)

    # Spine gentle lean forward
    set_rot("Spine_02",    (3,  0,  0))
    set_rot("Spine_03",    (4,  0,  0))
    set_rot("Chest",       (2,  0,  0))

    # Head tilted slightly
    set_rot("Head",        (-5, 0,  3))

    # Arms relaxed at sides (slight outward rotation)
    set_rot("UpperArm_L",  (0, -10, -5))
    set_rot("UpperArm_R",  (0,  10,  5))
    set_rot("LowerArm_L",  (0, -8,  0))
    set_rot("LowerArm_R",  (0,  8,  0))

    # Hip tilt for weight-shift
    set_rot("Hip_L",       (0,  0, -3))
    set_rot("Hip_R",       (0,  0,  3))

    # Slight knee bend
    set_rot("Shin_L",      (-5, 0,  0))
    set_rot("Shin_R",      (-5, 0,  0))

    bpy.ops.object.mode_set(mode="OBJECT")


# ---------------------------------------------------------------------------
# Turntable animation
# ---------------------------------------------------------------------------

def build_turntable(root_obj, frame_start=1, frame_end=120):
    """Rotate root_obj 360 degrees over frame_start→frame_end."""
    root_obj.rotation_mode = "XYZ"

    root_obj.rotation_euler = (0, 0, 0)
    root_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=frame_start)

    root_obj.rotation_euler = (0, 0, math.radians(360))
    root_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=frame_end)

    bpy.context.scene.frame_start = frame_start
    bpy.context.scene.frame_end = frame_end
    bpy.context.scene.render.fps = 24

    # Set linear interpolation on both keyframes for constant speed
    if root_obj.animation_data and root_obj.animation_data.action:
        for fc in root_obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


# ---------------------------------------------------------------------------
# Scene lighting
# ---------------------------------------------------------------------------

def setup_lighting():
    """Rim light + key light for anime-style preview."""
    # Key light
    bpy.ops.object.light_add(type="AREA", location=(1.5, -1.5, 2.5))
    key = bpy.context.active_object
    key.name = "Light_Key"
    key.data.energy = 800
    key.data.size = 1.5
    key.rotation_euler = (math.radians(50), 0, math.radians(30))

    # Rim light (back-right, blue tint)
    bpy.ops.object.light_add(type="AREA", location=(-1.2, 1.2, 2.0))
    rim = bpy.context.active_object
    rim.name = "Light_Rim"
    rim.data.energy = 400
    rim.data.color = (0.6, 0.7, 1.0)
    rim.data.size = 0.8
    rim.rotation_euler = (math.radians(-40), 0, math.radians(-140))

    # Fill light (soft, low intensity)
    bpy.ops.object.light_add(type="AREA", location=(0, -2.0, 1.2))
    fill = bpy.context.active_object
    fill.name = "Light_Fill"
    fill.data.energy = 150
    fill.data.size = 3.0

    # Camera for turntable
    bpy.ops.object.camera_add(location=(0, -2.2, 1.4))
    cam = bpy.context.active_object
    cam.name = "Camera_Main"
    cam.rotation_euler = (math.radians(78), 0, 0)
    bpy.context.scene.camera = cam


# ---------------------------------------------------------------------------
# Master build function
# ---------------------------------------------------------------------------

def build_scene():
    print("=== Little Red Riding Hood — Build Start ===")

    clear_scene()
    collections = build_collections()

    # --- Materials ---
    print("  Building materials …")
    mat_skin   = make_material_skin()
    mat_cloak  = make_material_cloak()
    mat_hair   = make_material_hair()
    mat_tunic  = make_material_tunic()
    mat_boots  = make_material_boots()
    mat_sword  = make_material_sword()
    mat_wolf   = make_material_wolf_armor()
    mat_eye    = make_material_eye()
    mat_basket = make_material_basket()

    # --- Body ---
    print("  Building body meshes …")
    head   = build_head(collections, mat_skin, mat_eye)
    neck   = build_neck(collections, mat_skin)
    body   = build_body(collections, mat_skin, mat_tunic)
    arms   = build_arms(collections, mat_skin)
    legs   = build_legs(collections, mat_skin)

    # --- Hair ---
    print("  Building hair …")
    hair   = build_hair(collections, mat_hair)

    # --- Clothing ---
    print("  Building clothing …")
    cloak, hood = build_cloak(collections, mat_cloak)
    tunic       = build_tunic(collections, mat_tunic)
    boots       = build_boots(collections, mat_boots)
    gloves      = build_gloves(collections, mat_boots)

    # --- Accessories ---
    print("  Building accessories …")
    sword, guard = build_sword(collections, mat_sword)
    basket, handle = build_basket(collections, mat_basket, mat_sword)
    wolf_pauldron  = build_wolf_armor(collections, mat_wolf)

    # --- Armature ---
    print("  Building armature …")
    arm_obj = build_armature(collections)

    # --- Control shapes ---
    print("  Building rig control shapes …")
    shapes = build_control_shapes(collections)
    assign_control_shapes(arm_obj, shapes)

    # --- Bind meshes to armature ---
    print("  Binding meshes to armature …")
    all_meshes = (
        [head, neck, body, hair, cloak, hood, tunic, wolf_pauldron,
         sword, guard, basket, handle]
        + arms + legs + boots + gloves
    )
    add_armature_modifiers(arm_obj, all_meshes)

    # --- Sword driver ---
    print("  Setting up sword reveal driver …")
    add_sword_driver(arm_obj, sword, guard)

    # --- Idle pose ---
    print("  Applying idle pose …")
    set_idle_pose(arm_obj)

    # --- Turntable animation on armature ---
    print("  Creating turntable animation …")
    build_turntable(arm_obj, frame_start=1, frame_end=120)

    # --- Lighting & Camera ---
    print("  Setting up lighting and camera …")
    setup_lighting()

    # --- Final viewport shading ---
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.type = "MATERIAL"

    # Save the result
    blend_path = bpy.data.filepath
    if not blend_path:
        blend_path = "/tmp/little_red_riding_hood.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

    print(f"=== Build Complete — saved to: {blend_path} ===")
    print()
    print("Scene collections:")
    for col in bpy.data.collections:
        print(f"  {col.name}")
    print()
    print("Mesh objects:")
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            print(f"  {obj.name}")
    print()
    print("Armature objects:")
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            print(f"  {obj.name}")
    print()
    print("Materials:")
    for mat in bpy.data.materials:
        print(f"  {mat.name}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    build_scene()
