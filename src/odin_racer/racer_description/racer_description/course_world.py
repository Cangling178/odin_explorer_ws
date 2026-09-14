"""Competition drawing reconstruction on a flat physical floor.

The printed course is visual-only; white and black regions share the existing
ground contact. It does not define route order, official start or surveyed truth.
"""

from pathlib import Path
import math

import yaml

from .contact_world import element, numbers


def add_competition_course(world, share, overview=False, parameters=None, resource_directory=None):
    share = Path(share)
    config = yaml.safe_load((share/'config/competition_course.yaml').read_text())
    supplied = parameters or {}
    spawn_keys = {'spawn_x': 'spawn_x_m', 'spawn_y': 'spawn_y_m',
                  'spawn_yaw': 'spawn_yaw_rad'}
    if set(supplied)-(set(spawn_keys) | {'scale', 'line_width'}):
        raise ValueError('Unknown competition course parameter')
    scale = supplied.get('scale', 2.0)
    if not isinstance(scale, (float, int)) or not math.isfinite(scale) or scale <= 0:
        raise ValueError('Competition scale must be finite and positive')
    line_width = supplied.get('line_width', config['estimated_top_straight_width_m'])
    if not isinstance(line_width, (float, int)) or not math.isfinite(line_width) or line_width <= 0:
        raise ValueError('Competition line_width must be finite and positive')
    # Scale the printed XY geometry and default map position, never the vehicle.
    for key in ('board_size_m', 'meters_per_pixel', 'track_outer_extent_m'):
        config[key] = [value*scale for value in config[key]]
    for key in ('spawn_x_m', 'spawn_y_m', 'estimated_top_straight_width_m'):
        config[key] *= scale
    config['runtime_scale'] = scale
    config['rendered_line_width_m'] = line_width
    for key, value in supplied.items():
        if key in ('scale', 'line_width'):
            continue
        if not isinstance(value, (float, int)) or not math.isfinite(value):
            raise ValueError('Competition spawn pose must be finite')
        # Explicit spawn overrides are world metres on the scaled map.
        config[spawn_keys[key]] = float(value)
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
    mesh_path = share/'meshes/competition_course/course.dae'
    if scale != 1 or 'line_width' in supplied:
        if resource_directory is None:
            raise ValueError('Scaled competition texture requires a resource directory')
        from .course_texture import fixed_width_mesh
        mesh_path = fixed_width_mesh(mesh_path.parent, resource_directory,
                                     config['board_size_m'], line_width)
    element(mesh, 'uri', mesh_path.resolve().as_uri())
    element(mesh, 'scale', numbers([scale, scale, 1]))
    # Preserve the release height inferred from the lowest vehicle collision.
    vehicle_pose = world.find("model[@name='odin_racer']/pose")
    values = [float(v) for v in vehicle_pose.text.split()]
    values[0], values[1], values[5] = (config[k] for k in ('spawn_x_m', 'spawn_y_m', 'spawn_yaw_rad'))
    vehicle_pose.text = numbers(values)
    world.set('name', 'competition_reference')
    gui = element(world, 'gui')
    camera = element(gui, 'camera', name='course_view')
    element(camera, 'pose', numbers([0, -2.2*scale, 2.5*scale, 0, .8, math.pi/2]))
    element(camera, 'view_controller', 'orbit')
    if overview:
        # Optional instrumentation camera, not part of Odin and never an algorithm input.
        observer = element(world, 'model', name='course_overview')
        element(observer, 'static', 'true')
        element(observer, 'pose', numbers([0, 0, 3*scale, 0, math.pi/2, math.pi/2]))
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


LINE_SCENES = ('line_straight', 'line_arc', 'line_left', 'line_right', 'line_s',
               'line_corner_left', 'line_corner_right')


def line_fixture(kind, parameters=None):
    """Geometry for the renderer and independent evaluator ONLY (metres/radians).

    The visible print continues beyond the evaluator's end region. No reference
    coordinates, scenario identity or end region are published to runtime nodes.
    """
    if kind not in LINE_SCENES:
        raise ValueError('Unknown line test fixture')
    cfg = dict(line_width=.021, radius=.8, straight_length=1.2, s_length=2.,
               s_amplitude=.14, corner_x=.8, exit_length=.7, spawn_x=0., spawn_y=-.035,
               spawn_yaw=-.08, end_radius=.06, corridor_half_width=.23)
    supplied = parameters or {}
    if set(supplied)-set(cfg):
        raise ValueError('Unknown fixture parameter')
    cfg.update(supplied)
    if any(not isinstance(v, (float, int)) or not math.isfinite(v) for v in cfg.values()):
        raise ValueError('Nonfinite fixture parameter')
    if any(cfg[k] <= 0 for k in cfg if k not in ('spawn_x', 'spawn_y', 'spawn_yaw')):
        raise ValueError('Geometry dimensions must be positive')
    if cfg['line_width'] >= .05 or cfg['radius'] < .3:
        raise ValueError('Fixture outside engineering geometry bounds')
    sign = -1 if kind in ('line_right', 'line_corner_right') else 1
    points = []
    def segment(a, b):
        n = max(1, math.ceil(math.dist(a, b)/.006))
        points.extend([[a[0]+(b[0]-a[0])*i/n, a[1]+(b[1]-a[1])*i/n] for i in range(n)])
    if kind == 'line_straight':
        end = [cfg['straight_length'], 0.]
        segment([-.5, 0.], [end[0]+.9, 0.])
        heading = 0.
    elif kind in ('line_arc', 'line_left', 'line_right'):
        r = cfg['radius']
        end_angle = 2.5 if kind == 'line_arc' else 1.5
        end = [r*math.sin(end_angle), sign*r*(1-math.cos(end_angle))]
        points = [[r*math.sin(a), sign*r*(1-math.cos(a))]
                  for a in [-.3+i*(math.pi+.6)/600 for i in range(601)]]
        heading = sign*end_angle
    elif kind == 'line_s':
        length, amplitude = cfg['s_length'], cfg['s_amplitude']
        segment([-.5, 0.], [0., 0.])
        points.extend([[length*i/400, amplitude*(1-math.cos(2*math.pi*i/400))] for i in range(401)])
        segment([length, 0.], [length+.9, 0.])
        end, heading = [length, 0.], 0.
    else:
        x = cfg['corner_x']
        segment([-.5, 0.], [x, 0.])
        segment([x, 0.], [x, sign*(cfg['exit_length']+.9)])
        end, heading = [x, sign*cfg['exit_length']], sign*math.pi/2
    return dict(kind=kind, parameters=cfg, reference=points,
                spawn=[cfg['spawn_x'], cfg['spawn_y'], cfg['spawn_yaw']],
                end=dict(center=end, radius=cfg['end_radius'], yaw=heading),
                conditions='engineering_test_not_official_competition')


def add_line_test_course(world, kind, parameters=None, resource_directory=None):
    fixture = line_fixture(kind, parameters)
    model = element(world, 'model', name='line_test_course')
    element(model, 'static', 'true')
    body = element(model, 'link', name='print')

    def patch(name, x, y, yaw, length, width, z, color):
        visual = element(body, 'visual', name=name)
        element(visual, 'pose', numbers([x, y, z, 0, 0, yaw]))
        element(visual, 'cast_shadows', 'false')
        box = element(element(visual, 'geometry'), 'box')
        element(box, 'size', numbers([length, width, .0001]))
        material = element(visual, 'material')
        element(material, 'ambient', color)
        element(material, 'diffuse', color)

    patch('white_board', 0, 0, 0, 8, 8, .0001, '1 1 1 1')
    triangles = []
    for i, (a, b) in enumerate(zip(fixture['reference'], fixture['reference'][1:])):
        length = math.dist(a, b)
        if length < 1e-9:
            continue
        yaw = math.atan2(b[1]-a[1], b[0]-a[0])
        width = fixture['parameters']['line_width']
        if resource_directory is None:
            patch(f'line_{i}', (a[0]+b[0])/2, (a[1]+b[1])/2,
                  yaw, length*1.08, width, .0002, '0 0 0 1')
        else:
            # Batch the exact same strip top faces into one visual. Hundreds
            # of individual draw calls unnecessarily slow repeated camera tests.
            cx, cy = (a[0]+b[0])/2, (a[1]+b[1])/2
            dx, dy = math.cos(yaw)*length*.54, math.sin(yaw)*length*.54
            nx, ny = -math.sin(yaw)*width/2, math.cos(yaw)*width/2
            vertices = [(cx-dx-nx,cy-dy-ny,.00025), (cx+dx-nx,cy+dy-ny,.00025),
                        (cx+dx+nx,cy+dy+ny,.00025), (cx-dx+nx,cy-dy+ny,.00025)]
            triangles.extend([[vertices[j] for j in indices] for indices in ((0,1,2),(0,2,3))])
    if resource_directory is not None:
        mesh_file = Path(resource_directory)/'line_print.stl'
        lines = ['solid line_print']
        for triangle in triangles:
            lines.extend(['facet normal 0 0 1', 'outer loop'])
            lines.extend('vertex '+numbers(vertex) for vertex in triangle)
            lines.extend(['endloop', 'endfacet'])
        lines.append('endsolid line_print')
        mesh_file.write_text('\n'.join(lines)+'\n')
        visual = element(body, 'visual', name='black_line_print')
        element(visual, 'cast_shadows', 'false')
        mesh = element(element(visual, 'geometry'), 'mesh')
        element(mesh, 'uri', mesh_file.resolve().as_uri())
        material = element(visual, 'material')
        element(material, 'ambient', '0 0 0 1')
        element(material, 'diffuse', '0 0 0 1')
    pose = world.find("model[@name='odin_racer']/pose")
    values = [float(v) for v in pose.text.split()]
    values[0], values[1], values[5] = fixture['spawn']
    pose.text = numbers(values)
    world.set('name', kind)
    return fixture
