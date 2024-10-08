# written: UQ team @ SimCenter  # noqa: INP001, D100

# import functions for Python 2.X support
import sys

if sys.version.startswith('2'):
    range = xrange  # noqa: A001, F821
    string_types = basestring  # noqa: F821
else:
    string_types = str

import json
import os
import platform
import stat
import subprocess
import sys

inputArgs = sys.argv  # noqa: N816

workdir_main = inputArgs[1]
workdir_temp = inputArgs[2]
run_type = inputArgs[3]

# Replace the PATH TO strings with the path to the given executable in your
# computer. The 'darwin' part corresponds to Mac, the 'else' clause corresponds
# to Windows. You only need the path to either Feap or OpenSees depending on
# which one you plan to use for the analysis.

# run on local computer
if run_type == 'runningLocal':
    # MAC
    if sys.platform == 'darwin':
        OpenSees = 'OpenSees'
        surrogate = 'surrogateBuild.py'
        natafExe = 'nataf_gsa'  # noqa: N816
        Feap = 'feappv'
        Dakota = 'dakota'
        plomScript = 'runPLoM.py'  # noqa: N816
        workflow_driver = 'workflow_driver'
        osType = 'Darwin'  # noqa: N816

    # Windows
    else:
        OpenSees = 'OpenSees'
        Feap = 'Feappv41.exe'
        surrogate = 'surrogateBuild.py'
        natafExe = 'nataf_gsa.exe'  # noqa: N816
        Dakota = 'dakota'
        plomScript = 'runPLoM.py'  # noqa: N816
        workflow_driver = 'workflow_driver.bat'
        osType = 'Windows'  # noqa: N816

# Stampede @ DesignSafe, DON'T EDIT
elif run_type == 'runningRemote':
    OpenSees = '/home1/00477/tg457427/bin/OpenSees'
    Feap = '/home1/00477/tg457427/bin/feappv'
    Dakota = 'dakota'
    workflow_driver = 'workflow_driver'
    osType = 'Linux'  # noqa: N816

# change workdir to the templatedir
os.chdir(workdir_temp)
cwd = os.getcwd()  # noqa: PTH109

print(cwd)  # noqa: T201

# open the dakota json file
with open('dakota.json') as data_file:  # noqa: PTH123
    data = json.load(data_file)

uq_data = data['UQ_Method']
fem_data = data['fem']
rnd_data = data['randomVariables']
my_edps = data['EDP']

myScriptDir = os.path.dirname(os.path.realpath(__file__))  # noqa: PTH120, N816
inputFile = 'dakota.json'  # noqa: N816

osType = platform.system()  # noqa: N816
# preprocessorCommand = '"{}/preprocessSimCenterUQ" {} {} {} {}'.format(myScriptDir, inputFile, workflow_driver, run_type, osType)
# subprocess.Popen(preprocessorCommand, shell=True).wait()
# print("DONE RUNNING PREPROCESSOR\n")


# edps = samplingData["edps"]
numResponses = 0  # noqa: N816
responseDescriptors = []  # noqa: N816

for edp in my_edps:
    responseDescriptors.append(edp['name'])
    numResponses += 1  # noqa: SIM113, N816

femProgram = fem_data['program']  # noqa: N816
print(femProgram)  # noqa: T201

if run_type == 'runningLocal':
    os.chmod(workflow_driver, stat.S_IXUSR | stat.S_IRUSR | stat.S_IXOTH)  # noqa: PTH101

# command = Dakota + ' -input dakota.in -output dakota.out -error dakota.err'

# Change permission of workflow driver
st = os.stat(workflow_driver)  # noqa: PTH116
os.chmod(workflow_driver, st.st_mode | stat.S_IEXEC)  # noqa: PTH101

# change dir to the main working dir for the structure
os.chdir('../')

cwd = os.getcwd()  # noqa: PTH109
print(cwd)  # noqa: T201

if run_type == 'runningLocal':
    #    p = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    #    for line in p.stdout:
    #        print(str(line))

    #    dakotaCommand = "dakota -input dakota.in -output dakota.out -error dakota.err"

    """
    LATER, CHANGE THE LOCATION
    """

    if uq_data['uqType'] == 'Train GP Surrogate Model':
        # simCenterUQCommand = 'python "{}/{}" {} {} {}'.format(myScriptDir,surrogate,workdir_main,osType,run_type)
        simCenterUQCommand = '"{}" "{}/{}" "{}" {} {}'.format(  # noqa: N816
            data['python'], myScriptDir, surrogate, workdir_main, osType, run_type
        )
    elif (
        uq_data['uqType'] == 'Sensitivity Analysis'
        or uq_data['uqType'] == 'Forward Propagation'
    ):
        simCenterUQCommand = (  # noqa: N816
            f'"{myScriptDir}/{natafExe}" "{workdir_main}" {osType} {run_type}'
        )
    elif uq_data['uqType'] == 'Train PLoM Model':
        simCenterUQCommand = '"{}" "{}/{}" "{}" {} {}'.format(  # noqa: N816
            data['python'], myScriptDir, plomScript, workdir_main, osType, run_type
        )

    print('running SimCenterUQ: ', simCenterUQCommand)  # noqa: T201

    # subprocess.Popen(simCenterUQCommand, shell=True).wait()

    try:
        result = subprocess.check_output(  # noqa: S602
            simCenterUQCommand, stderr=subprocess.STDOUT, shell=True
        )
        returncode = 0
        print('DONE SUCESS')  # noqa: T201
    except subprocess.CalledProcessError as e:
        result = e.output
        returncode = e.returncode
        print('DONE FAIL')  # noqa: T201
