def constant_elasticity(
    population, gdp_per_capita, price,
    sigma, income_elast, price_elast
):
    rpk_per_capita = sigma * (gdp_per_capita ** income_elast) * (price ** price_elast)
    rpk = population * rpk_per_capita
    return rpk, rpk_per_capita