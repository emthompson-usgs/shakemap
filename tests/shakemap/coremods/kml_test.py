#!/usr/bin/env python

import os.path
import tempfile
import shutil
import zipfile
import logging
from xml.dom import minidom

import configobj

from shakemap.utils.config import (get_config_paths,
                                   get_configspec,
                                   get_custom_validator,
                                   config_error)
from shakemap.coremods.kml import (create_kmz)
from shakelib.utils.containers import ShakeMapOutputContainer


def test_create_kmz():
    tempdir = tempfile.mkdtemp()
    try:
        homedir = os.path.dirname(os.path.abspath(__file__))
        cfile = os.path.join(homedir, '..', '..', 'data', 'containers',
                             'northridge', 'shake_result.hdf')
        container = ShakeMapOutputContainer.load(cfile)
        install_path, data_path = get_config_paths()

        product_config_file = os.path.join(
            install_path, 'config', 'products.conf')
        spec_file = get_configspec('products')
        validator = get_custom_validator()
        pconfig = configobj.ConfigObj(product_config_file,
                                      configspec=spec_file)
        results = pconfig.validate(validator)
        if not isinstance(results, bool) or not results:
            config_error(pconfig, results)
        oceanfile = pconfig['products']['mapping']['layers']['lowres_oceans']

        logger = logging.getLogger(__name__)
        kmzfile = create_kmz(container, tempdir, oceanfile, logger)
        myzip = zipfile.ZipFile(kmzfile, mode='r')
        kmlstr = myzip.read('shakemap.kml').decode('utf-8')
        root = minidom.parseString(kmlstr)
        document = root.getElementsByTagName('Document')[0]
        folders = document.getElementsByTagName('Folder')
        names = []
        nstations = 0
        nmmi = 0
        for folder in folders:
            name = folder.getElementsByTagName('name')[0].firstChild.data
            names.append(name)
            if name == 'Instrumented Stations':
                nstations = len(folder.getElementsByTagName('Placemark'))
            elif name == 'Macroseismic Stations':
                nmmi = len(folder.getElementsByTagName('Placemark'))
        assert sorted(names) == ['Contours',
                                 'Instrumented Stations',
                                 'Macroseismic Stations']
        assert nstations == 185
        assert nmmi == 977
        myzip.close()

    except Exception as e:
        print(str(e))
        assert 1 == 2
    finally:
        shutil.rmtree(tempdir)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_create_kmz()
