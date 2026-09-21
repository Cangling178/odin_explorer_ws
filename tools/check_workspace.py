#!/usr/bin/env python3
"""Minimal checks for source dependencies, local links and the preview model."""
import ast
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import xacro

ROOT = Path(__file__).resolve().parents[1]


def main():
    packages = {}
    for manifest in sorted((ROOT / 'src').rglob('package.xml')):
        xml = ET.parse(manifest).getroot()
        name = xml.findtext('name')
        if name in packages:
            raise ValueError(f'Duplicate package: {name}')
        packages[name] = manifest.parent
    for name, path in packages.items():
        xml = ET.parse(path / 'package.xml').getroot()
        for element in xml:
            if 'depend' in element.tag:
                dependency = element.text or ''
                if dependency.startswith('explorer_') and dependency not in packages:
                    raise ValueError(f'{name}: missing dependency {dependency}')
        for launch in path.rglob('*.py'):
            ast.parse(launch.read_text(), filename=str(launch))

    roots = [ROOT / 'docs', ROOT / 'hardware', ROOT / 'firmware', ROOT / 'src']
    documents = [*ROOT.glob('*.md'), *(ROOT / 'vendor_ws').glob('*.md')]
    for folder in roots:
        documents.extend(folder.rglob('*.md'))
    for doc in documents:
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', doc.read_text()):
            if '://' in target or target.startswith(('mailto:', '#')):
                continue
            target = target.split('#', 1)[0]
            if target and not (doc.parent / target).exists():
                raise ValueError(f'{doc.relative_to(ROOT)}: broken link {target}')

    model = packages['explorer_description'] / 'urdf/robot.urdf.xacro'
    robot = ET.fromstring(xacro.process_file(str(model)).toxml())
    links = [link.attrib['name'] for link in robot.findall('link')]
    if len(links) != len(set(links)):
        raise ValueError('Duplicate model links')
    parents = {}
    for joint in robot.findall('joint'):
        parent = joint.find('parent').attrib['link']
        child = joint.find('child').attrib['link']
        if parent not in links or child not in links or child in parents:
            raise ValueError(f'Invalid joint: {joint.attrib["name"]}')
        parents[child] = parent
    if set(links) - set(parents) != {'base_link'}:
        raise ValueError('Model must have one base_link root')
    for link in links:
        seen = set()
        while link in parents:
            if link in seen:
                raise ValueError('Cycle in model TF tree')
            seen.add(link)
            link = parents[link]
    for mesh in robot.iter('mesh'):
        uri = mesh.attrib['filename']
        if not uri.startswith('package://'):
            raise ValueError(f'Non-portable mesh: {uri}')
        package, relative = uri[len('package://'):].split('/', 1)
        if package not in packages or not (packages[package] / relative).is_file():
            raise ValueError(f'Missing mesh: {uri}')
    if robot.find('gazebo') is not None or robot.find('ros2_control') is not None:
        raise ValueError('Preview must not contain simulator or actuator plugins')
    print(f'PASS: {len(packages)} packages, {len(documents)} documents, '
          f'{len(links)} model links; dependencies, syntax and meshes valid.')


if __name__ == '__main__':
    main()
