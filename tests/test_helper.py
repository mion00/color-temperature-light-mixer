from custom_components.light_temperature_mixer.const import (
    CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
    CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
)
from custom_components.light_temperature_mixer.helper import (
    BRIGHTNESS_RANGE,
    BrightnessCalculator,
    BrightnessTemperaturePriority,
)
from homeassistant.util.color import (
    color_temperature_kelvin_to_mired,
    color_temperature_mired_to_kelvin,
)


class TestBrightnessCalculator:

    def test_full_warm_only(self):
        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            3000,
            int(BRIGHTNESS_RANGE[1] / 2),
        )
        ww, cw = bc.compute_brightnesses()
        assert BRIGHTNESS_RANGE[1] - 1 <= ww <= BRIGHTNESS_RANGE[1]
        assert cw == 0

    def test_full_cold_only(self):
        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            6000,
            int(BRIGHTNESS_RANGE[1] / 2),
        )
        ww, cw = bc.compute_brightnesses()
        assert ww == 0
        assert BRIGHTNESS_RANGE[1] - 1 <= cw <= BRIGHTNESS_RANGE[1]

    def test_inside_range(self):
        target_temperature = 4000
        target_brightness = int(BRIGHTNESS_RANGE[1] / 2)

        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            target_temperature,
            target_brightness,
        )
        ww, cw = bc.compute_brightnesses()

        assert ww == 128
        assert cw == 126

    def test_middle_temperature(self):
        cold_light_mired = color_temperature_kelvin_to_mired(
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE
        )
        warm_light_mired = color_temperature_kelvin_to_mired(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE
        )
        target_temperature_mired = (cold_light_mired + warm_light_mired) / 2

        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            color_temperature_mired_to_kelvin(target_temperature_mired),
            int((BRIGHTNESS_RANGE[0] + BRIGHTNESS_RANGE[1]) / 4),
        )
        ww, cw = bc.compute_brightnesses()

        mid_brightness = (BRIGHTNESS_RANGE[0] + BRIGHTNESS_RANGE[1]) / 4
        assert mid_brightness - 1 <= ww <= mid_brightness
        assert mid_brightness - 1 <= cw <= mid_brightness

    def test_full_cold_temperature_priority(self):
        target_temperature = CONF_DEFAULT_COLD_LIGHT_TEMPERATURE

        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            int(target_temperature),
            int(BRIGHTNESS_RANGE[1]),
            BrightnessTemperaturePriority.TEMPERATURE,
        )
        ww, cw = bc.compute_brightnesses()

        assert -1 <= ww <= 0
        assert BRIGHTNESS_RANGE[1] - 1 <= cw <= BRIGHTNESS_RANGE[1]

    def test_full_warm_temperature_priority(self):
        target_temperature = CONF_DEFAULT_WARM_LIGHT_TEMPERATURE

        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            int(target_temperature),
            int(BRIGHTNESS_RANGE[1]),
            BrightnessTemperaturePriority.TEMPERATURE,
        )
        ww, cw = bc.compute_brightnesses()

        assert BRIGHTNESS_RANGE[1] - 1 <= ww <= BRIGHTNESS_RANGE[1]
        assert -1 <= cw <= 0

    def test_full_cold_brightness_priority(self):

        target_temperature = CONF_DEFAULT_COLD_LIGHT_TEMPERATURE
        target_brightness = int(BRIGHTNESS_RANGE[1])
        priority = BrightnessTemperaturePriority.BRIGHTNESS

        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            int(target_temperature),
            target_brightness,
            priority,
        )
        ww, cw = bc.compute_brightnesses()

        assert BRIGHTNESS_RANGE[1] - 1 <= ww <= BRIGHTNESS_RANGE[1], ww
        assert BRIGHTNESS_RANGE[1] - 1 <= cw <= BRIGHTNESS_RANGE[1], cw

    def test_full_warm_brightness_priority(self):

        target_temperature = CONF_DEFAULT_WARM_LIGHT_TEMPERATURE
        target_brightness = int(BRIGHTNESS_RANGE[1])
        priority = BrightnessTemperaturePriority.BRIGHTNESS

        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            int(target_temperature),
            target_brightness,
            priority,
        )
        ww, cw = bc.compute_brightnesses()

        assert BRIGHTNESS_RANGE[1] - 1 <= ww <= BRIGHTNESS_RANGE[1], ww
        assert BRIGHTNESS_RANGE[1] - 1 <= cw <= BRIGHTNESS_RANGE[1], cw

    def test_mixed(self):
        target_temperature = 5000
        target_brightness = int(BRIGHTNESS_RANGE[1])
        priority = BrightnessTemperaturePriority.MIXED

        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            int(target_temperature),
            target_brightness,
            priority,
        )
        ww, cw = bc.compute_brightnesses()

        assert ww == 234
        assert cw == 255

    def test_mixed_warmer(self):
        target_temperature = 3500
        target_brightness = int(BRIGHTNESS_RANGE[1])
        priority = BrightnessTemperaturePriority.MIXED

        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            int(target_temperature),
            target_brightness,
            priority,
        )
        ww, cw = bc.compute_brightnesses()

        assert ww == 255
        assert cw == 240

    def test_mixed_6000_189(self):
        target_temperature = 6000
        target_brightness = 189
        priority = BrightnessTemperaturePriority.MIXED

        bc = BrightnessCalculator(
            CONF_DEFAULT_WARM_LIGHT_TEMPERATURE,
            CONF_DEFAULT_COLD_LIGHT_TEMPERATURE,
            target_temperature,
            target_brightness,
            priority,
        )
        ww, cw = bc.compute_brightnesses()

        assert ww == 65
        assert cw == 255
