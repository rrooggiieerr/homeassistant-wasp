# Home Assistant Wasp in a Box helper sensor

![Python][python-shield]
[![GitHub Release][releases-shield]][releases]
[![Licence][license-shield]][license]
[![Maintainer][maintainer-shield]][maintainer]
[![Home Assistant][homeassistant-shield]][homeassistant]
[![HACS][hacs-shield]][hacs]  

## Introduction

PIR Motion Sensors aren't perfect. If you enter a room and are sitting quietly -- working, reading, sleeping, watching Television -- a PIR Motion Sensor will eventually see no motion. Using such a sensor as the sole source of information to determine if a room is occupied can leave undesired behavior -- lights turning off while you're still in the room, HVAC no longer adjusting temperature for that room, etc. A Wasp Sensor is one solution to that problem.

The name "Wasp in a Box" has been used many times in reference to the logic contained in this Integration. The idea is, if motion is seen in a room (the Wasp) while all the doors are closed, then, even if motion stops, people (the Wasp) are still in there. Once a door opens, the logic resets.

This can also be used if you have motion sensors at all of the exits for a room. If motion happened inside the room and no motion has happened at the exits of a room, then someone is still inside the room.

### Logic

If the "box" is closed and THEN motion is detected, the wasp sensor will immediately turn on.

If the "box" is opened the wasp sensor will immediate turn off. It will stay off until the "box" is closed.

If the "box" becomes closed WHILE motion is detected, the wasp sensor will wait for `timeout` to elapse before checking to ensure that motion is still detected. If it is, the wasp sensor will turn on.

## Installation

### HACS

The recommended way to install this Home Assistant integration is by using [HACS][hacs].
Click the following button to open the integration directly on the HACS integration page.

[![Install Wasp in a Box from HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rrooggiieerr&repository=homeassistant-wasp&category=integration)

Or follow these instructions:

- Go to your **HACS** view in Home Assistant and then to **Integrations**
- Open the **Custom repositories** menu
- Add this repository URL to the **Custom repositories** and select
**Integration** as the **Category**
- Click **Add**
- Close the **Custom repositories** menu
- Select **+ Explore & download repositories** and search for *Wasp in a Box*
- Select **Download**
- Restart Home Assistant

### Manually

- Copy the `custom_components/wasp_sensor` directory of this repository into the
`config/custom_components/` directory of your Home Assistant installation
- Restart Home Assistant

## Adding a new Wasp in a Box helper

### Config flow

- After restarting go to **Settings** then **Devices & Services** then **Helpers**
- Select **+ Create Helper** and type in *Wasp Sensor*
- Define which sensors to be used as Wasp and Box sensor.
- Select **Submit**

A new Wasp sensor will now be added to your Helpers view.

### YAML

This integration is configurable with YAML in `configuration.yaml`. Here's an example configuration:

```yaml
wasp_sensor:
  - name: office
    wasp_sensors:
      - binary_sensor.office_motion_front
      - binary_sensor.office_motion_rear
    box_sensors:
      - binary_sensor.office_door

  - name: office_motion
    wasp_sensors:
      - binary_sensor.office_motion_front
      - binary_sensor.office_motion_rear
    box_sensors:
      - binary_sensor.halldown_motion
```

#### Configuration Details

**name**
User Defined name for the `binary_sensor`

**wasp_sensors**
A List of `entity_id`s that indicate motion in the room. These Entities should have an on/off state and should be `on` when motion is detected.

**wasp_inv_sensors**
The same as `wasp_sensors` but `off` indicates motion.

**box_sensors**
A list of `entity_id`s that indicate when the room is open or when an exit is being used. These Entities should have an on/off state and should be `on` to indicate that the room is exitable or being exited.

**box_inv_sensors**
The same as `box_sensors` but `off` indicates that the room is exitable or being exited.

**timeout**
The number of seconds that `wasp_sensors` and `wasp_inv_sensors` should be in the motion detected state to indicate that the room is truly occupied. This defaults to 180.

## Best Use Cases
With the above configuration, I recommend setting up a template `binary_sensor` to indicate room occupancy.

```yaml
template:
  - binary_sensor:
      - name: "Office Occupied"
        device_class: occupancy
        state: >
          {{
          is_state('binary_sensor.office_motion','on')
          or is_state('binary_sensor.wasp_office', 'on')
          or is_state('binary_sensor.wasp_office_motion','on')
          }}
```

With the above, when `binary_sensor.office_occupied` is `on` your automations can take the desired actions when the room is occupied.

If you don't have "door sensors" or have a room without doors, you can leave that part out of your configuration and out of the template `binary_sensor`. The same is true if you do not have "exit motion sensors". By setting these sensors in an `or` configuration using the template `binary_sensor` you ensure that occupancy will be indicated if any of these sensors have an `on` state.

## Contribution and appreciation

You can contribute to this integration, or show your appreciation, in the following ways.

### Contribute your language

If you would like to use this Home Assistant integration in your own language you can provide a
translation file as found in the `custom_components/wasp_sensor/translations` directory. Create a
pull request (preferred) or issue with the file attached.

More on translating custom integrations can be found
[here](https://developers.home-assistant.io/docs/internationalization/custom_integration/).

### Star this helper

Help other Home Assistant users find this helper by starring this GitHub page. Click **⭐ Star**
on the top right of the GitHub page.

### Hire me

If you would like to have a Home Assistant integration developed for your product or are in need
for a freelance Python developer for your project please contact me, you can find my email address
on [my GitHub profile](https://github.com/rrooggiieerr).

[python-shield]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[releases]: https://github.com/rrooggiieerr/homeassistant-wasp/releases
[releases-shield]: https://img.shields.io/github/v/release/rrooggiieerr/homeassistant-wasp?style=for-the-badge
[license]: ./LICENSE
[license-shield]: https://img.shields.io/github/license/rrooggiieerr/homeassistant-wasp?style=for-the-badge
[maintainer]: https://github.com/rrooggiieerr
[maintainer-shield]: https://img.shields.io/badge/MAINTAINER-%40rrooggiieerr-41BDF5?style=for-the-badge
[homeassistant]: https://www.home-assistant.io/
[homeassistant-shield]: https://img.shields.io/badge/home%20assistant-%2341BDF5.svg?style=for-the-badge&logo=home-assistant&logoColor=white
[hacs]: https://hacs.xyz/
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
