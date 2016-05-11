# -*- coding: utf-8 -*-

#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import inspect
from itertools import chain

from stevedore.extension import ExtensionManager

from nailgun import errors
from nailgun.extensions import consts
from nailgun.logger import logger

_EXTENSION_MANAGER = None


def on_load_failure(manager, endpoint, exc):
    logger.exception("Failed to load %s extension", endpoint.name)
    raise


def get_all_extensions():
    """Retrieves all available extensions for Nailgun

    :returns: generator of extensions objects
    """
    # NOTE(sbrzeczkowski): in order to not cause circular imports from
    # extensions and not creating instances ExtensionManager on every time
    # this function is called, we use 'global' variable.
    global _EXTENSION_MANAGER

    if _EXTENSION_MANAGER is None:
        _EXTENSION_MANAGER = ExtensionManager(
            on_load_failure_callback=on_load_failure,
            namespace=consts.EXTENSIONS_NAMESPACE)

    return (ext.plugin for ext in _EXTENSION_MANAGER.extensions)


def get_extension(name):
    """Retrieves extension by name

    :param str name: name of the extension
    :returns: extension class
    :raises errors.CannotFindExtension: on non existing extension
    """
    extension = next(
        (ext for ext in get_all_extensions() if ext.name == name), None)

    if extension is not None:
        return extension

    raise errors.CannotFindExtension(
        "Cannot find extension with name '{0}'".format(name))


def callback_wrapper(name, pass_args=None):
    pass_args = pass_args or []

    def decorator(func):
        def wrapper(*args, **kwargs):
            arg_map = inspect.getcallargs(func, *args)
            filtered_args = [arg_map[arg] for arg in pass_args]
            before_func_name = 'before_{}'.format(name)
            after_func_name = 'after_{}'.format(name)

            # Called when a before or after callback doesn't exist for an ext
            def noop(*args, **kwargs):
                pass

            for extension in get_all_extensions():
                before_func = getattr(extension, before_func_name, noop)
                before_func(*filtered_args, **kwargs)

            func(*args, **kwargs)

            for extension in get_all_extensions():
                after_func = getattr(extension, after_func_name, noop)
                after_func(*filtered_args, **kwargs)

        return wrapper
    return decorator


def _get_extension_by_node(call_name, node):
    all_extensions = {ext.name: ext for ext in get_all_extensions()}
    for extension in chain(node.extensions,
                           node.cluster.extensions if node.cluster else []):

        if (extension in all_extensions and
                call_name in all_extensions[extension].provides):
            return all_extensions[extension]

    raise errors.CannotFindExtension("Cannot find extension which provides "
                                     "'{0}' call".format(call_name))


def node_extension_call(call_name, node, *args, **kwargs):
    extension = _get_extension_by_node(call_name, node)
    return getattr(extension, call_name)(node, *args, **kwargs)


def fire_callback_on_node_create(node):
    for extension in get_all_extensions():
        extension.on_node_create(node)


def fire_callback_on_node_update(node):
    for extension in get_all_extensions():
        extension.on_node_update(node)


def fire_callback_on_node_reset(node):
    for extension in get_all_extensions():
        extension.on_node_reset(node)


def fire_callback_on_node_delete(node):
    for extension in get_all_extensions():
        extension.on_node_delete(node)


def fire_callback_on_remove_node_from_cluster(node):
    for extension in get_all_extensions():
        extension.on_remove_node_from_cluster(node)


def fire_callback_on_node_collection_delete(node_ids):
    for extension in get_all_extensions():
        extension.on_node_collection_delete(node_ids)


def fire_callback_on_nodegroup_create(nodegroup):
    for extension in get_all_extensions():
        extension.on_nodegroup_create(nodegroup)


def fire_callback_on_nodegroup_delete(nodegroup):
    for extension in get_all_extensions():
        extension.on_nodegroup_delete(nodegroup)


def fire_callback_on_cluster_create(cluster, data):
    for extension in get_all_extensions():
        extension.on_cluster_create(cluster, data)


def fire_callback_on_cluster_patch_attributes(cluster, public_map):
    for extension in get_all_extensions():
        extension.on_cluster_patch_attributes(cluster, public_map)


def fire_callback_on_cluster_delete(cluster):
    for extension in get_all_extensions():
        extension.on_cluster_delete(cluster)


def fire_callback_on_before_deployment_check(cluster):
    for extension in get_all_extensions():
        extension.on_before_deployment_check(cluster)


def fire_callback_on_before_deployment_serialization(cluster, nodes,
                                                     ignore_customized):
    for extension in get_all_extensions():
        extension.on_before_deployment_serialization(
            cluster, nodes, ignore_customized
        )


def fire_callback_on_before_provisioning_serialization(cluster, nodes,
                                                       ignore_customized):
    for extension in get_all_extensions():
        extension.on_before_provisioning_serialization(
            cluster, nodes, ignore_customized
        )


def _collect_data_pipelines_for_cluster(cluster):
    extensions = set(cluster.extensions)
    return chain.from_iterable(e.data_pipelines for e in get_all_extensions()
                               if e.name in extensions)


def fire_callback_on_deployment_data_serialization(data, cluster, nodes,
                                                   **kwargs):
    for pipeline in _collect_data_pipelines_for_cluster(cluster):
        data = pipeline.process_deployment(data, cluster, nodes, **kwargs)

    return data


def fire_callback_on_provisioning_data_serialization(data, cluster, nodes,
                                                     **kwargs):
    for pipeline in _collect_data_pipelines_for_cluster(cluster):
        data = pipeline.process_provisioning(data, cluster, nodes, **kwargs)

    return data
