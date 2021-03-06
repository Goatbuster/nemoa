# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa.dataset.exports.archive
import nemoa.dataset.exports.image
import nemoa.dataset.exports.text

def filetypes(filetype = None):
    """Get supported dataset export filetypes."""

    type_dict = {}

    # get supported archive filetypes
    archive_types = nemoa.dataset.exports.archive.filetypes()
    for key, val in list(archive_types.items()):
        type_dict[key] = ('archive', val)

    # get supported image filetypes
    image_types = nemoa.dataset.exports.image.filetypes()
    for key, val in list(image_types.items()):
        type_dict[key] = ('image', val)

    # get supported text filetypes
    text_types = nemoa.dataset.exports.text.filetypes()
    for key, val in list(text_types.items()):
        type_dict[key] = ('text', val)

    if not filetype:
        return {key: val[1] for key, val in list(type_dict.items())}
    if filetype in type_dict:
        return type_dict[filetype]

    return False

def save(dataset, path = None, filetype = None, workspace = None,
    base = 'user', **kwargs):
    """Export dataset to file.

    Args:
        dataset (object): nemoa dataset instance
        path (str, optional): path of export file
        filetype (str, optional): filetype of export file
        workspace (str, optional): workspace to use for file export

    Returns:
        Boolean value which is True if file export was successful

    """

    if not nemoa.common.type.isdataset(dataset):
        return nemoa.log('error', """could not export dataset to file:
            dataset is not valid.""")

    # get directory, filename and fileextension
    if isinstance(workspace, str) and not workspace == 'None':
        directory = nemoa.path('datasets',
            workspace = workspace, base = base)
    elif isinstance(path, str):
        directory = nemoa.common.ospath.directory(path)
    else:
        directory = nemoa.common.ospath.directory(dataset.path)
    if isinstance(path, str):
        name = nemoa.common.ospath.basename(path)
    else:
        name = dataset.fullname
    if isinstance(filetype, str):
        fileext = filetype
    elif isinstance(path, str):
        fileext = nemoa.common.ospath.fileext(path)
        if not fileext:
            fileext = nemoa.common.ospath.fileext(dataset.path)
    else:
        fileext = nemoa.common.ospath.fileext(dataset.path)
    path = nemoa.common.ospath.joinpath(directory, name, fileext)

    # get filetype from file extension if not given
    # and test if filetype is supported
    if not filetype: filetype = fileext.lower()
    if not filetype in list(filetypes().keys()):
        return nemoa.log('error', """could not export dataset:
            filetype '%s' is not supported.""" % (filetype))

    # export to file
    mname = filetypes(filetype)[0]
    if mname == 'text':
        return nemoa.dataset.exports.text.save(
            dataset, path, filetype, **kwargs)
    if mname == 'archive':
        return nemoa.dataset.exports.archive.save(
            dataset, path, filetype, **kwargs)
    if mname == 'image':
        return nemoa.dataset.exports.image.save(
            dataset, path, filetype, **kwargs)

    return False

def show(dataset, *args, **kwargs):
    return nemoa.dataset.exports.image.show(dataset, *args, **kwargs)
