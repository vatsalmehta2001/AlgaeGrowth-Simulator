"""Beer-Lambert light attenuation and depth-averaged irradiance.

Implements the light model for microalgal photobioreactor simulation.
Light attenuation through the culture is one of two core growth-limiting
factors (along with CO2 availability).

Functions are pure (no side effects, no state mutation) and take raw
float arguments for maximum testability and reusability.

References:
    - Razzak et al. (2024) Eq. 18-19: Beer-Lambert attenuation in
      microalgal cultures with biomass-specific extinction.
    - Schediwy et al. (2019) Eq. 3, 10: Depth-averaged irradiance
      analytical solution for open raceway ponds.
"""

import numpy as np


def beer_lambert(
    I0: float,
    sigma_x: float,
    biomass_conc: float,
    depth: float,
    k_bg: float = 0.0,
) -> float:
    """Compute irradiance at a specific depth using Beer-Lambert law.

    I(z) = I0 * exp(-(sigma_x * X + k_bg) * z)

    Args:
        I0: Surface irradiance [umol/m2/s].
        sigma_x: Biomass-specific light absorption coefficient [m2/g].
        biomass_conc: Biomass concentration X [g/L].
        depth: Depth z below the surface [m].
        k_bg: Background (non-biomass) extinction coefficient [1/m].

    Returns:
        Irradiance at the given depth [umol/m2/s].

    References:
        Razzak et al. (2024) Eq. 18: I(z) = I0 * exp(-K_ext * z)
    """
    if I0 <= 0.0:
        return 0.0

    K = sigma_x * biomass_conc + k_bg
    return float(I0 * np.exp(-K * depth))


def depth_averaged_irradiance(
    I0: float,
    sigma_x: float,
    biomass_conc: float,
    depth: float,
    k_bg: float = 0.0,
) -> float:
    """Compute analytical depth-averaged irradiance over the full pond depth.

    I_avg = I0 / (K * D) * (1 - exp(-K * D))

    where K = sigma_x * X + k_bg is the total extinction coefficient.

    This analytical solution avoids the common pitfall of using surface
    irradiance alone, which overestimates growth by 20-50%. The depth
    average accounts for the exponential light gradient through the culture.

    Args:
        I0: Surface irradiance [umol/m2/s].
        sigma_x: Biomass-specific light absorption coefficient [m2/g].
        biomass_conc: Biomass concentration X [g/L].
        depth: Pond/reactor depth D [m].
        k_bg: Background (non-biomass) extinction coefficient [1/m].

    Returns:
        Depth-averaged irradiance [umol/m2/s].

    References:
        Schediwy et al. (2019) Eq. 3, 10: Analytical depth-averaged
        irradiance for raceway pond modelling.
        Razzak et al. (2024) Eq. 19: Depth-integrated light availability.
    """
    if I0 <= 0.0:
        return 0.0

    K = sigma_x * biomass_conc + k_bg
    KD = K * depth

    # Guard: if K*D is near zero (no attenuation), return surface irradiance
    if abs(KD) < 1e-10:
        return float(I0)

    return float(I0 / KD * (1.0 - np.exp(-KD)))
