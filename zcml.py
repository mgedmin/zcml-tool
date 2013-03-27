#!/usr/bin/python3
import argparse
import os
import sys
from xml.etree import cElementTree as ET


ZOPE = '{http://namespaces.zope.org/zope}'
CONFIGURE = ZOPE + 'configure'
INCLUDE = ZOPE + 'include'

ZCML = '{http://namespaces.zope.org/zcml}'
CONDITION = ZCML + 'condition'


def parse_xml(filename):
    with open(filename) as f:
        return ET.parse(f)


def resolve_package(package, relative_to):
    if not package:
        return relative_to
    if not package.startswith('.'):
        return package
    while package.startswith('..'):
        package = package[1:]
        relative_to = relative_to.rpartition('.')[0]
    return relative_to + package


def find_package(package):
    assert not package.startswith('.')
    package_init = package.replace('.', '/') + '/__init__.py'
    for dir in sys.path:
        fn = os.path.join(dir, package_init)
        if os.path.exists(fn):
            return os.path.dirname(fn)
    raise ValueError('Could not find package %s' % package)


def resolve(package, filename):
    if not package:
        return filename
    location = find_package(package)
    return os.path.join(location, filename)


def print_zcml_include_tree(package, filename, conditions=(), level=0, seen=None,
                            show_full_filenames=False, show_seen=False):
    if seen is None:
        seen = set()
    prefix = '  ' * level
    if package:
        prefix += package + ':'
    prefix += filename
    if conditions:
        prefix += ' [conditional on %s]' % ' and '.join(conditions)
    try:
        full_filename = resolve(package, filename)
    except ValueError:
        print('%s [not found]' % prefix)
        return
    if show_full_filenames:
        prefix = '  ' * level + full_filename
        if conditions:
            prefix += ' [conditional on %s]' % ' and '.join(conditions)
    if full_filename in seen:
        if show_seen:
            print('%s [seen]' % prefix)
        return
    print(prefix)
    seen.add(full_filename)
    tree = parse_xml(full_filename)
    def walk(node, package, conditions=()):
        if node.tag in (CONFIGURE, INCLUDE):
            condition = node.get(CONDITION)
            if condition:
                conditions += (condition,)
            package = resolve_package(node.get('package'), package)
        if node.tag == INCLUDE:
            filename = node.get('file') or 'configure.zcml'
            print_zcml_include_tree(package, filename, conditions,
                                    level + 1, seen,
                                    show_full_filenames=show_full_filenames,
                                    show_seen=show_seen)
        for child in node:
            walk(child, package, conditions)
    walk(tree.getroot(), package)


def main():
    parser = argparse.ArgumentParser(description="show the ZCML include tree")
    parser.add_argument('filename', nargs='?', default='configure.zcml')
    parser.add_argument('-p', '--package')
    parser.add_argument('--show-seen', action='store_true')
    parser.add_argument('--full-filenames', action='store_true')
    args = parser.parse_args()
    print_zcml_include_tree(args.package, args.filename,
                            show_full_filenames=args.full_filenames,
                            show_seen=args.show_seen)

if __name__ == '__main__':
    main()
