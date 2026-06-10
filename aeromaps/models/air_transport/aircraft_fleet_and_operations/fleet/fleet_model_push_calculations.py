"""
fleet_model push_visualisation
===========

Module for calculating the result of the push fleet model.
"""
from scipy import integrate, optimize
import numpy as np

def i1(gamma, m):
    """∫₀ᵐ t(m-t) exp(γt) dt"""
    val, _ = integrate.quad(lambda t: t * (m - t) * np.exp(gamma * t), 0, m)
    return val

def i_d(gamma, m, a, b):
    """∫₀ᵐ t(m-t) exp(γt) dt"""
    val, _ = integrate.quad(lambda t: t * (m - t) * np.exp(gamma * t), a, b)
    return val

def i2(gamma, m):
    """∫₀ᵐ t²(m-t) exp(γt) dt"""
    val, _ = integrate.quad(lambda t: t**2 * (m - t) * np.exp(gamma * t), 0, m)
    return val

def solve_deliv(B, m, gamma_bounds=(-10, 10)):

    if not (0 < B / 1 < m):
        raise ValueError(
            f"B/A = {B:.4f} doit être strictement dans (0, {m}) "
            "(la moyenne de t sous f doit rester dans l'intervalle)."
        )

    ratio = B
    def g(gamma):
        i_1 = i1(gamma, m)
        if abs(i_1) < 1e-14:
            return np.inf
        return i2(gamma, m) / i_1 - ratio
    # Vérification que g change de signe sur l'intervalle
    ga, gb = gamma_bounds
    fa, fb = g(ga), g(gb)
    if fa * fb > 0:
        raise ValueError(
            f"Impossible de trouver gamma dans [{ga}, {gb}] : "
            f"g({ga})={fa:.3f}, g({gb})={fb:.3f}. "
            "Essayez d'élargir gamma_bounds."
        )

    gamma_sol = optimize.brentq(g, ga, gb, xtol=1e-12, rtol=1e-12)
    mu_sol    = 1 / i1(gamma_sol, m)

    return mu_sol, gamma_sol

def fleet_content(a, b, fleet_obs_t, retirement_coeffs, constraint, epsilon=0.0001, first = False):
    if first :
        fleets_b = b**(np.exp(-retirement_coeffs)) * fleet_obs_t
        if fleets_b.sum().sum() < constraint :
            print('temporary aircraft parking', end=' ')
            # return fleet_content(b, 1,fleet_obs_t, retirement_coeffs, constraint, epsilon)
            # print(b)
            return fleet_content(b, b*2, fleet_obs_t, retirement_coeffs, constraint, epsilon, first = True)

    fleets = ((a+b)/2)**(np.exp(-retirement_coeffs)) * fleet_obs_t
    e = (fleets.sum().sum() - constraint)/constraint
    # print('power: '+str((a+b)/2) + ' constraint: '+str(constraint) + ' '+str(fleets.sum().sum())+' error: '+str(np.abs(e)))
    if b==0:
        print('reso bug')
    if np.abs(e) < epsilon:
        return fleets, (a+b)/2
    elif e > 0:
        return fleet_content(a, (a+b)/2,fleet_obs_t, retirement_coeffs, constraint, epsilon)
    else:
        return fleet_content((a+b)/2, b,fleet_obs_t, retirement_coeffs, constraint, epsilon)