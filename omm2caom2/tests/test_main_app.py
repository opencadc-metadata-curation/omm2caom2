# -*- coding: utf-8 -*-
# ***********************************************************************
# ******************  CANADIAN ASTRONOMY DATA CENTRE  *******************
# *************  CENTRE CANADIEN DE DONNÉES ASTRONOMIQUES  **************
#
#  (c) 2018.                            (c) 2018.
#  Government of Canada                 Gouvernement du Canada
#  National Research Council            Conseil national de recherches
#  Ottawa, Canada, K1A 0R6              Ottawa, Canada, K1A 0R6
#  All rights reserved                  Tous droits réservés
#
#  NRC disclaims any warranties,        Le CNRC dénie toute garantie
#  expressed, implied, or               énoncée, implicite ou légale,
#  statutory, of any kind with          de quelque nature que ce
#  respect to the software,             soit, concernant le logiciel,
#  including without limitation         y compris sans restriction
#  any warranty of merchantability      toute garantie de valeur
#  or fitness for a particular          marchande ou de pertinence
#  purpose. NRC shall not be            pour un usage particulier.
#  liable in any event for any          Le CNRC ne pourra en aucun cas
#  damages, whether direct or           être tenu responsable de tout
#  indirect, special or general,        dommage, direct ou indirect,
#  consequential or incidental,         particulier ou général,
#  arising from the use of the          accessoire ou fortuit, résultant
#  software.  Neither the name          de l'utilisation du logiciel. Ni
#  of the National Research             le nom du Conseil National de
#  Council of Canada nor the            Recherches du Canada ni les noms
#  names of its contributors may        de ses  participants ne peuvent
#  be used to endorse or promote        être utilisés pour approuver ou
#  products derived from this           promouvoir les produits dérivés
#  software without specific prior      de ce logiciel sans autorisation
#  written permission.                  préalable et particulière
#                                       par écrit.
#
#  This file is part of the             Ce fichier fait partie du projet
#  OpenCADC project.                    OpenCADC.
#
#  OpenCADC is free software:           OpenCADC est un logiciel libre ;
#  you can redistribute it and/or       vous pouvez le redistribuer ou le
#  modify it under the terms of         modifier suivant les termes de
#  the GNU Affero General Public        la “GNU Affero General Public
#  License as published by the          License” telle que publiée
#  Free Software Foundation,            par la Free Software Foundation
#  either version 3 of the              : soit la version 3 de cette
#  License, or (at your option)         licence, soit (à votre gré)
#  any later version.                   toute version ultérieure.
#
#  OpenCADC is distributed in the       OpenCADC est distribué
#  hope that it will be useful,         dans l’espoir qu’il vous
#  but WITHOUT ANY WARRANTY;            sera utile, mais SANS AUCUNE
#  without even the implied             GARANTIE : sans même la garantie
#  warranty of MERCHANTABILITY          implicite de COMMERCIALISABILITÉ
#  or FITNESS FOR A PARTICULAR          ni d’ADÉQUATION À UN OBJECTIF
#  PURPOSE.  See the GNU Affero         PARTICULIER. Consultez la Licence
#  General Public License for           Générale Publique GNU Affero
#  more details.                        pour plus de détails.
#
#  You should have received             Vous devriez avoir reçu une
#  a copy of the GNU Affero             copie de la Licence Générale
#  General Public License along         Publique GNU Affero avec
#  with OpenCADC.  If not, see          OpenCADC ; si ce n’est
#  <http://www.gnu.org/licenses/>.      pas le cas, consultez :
#                                       <http://www.gnu.org/licenses/>.
#
#  $Revision: 4 $
#
# ***********************************************************************
#


from omm2caom2 import main_app, APPLICATION
from caom2.diff import get_differences
from caom2pipe import manage_composable as mc

from hashlib import md5
import os
import sys

from mock import patch

TEST_URI = 'ad:OMM/imm_file.fits'

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_DIR = os.path.join(THIS_DIR, 'data')
PLUGIN = os.path.join(os.path.dirname(THIS_DIR), f'{APPLICATION}.py')


def pytest_generate_tests(metafunc):
    files = [os.path.join(TEST_DATA_DIR, name) for name in
             os.listdir(TEST_DATA_DIR) if name.endswith('header')]
    metafunc.parametrize('test_name', files)


def test_main_app(test_name):
    basename = os.path.basename(test_name)
    product_id = basename.split('.fits')[0]
    lineage = _get_lineage(product_id, basename)
    output_file = f'{test_name}.actual.xml'
    local = _get_local(test_name)
    plugin = PLUGIN
    input_file = f'{TEST_DATA_DIR}/in.{product_id}.fits.xml'
    if os.path.exists(input_file):
        input_param = f'--in {input_file}'
    else:
        input_param = f'--observation OMM {product_id}'
    with patch('caom2utils.fits2caom2.CadcDataClient') as data_client_mock:
        data_client_mock.return_value.get_file_info.side_effect = \
            _mock_get_file_info

        sys.argv = \
            (f'{APPLICATION} --no_validate --local {local}  --plugin {plugin} '
             f'--module {plugin} {input_param} -o {output_file} --lineage '
             f'{lineage}').split()
        print(sys.argv)
        main_app.to_caom2()
    obs_path = test_name.replace('.fits.header', '.expected.xml')
    expected = mc.read_obs_from_file(obs_path)
    actual = mc.read_obs_from_file(output_file)
    result = get_differences(expected, actual, 'Observation')
    if result:
        text = '\n'.join([r for r in result])
        msg = f'Differences found in observation {expected.observation_id}' \
              f'\n{text}'
        raise AssertionError(msg)
    # assert False  # cause I want to see logging messages


def _get_local(test_name):
    prev_name = test_name.replace('.fits.header', '_prev.jpg')
    prev_256_name = test_name.replace('.fits.header', '_prev_256.jpg')
    return f'{test_name} {prev_name} {prev_256_name}'


def _get_lineage(product_id, basename):
    return f'{product_id}/ad:OMM/{product_id}.fits.gz'


def _mock_get_file_info(archive, file_id):
    if '_prev' in file_id:
        return {'type': 'image/jpeg',
                'name': file_id}
    else:
        return {'type': 'application/fits',
                'name': file_id}