"""Competition drawing reconstruction on a flat physical floor.

The printed course is visual-only; white and black regions share the existing
ground contact. It does not define route order, official start or surveyed truth.
"""

from pathlib import Path
import math

import yaml

from .contact_world import element, numbers


def add_competition_course(world, share, overview=False):
    share = Path(share)
    config = yaml.safe_load((share/'config/competition_course.yaml').read_text())
    # Specify the light range and ambient illumination for reproducible rendering.
    light = world.find("light[@name='sun']")
    attenuation = element(light, 'attenuation')
    for key, value in (('range', 1000), ('constant', 1), ('linear', 0), ('quadratic', 0)):
        element(attenuation, key, value)
    element(light, 'cast_shadows', 'true')
    scene = element(world, 'scene')
    element(scene, 'ambient', '0.4 0.4 0.4 1')
    element(scene, 'background', '0.7 0.7 0.7 1')
    floor_visual = world.find("model[@name='floor']/link/visual")
    material = element(floor_visual, 'material')
    element(material, 'ambient', '0.25 0.25 0.25 1')
    element(material, 'diffuse', '0.25 0.25 0.25 1')
    model = element(world, 'model', name='competition_course')
    element(model, 'static', 'true')
    element(model, 'pose', numbers([0, 0, config['visual_z_m'], 0, 0, 0]))
    body = element(model, 'link', name='printed_board')
    visual = element(body, 'visual', name='course_print')
    element(visual, 'cast_shadows', 'false')
    mesh = element(element(visual, 'geometry'), 'mesh')
    element(mesh, 'uri', (share/'meshes/competition_course/course.dae').resolve().as_uri())
    # Preserve the release height inferred from the lowest vehicle collision.
    vehicle_pose = world.find("model[@name='odin_racer']/pose")
    values = [float(v) for v in vehicle_pose.text.split()]
    values[0], values[1], values[5] = (config[k] for k in ('spawn_x_m', 'spawn_y_m', 'spawn_yaw_rad'))
    vehicle_pose.text = numbers(values)
    world.set('name', 'competition_reference')
    gui = element(world, 'gui')
    camera = element(gui, 'camera', name='course_view')
    element(camera, 'pose', '0 -2.2 2.5 0 0.8 1.570796326794897')
    element(camera, 'view_controller', 'orbit')
    if overview:
        # Optional instrumentation camera, not part of Odin and never an algorithm input.
        observer = element(world, 'model', name='course_overview')
        element(observer, 'static', 'true')
        element(observer, 'pose', numbers([0, 0, 3, 0, math.pi/2, math.pi/2]))
        link = element(observer, 'link', name='camera')
        sensor = element(link, 'sensor', name='overview', type='camera')
        element(sensor, 'always_on', 'true')
        element(sensor, 'update_rate', 2)
        camera = element(sensor, 'camera')
        element(camera, 'horizontal_fov', 2*math.atan(1.1/3))
        image = element(camera, 'image')
        element(image, 'width', 1000)
        element(image, 'height', 750)
        element(image, 'format', 'R8G8B8')
        clip = element(camera, 'clip')
        element(clip, 'near', .05)
        element(clip, 'far', 10)
        plugin = element(sensor, 'plugin', name='course_overview', filename='libgazebo_ros_camera.so')
        ros = element(plugin, 'ros')
        element(ros, 'namespace', '/sim/course')
        element(ros, 'remapping', 'overview/image_raw:=/sim/course/overview/image')
        element(ros, 'remapping', 'overview/camera_info:=/sim/course/overview/camera_info')
        element(plugin, 'camera_name', 'overview')
        element(plugin, 'frame_name', 'course_overview_optical')
    return config
