from housing_pricer.valuation_api._utilities.geocode_address import (
    _extract_coordinates,
    _format_search_query,
)


def test_format_endpoint():
    actual_output = _format_search_query(
        gata="Attundavägen", gatunummer="14", ort="Täby"
    )
    expected_output = "Attundavägen+14,+Täby"
    assert actual_output == expected_output


def test_extract_coordinates():
    url = ".../maps/place/Attund...A4by/@59.4430162,18.0678478,17z/..."
    expected_coordinates = {"latitude": 59.4430162, "longitude": 18.0678478}
    coordinates = _extract_coordinates(url)
    assert coordinates == expected_coordinates
