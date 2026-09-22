"""Jetson 端：ODIN 重定位、点云适配、地图服务和 Nav2；不启动 RViz 或底盘通信。"""
from pathlib import Path
import math
import tempfile
import yaml
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, RegisterEventHandler, EmitEvent, TimerAction
from launch.event_handlers import OnShutdown, OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def setup(context):
    def value(name):
        return LaunchConfiguration(name).perform(context)

    def existing(name):
        path = Path(value(name)).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f'{name} 文件不存在：{path}')
        return str(path)

    def transform(name):
        values = yaml.safe_load(value(name))
        if not isinstance(values, list) or len(values) != 6:
            raise ValueError(f'{name} 必须是 [x, y, z, roll, pitch, yaw] 六个实测数值')
        numbers = [float(x) for x in values]
        if not all(math.isfinite(x) for x in numbers):
            raise ValueError(f'{name} 不允许空值或无穷值')
        return numbers

    map_file = existing('map')
    adapter_config = existing('adapter_params')
    nav_params = existing('params_file')
    # 安装外参由参数提供；地图变换采用用户确认的实验室默认值，也可显式覆盖。
    calibration = {'base_to_imu': transform('base_to_imu'), 'map_from_odin': transform('map_from_odin')}
    nav_share = Path(get_package_share_directory('nav2_bringup'))
    model = Path(get_package_share_directory('explorer_description')) / 'urdf/robot.urdf.xacro'
    robot_description = xacro.process_file(str(model)).toxml()
    actions = []
    if value('start_driver') == 'true':
        vendor_share = Path(get_package_share_directory('odin_ros_driver'))
        source = value('driver_config') or str(vendor_share / 'config/control_command.yaml')
        with open(source, encoding='utf-8') as stream:
            driver_config = yaml.safe_load(stream)
        keys = driver_config['register_keys']
        odin_map = existing('odin_map')
        keys.update(custom_map_mode=2, relocalization_map_abs_path=odin_map,
                    sendodom=1, senddtof=1, send_odom_baselink_tf=1,
                    tf_extra_publish_rate=0)
        # 保留用户已验证的 use_host_ros_time，不擅自切换设备时间模式。
        # 厂商读取的是普通 YAML，不是 ROS 参数文件。生成本次启动副本，不改厂商原文件。
        with tempfile.NamedTemporaryFile(mode='w', prefix='odin_navigation_', suffix='.yaml',
                                         encoding='utf-8', delete=False) as stream:
            yaml.safe_dump(driver_config, stream, allow_unicode=True)
            runtime_config = Path(stream.name)

        def cleanup(_context, *args, **kwargs):
            runtime_config.unlink(missing_ok=True)
            return []

        actions.append(RegisterEventHandler(OnShutdown(on_shutdown=[OpaqueFunction(function=cleanup)])))
        driver = Node(package='odin_ros_driver', executable='host_sdk_sample', name='host_sdk_sample',
                      output='screen', parameters=[{'config_file': str(runtime_config)}],
                      remappings=[('/tf', '/odin_vendor/tf'), ('/tf_static', '/odin_vendor/tf_static')])
        actions.extend([RegisterEventHandler(OnProcessExit(target_action=driver, on_exit=[
            EmitEvent(event=Shutdown(reason='ODIN 驱动已退出'))])), driver])

    adapter = Node(package='explorer_odin', executable='odin_nav_adapter', name='odin_nav_adapter',
                   output='screen', parameters=[adapter_config, calibration, {'use_sim_time': False}])
    actions.extend([
        RegisterEventHandler(OnProcessExit(target_action=adapter, on_exit=[
            EmitEvent(event=Shutdown(reason='导航适配节点已退出'))])),
        adapter,
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description, 'use_sim_time': False}]),
        # 下位机和轮反馈未接入，关节仅用于显示，不作为里程计来源。
        Node(package='joint_state_publisher', executable='joint_state_publisher',
             parameters=[{'robot_description': robot_description, 'use_sim_time': False}]),
        Node(package='nav2_map_server', executable='map_server', name='map_server', output='screen',
             parameters=[nav_params, {'yaml_filename': map_file, 'use_sim_time': False}]),
        # 等服务端完成 DDS 发现后再配置地图，避免 Humble 首个服务响应发现竞争。
        TimerAction(period=2.0, actions=[
            Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                 name='lifecycle_manager_localization', output='screen',
                 parameters=[{'autostart': True, 'use_sim_time': False, 'node_names': ['map_server']}])]),
        # 仅加载导航，避免 Nav2 默认定位入口另起 AMCL 并争用 map→odom。
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(nav_share / 'launch/navigation_launch.py')),
            launch_arguments={'params_file': nav_params, 'use_sim_time': 'false',
                              'autostart': 'true', 'use_composition': 'False'}.items()),
    ])
    return actions


def generate_launch_description():
    nav = Path(get_package_share_directory('explorer_navigation'))
    odin = Path(get_package_share_directory('explorer_odin'))
    return LaunchDescription([
        DeclareLaunchArgument('map', description='Jetson 上二维地图 YAML 的绝对路径'),
        DeclareLaunchArgument('odin_map', default_value='', description='与二维地图对应的 ODIN BIN 地图绝对路径'),
        DeclareLaunchArgument('base_to_imu', description='IMU 在车体 base_link 中的实测位姿 [x,y,z,roll,pitch,yaw]'),
        # 按用户红框位置修正：在原 (0, 4.6) 基础上向地图 +X 移 0.95 m、+Y 移 0.45 m。
        # 保持原 -90° 朝向；用于 lab_02.bin 与 lab_01_edit 的当前人工对齐。
        # 此值是当前采用的人工对齐关系，不代表已完成点云精确配准。
        DeclareLaunchArgument('map_from_odin', default_value='[0.95,5.05,0.0,0.0,0.0,-1.5708]',
                              description='ODIN 地图原点在二维地图坐标系中的位姿；默认仅适用于当前实验室地图对'),
        DeclareLaunchArgument('start_driver', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('driver_config', default_value='', description='厂商普通 YAML 配置；默认用厂商包内配置'),
        DeclareLaunchArgument('adapter_params', default_value=str(odin / 'config/nav_adapter.yaml')),
        DeclareLaunchArgument('params_file', default_value=str(nav / 'config/nav2_real.yaml')),
        OpaqueFunction(function=setup),
    ])
