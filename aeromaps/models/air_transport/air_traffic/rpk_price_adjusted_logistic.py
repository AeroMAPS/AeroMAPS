from numpy import divide
from numpy import exp


def generalised_logistic_function(
    x, left_asymptote, capacity, growth_rate, logistic_nu, asymptote_coeff, x_lag
):
    y = left_asymptote + divide(
        capacity - left_asymptote,
        (asymptote_coeff + exp(
            -growth_rate * (x - x_lag)
        )) ** (1.0 / logistic_nu),
    )

    return y

def per_capita_logistic_price(
    population, gdp_per_capita, price,
    left_asymptote, capacity, growth_rate, logistic_nu, asymptote_coeff, x_lag,
    price_ref, price_elast
):
    rpk_per_capita_trend = generalised_logistic_function(
        x=gdp_per_capita,
        left_asymptote=left_asymptote,
        capacity=capacity,
        growth_rate=growth_rate,
        logistic_nu=logistic_nu,
        asymptote_coeff=asymptote_coeff,
        x_lag=x_lag,
    )
    price_index = (price / price_ref) ** price_elast
    rpk_per_capita = rpk_per_capita_trend * price_index
    rpk = population * rpk_per_capita
    return rpk, rpk_per_capita, rpk_per_capita_trend, price_index