"""Compute the sound field generated by a sound source.

.. plot::
    :context: reset

    import sfs
    import numpy as np
    import matplotlib.pyplot as plt
    plt.rcParams['figure.figsize'] = 8, 4.5  # inch

    x0 = 1.5, 1, 0
    f = 500  # Hz
    omega = 2 * np.pi * f

    normalization_point = 4 * np.pi
    normalization_line = \\
        np.sqrt(8 * np.pi * omega / sfs.defs.c) * np.exp(1j * np.pi / 4)

    grid = sfs.util.xyz_grid([-2, 3], [-1, 2], 0, spacing=0.02)

    # Grid for vector fields:
    vgrid = sfs.util.xyz_grid([-2, 3], [-1, 2], 0, spacing=0.1)

"""

import itertools
import numpy as np
from scipy import special
from .. import util
from .. import defs


def point(omega, x0, n0, grid, c=None):
    """Sound pressure of a point source.

    Parameters
    ----------
    omega : float
        Frequency of source.
    x0 : (3,) array_like
        Position of source.
    n0 : (3,) array_like
        Normal vector (direction) of source. Only for compatibilty, not used.
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    c : float, optional
        Speed of sound.

    Returns
    -------
    `XyzComponents`
        Sound pressure at positions given by *grid*.

    Notes
    -----
    ::

                      1  e^(-j w/c |x-x0|)
        G(x-x0, w) = --- -----------------
                     4pi      |x-x0|

    Examples
    --------
    .. plot::
        :context: close-figs

        p = sfs.mono.source.point(omega, x0, None, grid)
        sfs.plot.soundfield(p, grid)
        plt.title("Point Source at {} m".format(x0))

    Normalization ...

    .. plot::
        :context: close-figs

        sfs.plot.soundfield(p * normalization_point, grid,
                            colorbar_kwargs=dict(label="p / Pa"))
        plt.title("Point Source at {} m (normalized)".format(x0))

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    grid = util.as_xyz_components(grid)

    r = np.linalg.norm(grid - x0)
    return 1 / (4*np.pi) * np.exp(-1j * k * r) / r


def point_velocity(omega, x0, n0, grid, c=None):
    """Particle velocity of a point source.

    Parameters
    ----------
    omega : float
        Frequency of source.
    x0 : (3,) array_like
        Position of source.
    n0 : (3,) array_like
        Normal vector (direction) of source. Only for compatibilty, not used.
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    c : float, optional
        Speed of sound.

    Returns
    -------
    `XyzComponents`
        Particle velocity at positions given by *grid*.

    Examples
    --------
    The particle velocity can be plotted on top of the sound pressure:

    .. plot::
        :context: close-figs

        v = sfs.mono.source.point_velocity(omega, x0, None, vgrid)
        sfs.plot.soundfield(p * normalization_point, grid)
        sfs.plot.vectors(v * normalization_point, vgrid)
        plt.title("Sound Pressure and Particle Velocity")

    """
    if c is None:
        c = defs.c
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    grid = util.as_xyz_components(grid)
    offset = grid - x0
    r = np.linalg.norm(offset)
    v = point(omega, x0, n0, grid, c=c)
    v *= (1+1j*k*r) / (defs.rho0 * c * 1j*k*r)
    return util.XyzComponents([v * o / r for o in offset])


def point_averaged_intensity(omega, x0, n0, grid, c=None):
    """Velocity of a point source.

    Parameters
    ----------
    omega : float
        Frequency of source.
    x0 : (3,) array_like
        Position of source.
    n0 : (3,) array_like
        Normal vector (direction) of source. Only for compatibilty, not used.
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    c : float, optional
        Speed of sound.

    Returns
    -------
    `XyzComponents`
        Averaged intensity at positions given by *grid*.
    """
    x0 = util.asarray_1d(x0)
    grid = util.as_xyz_components(grid)
    offset = grid - x0
    r = np.linalg.norm(offset)
    i = 1 / (2*defs.rho0 * defs.c)
    return util.XyzComponents([i * o / r**2 for o in offset])


def point_dipole(omega, x0, n0, grid, c=None):
    r"""Point source with dipole characteristics.

    Parameters
    ----------
    omega : float
        Frequency of source.
    x0 : (3,) array_like
        Position of source.
    n0 : (3,) array_like
        Normal vector (direction) of dipole.
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    c : float, optional
        Speed of sound.

    Returns
    -------
    numpy.ndarray
        Sound pressure at positions given by *grid*.

    Notes
    -----
    ::

         d                1   / iw       1    \   (x-x0) n0
        ---- G(x-x0,w) = --- | ----- + ------- | ----------- e^(-i w/c |x-x0|)
        d ns             4pi  \  c     |x-x0| /   |x-x0|^2

    Examples
    --------
    .. plot::
        :context: close-figs

        n0 = 0, 1, 0
        p = sfs.mono.source.point_dipole(omega, x0, n0, grid)
        sfs.plot.soundfield(p, grid)
        plt.title("Dipole Point Source at {} m".format(x0))

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    n0 = util.asarray_1d(n0)
    grid = util.as_xyz_components(grid)

    offset = grid - x0
    r = np.linalg.norm(offset)
    return 1 / (4*np.pi) * (1j * k + 1 / r) * np.inner(offset, n0) / \
        np.power(r, 2) * np.exp(-1j * k * r)


def point_modal(omega, x0, n0, grid, L, N=None, deltan=0, c=None):
    """Point source in a rectangular room using a modal room model.

    Parameters
    ----------
    omega : float
        Frequency of source.
    x0 : (3,) array_like
        Position of source.
    n0 : (3,) array_like
        Normal vector (direction) of source (only required for
        compatibility).
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    L : (3,) array_like
        Dimensionons of the rectangular room.
    N : (3,) array_like or int, optional
        For all three spatial dimensions per dimension maximum order or
        list of orders. A scalar applies to all three dimensions. If no
        order is provided it is approximately determined.
    deltan : float, optional
        Absorption coefficient of the walls.
    c : float, optional
        Speed of sound.

    Returns
    -------
    numpy.ndarray
        Sound pressure at positions given by *grid*.

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    x, y, z = util.as_xyz_components(grid)

    if np.isscalar(N):
        N = N * np.ones(3, dtype=int)

    if N is None:
            N = [None, None, None]

    orders = [0, 0, 0]
    for i in range(3):
        if N[i] is None:
            # compute max order
            orders[i] = range(int(np.ceil(L[i]/np.pi * k) + 1))
        elif np.isscalar(N[i]):
            # use given max order
            orders[i] = range(N[i] + 1)
        else:
            # use given orders
            orders[i] = N[i]

    kmp0 = [((kx + 1j * deltan)**2, np.cos(kx * x) * np.cos(kx * x0[0]))
            for kx in [m * np.pi / L[0] for m in orders[0]]]
    kmp1 = [((ky + 1j * deltan)**2, np.cos(ky * y) * np.cos(ky * x0[1]))
            for ky in [n * np.pi / L[1] for n in orders[1]]]
    kmp2 = [((kz + 1j * deltan)**2, np.cos(kz * z) * np.cos(kz * x0[2]))
            for kz in [l * np.pi / L[2] for l in orders[2]]]
    ksquared = k**2
    p = 0
    for (km0, p0), (km1, p1), (km2, p2) in itertools.product(kmp0, kmp1, kmp2):
        km = km0 + km1 + km2
        p = p + 8 / (ksquared - km) * p0 * p1 * p2
    return p


def point_modal_velocity(omega, x0, n0, grid, L, N=None, deltan=0, c=None):
    """Velocity of point source in a rectangular room using a modal room model.

    Parameters
    ----------
    omega : float
        Frequency of source.
    x0 : (3,) array_like
        Position of source.
    n0 : (3,) array_like
        Normal vector (direction) of source (only required for
        compatibility).
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    L : (3,) array_like
        Dimensionons of the rectangular room.
    N : (3,) array_like or int, optional
        Combination of modal orders in the three-spatial dimensions to
        calculate the sound field for or maximum order for all
        dimensions.  If not given, the maximum modal order is
        approximately determined and the sound field is computed up to
        this maximum order.
    deltan : float, optional
        Absorption coefficient of the walls.
    c : float, optional
        Speed of sound.

    Returns
    -------
    `XyzComponents`
        Particle velocity at positions given by *grid*.

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    x, y, z = util.as_xyz_components(grid)

    if N is None:
        # determine maximum modal order per dimension
        Nx = int(np.ceil(L[0]/np.pi * k))
        Ny = int(np.ceil(L[1]/np.pi * k))
        Nz = int(np.ceil(L[2]/np.pi * k))
        mm = range(Nx)
        nn = range(Ny)
        ll = range(Nz)
    elif np.isscalar(N):
        # compute up to a given order
        mm = range(N)
        nn = range(N)
        ll = range(N)
    else:
        # compute field for one order combination only
        mm = [N[0]]
        nn = [N[1]]
        ll = [N[2]]

    kmp0 = [((kx + 1j * deltan)**2, np.sin(kx * x) * np.cos(kx * x0[0]))
            for kx in [m * np.pi / L[0] for m in mm]]
    kmp1 = [((ky + 1j * deltan)**2, np.sin(ky * y) * np.cos(ky * x0[1]))
            for ky in [n * np.pi / L[1] for n in nn]]
    kmp2 = [((kz + 1j * deltan)**2, np.sin(kz * z) * np.cos(kz * x0[2]))
            for kz in [l * np.pi / L[2] for l in ll]]
    ksquared = k**2
    vx = 0+0j
    vy = 0+0j
    vz = 0+0j
    for (km0, p0), (km1, p1), (km2, p2) in itertools.product(kmp0, kmp1, kmp2):
        km = km0 + km1 + km2
        vx = vx - 8*1j / (ksquared - km) * p0
        vy = vy - 8*1j / (ksquared - km) * p1
        vz = vz - 8*1j / (ksquared - km) * p2
    return util.XyzComponents([vx, vy, vz])


def point_image_sources(omega, x0, n0, grid, L, max_order, coeffs=None,
                        c=None):
    """Point source in a rectangular room using the mirror image source model.

    Parameters
    ----------
    omega : float
        Frequency of source.
    x0 : (3,) array_like
        Position of source.
    n0 : (3,) array_like
        Normal vector (direction) of source (only required for
        compatibility).
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    L : (3,) array_like
        Dimensions of the rectangular room.
    max_order : int
        Maximum number of reflections for each image source.
    coeffs : (6,) array_like, optional
        Reflection coeffecients of the walls.
        If not given, the reflection coefficients are set to one.
    c : float, optional
        Speed of sound.

    Returns
    -------
    numpy.ndarray
        Sound pressure at positions given by *grid*.

    """
    if coeffs is None:
        coeffs = np.ones(6)

    xs, order = util.image_sources_for_box(x0, L, max_order)
    source_strengths = np.prod(coeffs**order, axis=1)

    p = 0
    for position, strength in zip(xs, source_strengths):
        if strength != 0:
            p += strength * point(omega, position, n0, grid, c)

    return p


def line(omega, x0, n0, grid, c=None):
    """Line source parallel to the z-axis.

    Note: third component of x0 is ignored.

    Notes
    -----
    ::

                           (2)
        G(x-x0, w) = -j/4 H0  (w/c |x-x0|)

    Examples
    --------
    .. plot::
        :context: close-figs

        p = sfs.mono.source.line(omega, x0, None, grid)
        sfs.plot.soundfield(p, grid)
        plt.title("Line Source at {} m".format(x0[:2]))

    Normalization ...

    .. plot::
        :context: close-figs

        sfs.plot.soundfield(p * normalization_line, grid,
                            colorbar_kwargs=dict(label="p / Pa"))
        plt.title("Line Source at {} m (normalized)".format(x0[:2]))

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)[:2]  # ignore z-component
    grid = util.as_xyz_components(grid)

    r = np.linalg.norm(grid[:2] - x0)
    p = -1j/4 * _hankel2_0(k * r)
    return _duplicate_zdirection(p, grid)


def line_velocity(omega, x0, n0, grid, c=None):
    """Velocity of line source parallel to the z-axis.

    Returns
    -------
    `XyzComponents`
        Particle velocity at positions given by *grid*.

    Examples
    --------
    The particle velocity can be plotted on top of the sound pressure:

    .. plot::
        :context: close-figs

        v = sfs.mono.source.line_velocity(omega, x0, None, vgrid)
        sfs.plot.soundfield(p * normalization_line, grid)
        sfs.plot.vectors(v * normalization_line, vgrid)
        plt.title("Sound Pressure and Particle Velocity")

    """
    if c is None:
        c = defs.c
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)[:2]  # ignore z-component
    grid = util.as_xyz_components(grid)

    offset = grid[:2] - x0
    r = np.linalg.norm(offset)
    v = -1/(4*c*defs.rho0) * special.hankel2(1, k * r)
    v = [v * o / r for o in offset]

    assert v[0].shape == v[1].shape

    if len(grid) > 2:
        v.append(np.zeros_like(v[0]))

    return util.XyzComponents([_duplicate_zdirection(vi, grid) for vi in v])


def line_dipole(omega, x0, n0, grid, c=None):
    """Line source with dipole characteristics parallel to the z-axis.

    Note: third component of x0 is ignored.

    Notes
    -----
    ::

                           (2)
        G(x-x0, w) = jk/4 H1  (w/c |x-x0|) cos(phi)


    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)[:2]  # ignore z-components
    n0 = util.asarray_1d(n0)[:2]
    grid = util.as_xyz_components(grid)
    dx = grid[:2] - x0

    r = np.linalg.norm(dx)
    p = 1j*k/4 * special.hankel2(1, k * r) * np.inner(dx, n0) / r
    return _duplicate_zdirection(p, grid)


def line_dirichlet_edge(omega, x0, grid, alpha=3/2*np.pi, Nc=None, c=None):
    """Line source scattered at an edge with Dirichlet boundary conditions.

    :cite:`Moser2012`, eq.(10.18/19)

    Parameters
    ----------
    omega : float
        Angular frequency.
    x0 : (3,) array_like
        Position of line source.
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    alpha : float, optional
        Outer angle of edge.
    Nc : int, optional
        Number of elements for series expansion of driving function.
        Estimated if not given.
    c : float, optional
        Speed of sound

    Returns
    -------
    numpy.ndarray
        Complex pressure at grid positions.

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    phi_s = np.arctan2(x0[1], x0[0])
    if phi_s < 0:
        phi_s = phi_s + 2*np.pi
    r_s = np.linalg.norm(x0)

    grid = util.XyzComponents(grid)

    r = np.linalg.norm(grid[:2])
    phi = np.arctan2(grid[1], grid[0])
    phi = np.where(phi < 0, phi+2*np.pi, phi)

    if Nc is None:
        Nc = np.ceil(2 * k * np.max(r) * alpha/np.pi)

    epsilon = np.ones(Nc)  # weights for series expansion
    epsilon[0] = 2

    p = np.zeros((grid[0].shape[1], grid[1].shape[0]), dtype=complex)
    idxr = (r <= r_s)
    idxa = (phi <= alpha)
    for m in np.arange(Nc):
        nu = m*np.pi/alpha
        f = 1/epsilon[m] * np.sin(nu*phi_s) * np.sin(nu*phi)
        p[idxr & idxa] = p[idxr & idxa] + f[idxr & idxa] * \
            special.jn(nu, k*r[idxr & idxa]) * special.hankel2(nu, k*r_s)
        p[~idxr & idxa] = p[~idxr & idxa] + f[~idxr & idxa] * \
            special.jn(nu, k*r_s) * special.hankel2(nu, k*r[~idxr & idxa])

    p = p * -1j*np.pi/alpha

    pl = line(omega, x0, None, grid, c=c)
    p[~idxa] = pl[~idxa]

    return p


def plane(omega, x0, n0, grid, c=None):
    """Plane wave.

    Parameters
    ----------
    omega : float
        Frequency of plane wave.
    x0 : (3,) array_like
        Position of plane wave.
    n0 : (3,) array_like
        Normal vector (direction) of plane wave.
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    c : float, optional
        Speed of sound.

    Returns
    -------
    `XyzComponents`
        Sound pressure at positions given by *grid*.

    Notes
    -----
    ::

        G(x, w) = e^(-i w/c n x)

    Examples
    --------
    .. plot::
        :context: close-figs

        direction = 45  # degree
        n0 = sfs.util.direction_vector(np.radians(direction))
        p = sfs.mono.source.plane(omega, x0, n0, grid)
        sfs.plot.soundfield(p, grid, colorbar_kwargs=dict(label="p / Pa"))
        plt.title("Plane wave with direction {} degree".format(direction))

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    n0 = util.normalize_vector(n0)
    grid = util.as_xyz_components(grid)
    return np.exp(-1j * k * np.inner(grid - x0, n0))


def plane_velocity(omega, x0, n0, grid, c=None):
    """Velocity of a plane wave.

    Parameters
    ----------
    omega : float
        Frequency of plane wave.
    x0 : (3,) array_like
        Position of plane wave.
    n0 : (3,) array_like
        Normal vector (direction) of plane wave.
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    c : float, optional
        Speed of sound.

    Returns
    -------
    `XyzComponents`
        Particle velocity at positions given by *grid*.

    Notes
    -----
    ::

        V(x, w) = 1/(rho c) e^(-i w/c n x) n

    Examples
    --------
    The particle velocity can be plotted on top of the sound pressure:

    .. plot::
        :context: close-figs

        v = sfs.mono.source.plane_velocity(omega, x0, n0, vgrid)
        sfs.plot.soundfield(p, grid)
        sfs.plot.vectors(v, vgrid)
        plt.title("Sound Pressure and Particle Velocity")

    """
    if c is None:
        c = defs.c
    v = plane(omega, x0, n0, grid, c=c) / (defs.rho0 * c)
    return util.XyzComponents([v * n for n in n0])


def plane_averaged_intensity(omega, x0, n0, grid, c=None):
    """Averaged intensity of a plane wave.

    Parameters
    ----------
    omega : float
        Frequency of plane wave.
    x0 : (3,) array_like
        Position of plane wave.
    n0 : (3,) array_like
        Normal vector (direction) of plane wave.
    grid : triple of array_like
        The grid that is used for the sound field calculations.
        See `sfs.util.xyz_grid()`.
    c : float, optional
        Speed of sound.

    Returns
    -------
    `XyzComponents`
        Averaged intensity at positions given by *grid*.

    Notes
    -----
    ::

        I(x, w) = 1/(2 rho c) n

    """
    if c is None:
        c = defs.c
    i = 1 / (2 * defs.rho0 * c)
    return util.XyzComponents([i * n for n in n0])


def _duplicate_zdirection(p, grid):
    """If necessary, duplicate field in z-direction."""
    gridshape = np.broadcast(*grid).shape
    if len(gridshape) > 2:
        return np.tile(p, [1, 1, gridshape[2]])
    else:
        return p


def _hankel2_0(x):
    """Wrapper for Hankel function of the second type using fast versions
       of the Bessel functions of first/second kind in scipy"""
    return special.j0(x)-1j*special.y0(x)
