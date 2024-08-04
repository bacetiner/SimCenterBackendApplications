"""Created on Wed May 26 16:11:36 2021

@author: snaeimi
"""  # noqa: CPY001, D400

import ctypes
import logging
import os
import platform
import sys

import numpy as np
import wntrfr.epanet.toolkit
from pkg_resources import resource_filename

logger = logging.getLogger(__name__)


class EpanetException(Exception):  # noqa: N818, D101
    pass


class ENepanet(wntrfr.epanet.toolkit.ENepanet):  # noqa: D101
    def __init__(  # noqa: ANN204, C901
        self,
        inpfile='',  # noqa: ANN001
        rptfile='',  # noqa: ANN001
        binfile='',  # noqa: ANN001
        changed_epanet=False,  # noqa: ANN001, FBT002
        version=2.2,  # noqa: ANN001
    ):
        if changed_epanet == False or changed_epanet == True:  # noqa: E712, PLR1714
            self.changed_epanet = changed_epanet
        else:
            raise ValueError('changed_epanet must be a boolean value')  # noqa: EM101, TRY003

        if changed_epanet == False:  # noqa: E712
            super().__init__(inpfile, rptfile, binfile, version=version)
        else:
            try:  # noqa: SIM105
                super().__init__(inpfile, rptfile, binfile, version=version)
            except:  # noqa: S110, E722
                pass  # to add robustness for the time when for the WNTR
                # cannot load the umodified DLLs for any reason

            if float(version) != 2.2:  # noqa: PLR2004
                raise ValueError(  # noqa: TRY003
                    'EPANET version must be 2.2 when using the changed version'  # noqa: EM101
                )

            elif float(version) == 2.2:  # noqa: RET506, PLR2004
                libnames = ['epanet22_mod', 'epanet22_win32_mod']
                if '64' in platform.machine():
                    libnames.insert(0, 'epanet22_amd64_mod')
            for lib in libnames:
                try:
                    if os.name in ['nt', 'dos']:  # noqa: PLR6201
                        libepanet = resource_filename(
                            __name__,
                            'Windows/%s.dll' % lib,  # noqa: UP031
                        )
                        self.ENlib = ctypes.windll.LoadLibrary(libepanet)
                    elif sys.platform == 'darwin':
                        libepanet = resource_filename(
                            __name__,
                            'Darwin/lib%s.dylib' % lib,  # noqa: UP031
                        )
                        self.ENlib = ctypes.cdll.LoadLibrary(libepanet)
                    else:
                        libepanet = resource_filename(
                            __name__,
                            'Linux/lib%s.so' % lib,  # noqa: UP031
                        )
                        self.ENlib = ctypes.cdll.LoadLibrary(libepanet)
                    return  # noqa: TRY300
                except Exception as E1:  # noqa: PERF203
                    if lib == libnames[-1]:
                        raise E1  # noqa: TRY201
                finally:
                    if version >= 2.2 and '32' not in lib:  # noqa: PLR2004
                        self._project = ctypes.c_uint64()
                    elif version >= 2.2:  # noqa: PLR2004
                        self._project = ctypes.c_uint32()
                    else:
                        self._project = None

    def ENSetIgnoreFlag(self, ignore_flag=0):  # noqa: ANN001, ANN201, D102, N802, PLR6301
        if abs(ignore_flag - np.round(ignore_flag)) > 0.00001 or ignore_flag < 0:  # noqa: PLR2004
            logger.error(
                'ignore_flag must be int value and bigger than zero'  # noqa: G003
                + str(ignore_flag)
            )
        flag = ctypes.c_int(int(ignore_flag))  # noqa: F841
        # print('++++++++++++++++++++++')
        # self.ENlib.ENEXTENDEDsetignoreflag(flag)
