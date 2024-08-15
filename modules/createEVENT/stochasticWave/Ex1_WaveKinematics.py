#!/usr/bin/env python3  # noqa: EXE001

"""Plot the wave kinematics (elevation, velocity, acceleration) for linear waves
Different locations, times and superposition of frequencies can be used.
"""  # noqa: D205

import matplotlib.pyplot as plt
import numpy as np

# Local
from welib.tools.figure import defaultRC

defaultRC()
from welib.hydro.morison import *  # noqa: E402, F403
from welib.hydro.wavekin import *  # noqa: E402, F403
from welib.hydro.wavekin import elevation2d, kinematics2d, wavenumber  # noqa: E402
from welib.tools.colors import python_colors  # noqa: E402

fig, axes = plt.subplots(2, 2, sharey=False, figsize=(6.4, 4.8))  # (6.4,4.8)
fig.subplots_adjust(
    left=0.10, right=0.95, top=0.91, bottom=0.09, hspace=0.29, wspace=0.46
)
plt.suptitle('Hydro - Wave kinematics')


g = 9.81  # gravity [m/s^2]
h = 30.0  # water depth [m]

# --- (Top Left) Example for one frequency, one point, multiple times
a = 8.1  # wave peak amplitude [m]
x, z = 0, 0  # position where kinematics are evaluated [m]
T = 12.7  # period [s]
eps = 0  # phase shift [rad]
f = 1.0 / T
k = wavenumber(f, h, g)
time = np.arange(0, 2 * T, T / 101)
# Wave kinematics
vel, acc = kinematics2d(a, f, k, eps, h, time, z, x)
eta = elevation2d(a, f, k, eps, time, x)

# Plot
ax = axes[0, 0]
ax.plot(time, eta, label=r'Elevation [m]')
ax.plot(time, vel, label=r'Velocity [m/s]')
ax.plot(time, acc, label=r'Acceleration [m$^2$/s]')
ax.set_xlabel('Time [s]')
ax.set_ylabel('Kinematics')
ax.legend(fontsize=8, loc='lower center')
ax.set_title('One frequency')


# --- (Bottom Left) Example for one frequencies, multiple points(1d array), multiple times
a = np.array(
    [
        3,
    ]
)  # wave peak amplitude [m]
T = np.array([12.0])  # period [s]
eps = np.array([0])  # phase shift [rad]
z = np.linspace(-h, 0, 10)  # position where kinematics are evaluated
x = z * 0
f = 1.0 / T
k = wavenumber(f, h, g)
time = np.linspace(0, 2 * T[0] / 2, 5)
vel, acc = kinematics2d(a, f, k, eps, h, time, z, x)
# eta = elevation2d(a, f, k, eps, time, x)
ax = axes[1, 0]
sT = ['0', 'T/4', 'T/2', '3T/4']  # noqa: N816
for it, t in enumerate(time[:-1]):  # noqa: B007
    ax.plot(
        vel[:, it],
        z,
        ['-', '-', '-', '--'][it],
        c=python_colors(it),
        label=f'vel, t={sT[it]}',
    )
for it, t in enumerate(time[:-1]):  # noqa: B007
    ax.plot(
        acc[:, it],
        z,
        ['o', '.', '.', '.'][it],
        c=python_colors(it),
        label=f'acc, t={sT[it]}',
    )
ax.set_ylabel('Water depth [m]')
ax.set_xlabel('Velocity and acceleration')
ax.legend(fontsize=8, ncol=2, loc='lower center')


# --- (Top Right) Example for multiple frequencies, one point, multiple times
a = np.array([1.0, 3.0, 5.0, 0.5])  # wave peak amplitude [m]
T = np.array([20.0, 12.0, 9.0, 3.0])  # period [s]
eps = np.array([np.pi / 4, 0, np.pi / 2, 0])  # phase shift [rad]
x, z = 0, 0  # position where kinematics are evaluated
f = 1.0 / T
k = wavenumber(f, h, g)
time = np.arange(0, 2 * T[0], T[0] / 101)
vel, acc = kinematics2d(a, f, k, eps, h, time, z, x)
eta = elevation2d(a, f, k, eps, time, x)

# Plot
ax = axes[0, 1]
ax.plot(time, eta, label=r'Elevation [m]')
ax.plot(time, vel, label=r'Velocity [m/s]')
ax.plot(time, acc, label=r'Acceleration [m$^2$/s]')
ax.set_xlabel('Time [s]')
ax.set_ylabel('Kinematics')
ax.legend(fontsize=8, loc='lower center')
ax.tick_params(direction='in')
ax.set_ylim([-8, 8])
ax.set_title('Multiple frequencies')


# --- (Bottom Left) multiple frequencies, multiple points (2d array), multiple times
a = np.array([1.0, 3.0, 5.0, 0.5])  # wave peak amplitude [m]
T = np.array([20.0, 12.0, 9.0, 3.0])  # period [s]
eps = np.array([np.pi / 4, 0, np.pi / 2, 0])  # phase shift [rad]
vz = np.linspace(-h, 0, 2)  # position where kinematics are evaluated
vx = np.linspace(-10, 10, 3)
X, Z = np.meshgrid(vx, vz)
f = 1.0 / T
k = wavenumber(f, h, g)
time = np.arange(0, 2 * T[0], T[0] / 101)
vel, acc = kinematics2d(a, f, k, eps, h, time, Z, X)
# eta = elevation2d(a, f, k, eps, time, x)

# --- Plot
ax = axes[1, 1]
for i, z in enumerate(vz):
    for j, x in enumerate(vx):
        ax.plot(
            time,
            vel[i, j, :],
            ['--', '-', ':'][j],
            c=python_colors(i),
            label=f'z={z:.0f} x={x:.0f}',
        )
ax.set_ylabel('Velocity [m/s]')
ax.set_xlabel('Time [s]')
ax.legend(fontsize=8, loc='lower center', ncol=2)
ax.set_ylim([-8, 8])
ax.tick_params(direction='in')


# fig.savefig('WaveKinematics.png')
# fig.savefig('WaveKinematics.webp')


# plt.show()


if __name__ == '__main__':
    pass

if __name__ == '__test__':
    pass
if __name__ == '__export__':
    # fig.close()
    from welib.tools.repo import export_figs_callback

    export_figs_callback(__file__)
