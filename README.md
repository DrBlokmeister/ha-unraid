# Home Assistant Integration for Unraid®

[![HACS Integration][hacsbadge]][hacs]
[![GitHub Last Commit](https://img.shields.io/github/last-commit/ruaan-deysel/ha-unraid)](https://github.com/ruaan-deysel/ha-unraid/commits/main)
[![GitHub Release](https://img.shields.io/github/v/release/ruaan-deysel/ha-unraid?sort=semver)](https://github.com/ruaan-deysel/ha-unraid/releases)
[![GitHub Issues](https://img.shields.io/github/issues/ruaan-deysel/ha-unraid)](https://github.com/ruaan-deysel/ha-unraid/issues)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/ruaan-deysel)](https://github.com/sponsors/ruaan-deysel)
[![Community Forum](https://img.shields.io/badge/Community-Forum-blue)](https://community.home-assistant.io/t/unraid-integration)
[![License](https://img.shields.io/github/license/ruaan-deysel/ha-unraid)](./LICENSE)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ruaan-deysel/ha-unraid)

[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs]: https://github.com/hacs/integration

A Home Assistant custom integration for monitoring and controlling Unraid servers via the official GraphQL API.

> **Note**: This integration requires **Unraid 7.2.0 or later** which includes the GraphQL API.
>
> **Important**: This integration requires the **latest version** of the Unraid GraphQL API. If you encounter issues, install the **Unraid Connect** plugin from the Unraid Community Applications store — it automatically keeps the GraphQL API up to date. Many reported issues are resolved simply by updating to the latest API version.
>
> ⚠️ **Migration Notice**: Release **2025.06.11** is the **last stable SSH-based** version of this integration. Starting with **2025.12.0**, this integration has been completely rebuilt to use Unraid's official GraphQL API. **There is no direct migration or upgrade path** from SSH to GraphQL - you will need to remove the old integration and set up fresh with a new API key. Users who prefer the SSH-based integration can continue using [release 2025.06.11](https://github.com/ruaan-deysel/ha-unraid/releases/tag/v2025.06.11).

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruaan-deysel&repository=ha-unraid&category=integration)

1. Click the button above or manually add the repository in HACS
2. Search for **Unraid** and click **Download**
3. Restart Home Assistant

### Alternative

I encourage users to check out **[Unraid Management Agent integration](https://www.github.com/ruaan-deysel/ha-unraid-management-agent)**, which provides an alternative solution for integrating Unraid with Home Assistant.

## Features

### System Monitoring

* **CPU Usage**: Real-time CPU utilization percentage
* **CPU Temperature**: Package temperature monitoring
* **CPU Power**: Power consumption (when available)
* **Memory Usage**: Used memory and percentage utilization
* **System Uptime**: Human-readable uptime display

### Storage Management

* **Array Status**: State tracking (started/stopped/degraded)
* **Array Capacity**: Total, used, free space with usage percentage
* **Parity Status**: Parity check status, progress, and validation
* **Disk Health**: Per-disk health monitoring (binary sensors)
* **Disk Usage**: Individual disk capacity and usage for data and cache disks
* **Share Usage**: Per-share storage utilization
* **Flash Device**: Boot device usage monitoring

### Docker Container Control

* **Container Switches**: Start/stop Docker containers
* **State Sync**: Real-time container state updates
* **Attributes**: Container image, status, and port information

### Virtual Machine Control

* **VM Switches**: Start/stop virtual machines
* **State Sync**: Real-time VM state updates
* **Attributes**: VM name and state information

### UPS Monitoring (when connected)

* **Battery Level**: Charge percentage
* **Load**: Current UPS load percentage
* **Runtime**: Estimated battery runtime
* **Power Consumption**: Calculated power usage for Energy Dashboard (requires configuration)
* **Connection Status**: UPS connected binary sensor

### Notifications

* **Active Notifications**: Count of unread Unraid notifications
* **Notification Events**: Home Assistant event entity for new Unraid notifications
* **Notification Metadata**: Notification title, subject, description, timestamp, importance, type, link, and ID exposed as event attributes

## Requirements

* **Home Assistant**: 2025.12.0 or later
* **Unraid Server**: 7.2.0 or later with the **latest GraphQL API** (install the [Unraid Connect](https://unraid.net/connect) plugin to stay up to date)
* **Unraid API Key**: Generated in Unraid settings

### Manual Installation

1. Download this repository as ZIP
2. Extract the `custom_components/unraid` folder
3. Copy it to your Home Assistant `config/custom_components/` directory
4. Restart Home Assistant

## Configuration

### Step 1: Generate Unraid API Key

1. Log in to your Unraid WebGUI
2. Navigate to **Settings** → **Management Access** → **API**
3. Click **Add** to create a new API key
4. Copy the generated API key

### Step 2: Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **Unraid**
4. Enter your configuration:

   * **Host**: Unraid server IP or hostname
   * **API Key**: The key from Step 1

The integration will validate the connection and create entities for all discovered devices.

### Step 3: Configure Options (Optional)

After setup, you can adjust UPS settings (only shown if UPS is detected):

1. Go to **Settings** → **Devices & Services**
2. Find the Unraid entry and click **Configure**
3. Adjust:

   * **UPS capacity (VA)**: Your UPS VA rating for reference
   * **UPS nominal power (W)**: Required for UPS Power sensor in Energy Dashboard

> **Note**: Polling intervals are fixed per Home Assistant Core guidelines:
>
> * System data (CPU, RAM, Docker, VMs): **30 seconds**
> * Storage data (array, disks, SMART): **5 minutes**
>
> For custom refresh rates, use the `homeassistant.update_entity` service (see [Custom Polling](#custom-polling-intervals) below).

## Entity Overview

### Sensors

| Entity          | Description         | Device Class |
| --------------- | ------------------- | ------------ |
| CPU Usage       | CPU utilization %   | -            |
| CPU Temperature | Package temp °C     | temperature  |
| CPU Power       | Power consumption W | power        |
| Memory Usage    | RAM used %          | -            |
| Uptime          | System uptime       | -            |
| Array State     | started/stopped     | enum         |
| Array Usage     | Capacity used %     | -            |
| Parity Progress | Check progress %    | -            |
| Disk Usage      | Per-disk used %     | -            |
| Share Usage     | Per-share used %    | -            |
| Flash Usage     | Boot device used %  | -            |
| UPS Battery     | Charge level %      | battery      |
| UPS Load        | Current load %      | -            |
| UPS Runtime     | Estimated runtime   | -            |
| UPS Power       | Power consumption W | power        |
| Notifications   | Unread count        | -            |

### Binary Sensors

| Entity               | Description                         |
| -------------------- | ----------------------------------- |
| Array Started        | Array running state                 |
| Parity Check Running | Parity check in progress            |
| Parity Valid         | Parity status healthy               |
| Disk Health          | Per-disk health (problem if not OK) |
| UPS Connected        | UPS connection status               |

### Event Entities

| Entity        | Description                          | Event Type             |
| ------------- | ------------------------------------ | ---------------------- |
| Notifications | New Unraid notification was received | `notification_created` |

The exact entity ID depends on the configured Unraid server name. For example, a server named `Tower` may create `event.tower_notifications`.

### Switches

| Entity            | Description           |
| ----------------- | --------------------- |
| Docker Containers | Start/stop containers |
| Virtual Machines  | Start/stop VMs        |

### Buttons

| Entity                  | Description               |
| ----------------------- | ------------------------- |
| Array Start/Stop        | Control array state       |
| Parity Check Start/Stop | Control parity operations |
| Disk Spin Up/Down       | Control disk spin state   |

## UPS Power Sensor for Energy Dashboard

To track UPS power consumption in Home Assistant's Energy Dashboard:

1. Go to **Settings** → **Devices & Services**
2. Find Unraid and click **Configure**
3. Set **UPS capacity (VA)** to your UPS rating (e.g., 1000 for a 1000VA UPS)
4. The UPS Power sensor will show calculated wattage based on load percentage

**Formula**: `Power (W) = Load% × Capacity (VA) × 0.6 (power factor)`

## Notification Events

The integration exposes Unraid notifications in two ways:

1. A notification sensor that reports the number of unread Unraid notifications.
2. A Home Assistant event entity that updates whenever a new Unraid notification is received.

The event entity is useful for automations because it exposes the full notification payload as attributes. A typical event entity state update includes:

| Attribute             | Description                                    | Example                      |
| --------------------- | ---------------------------------------------- | ---------------------------- |
| `event_type`          | Home Assistant event type for the event entity | `notification_created`       |
| `notification_id`     | Unique Unraid notification identifier          | `abc123:Disk_Error.notify`   |
| `title`               | Notification title                             | `Disk Alert`                 |
| `subject`             | Notification subject                           | `Array has disk errors`      |
| `description`         | Detailed notification text                     | `Disk 1 has read errors`     |
| `timestamp`           | Notification timestamp from Unraid             | `2026-04-30T12:26:09.000Z`   |
| `formatted_timestamp` | Human-readable timestamp supplied by Unraid    | `Thursday, 30-04-2026 14:26` |
| `importance`          | Notification importance                        | `INFO`, `WARNING`, `ALERT`   |
| `notification_type`   | Unraid notification state/type                 | `UNREAD`                     |
| `link`                | Optional link supplied by Unraid               | `/Main`                      |

You can inspect the exact entity ID and attributes in **Developer Tools** → **States** by searching for `_notifications`, or by triggering a test notification in Unraid and watching the event entity update. Because this is a Home Assistant event entity, the state is usually the timestamp of the most recent event. The actual notification details are in the attributes.

## Dynamic Entity Creation

The integration only creates entities for available services:

* **No UPS connected** → No UPS sensors created
* **Docker service stopped** → No container switches created
* **No VMs defined** → No VM switches created
* **No shares** → No share sensors created
* **No notification support from the API** → No notification event entity created

Entities are automatically created when services become available.

## Troubleshooting

### Connection Issues

* **Verify API Key**: Ensure the key is valid and has appropriate permissions
* **Network Access**: Confirm Home Assistant can reach the Unraid server
* **Firewall**: Ensure HTTPS port (443) is accessible
* **Unraid Version**: Requires 7.2.0+ with the latest GraphQL API (install Unraid Connect plugin to update)

### Missing Entities

* Check if the service is running (Docker, VMs, UPS)
* Verify devices exist on the Unraid server
* Check Home Assistant logs for errors

### Notification Events Not Appearing

* Confirm your Unraid GraphQL API is up to date
* Check that a notifications event entity exists, for example `event.tower_notifications`
* Trigger a new Unraid notification and verify the event entity state changes
* Check the event entity attributes in **Developer Tools** → **States**
* Check Home Assistant logs for integration or coordinator errors

### Entities Not Updating

* System sensors update every 30 seconds, storage sensors every 5 minutes
* Use `homeassistant.update_entity` service to force immediate refresh
* Check Unraid server responsiveness
* View integration diagnostics for coordinator status

### Reauthentication

If your API key becomes invalid:

1. A repair notification will appear in Home Assistant
2. Click the notification and follow the steps to enter a new API key
3. Alternatively, go to **Settings** → **Devices & Services**, find Unraid, and use the "Reconfigure" option

## Removal

To remove the integration:

1. Go to **Settings** → **Devices & Services**
2. Find the **Unraid** entry
3. Click the three-dot menu (⋮) and select **Delete**
4. Confirm removal

If you installed via HACS, you can also uninstall from HACS after removing the integration.

## Known Limitations

* **Unraid 7.2+ Required**: This integration uses the GraphQL API which was introduced in Unraid 7.2.0. The latest API version is always required — install the Unraid Connect plugin to keep it updated
* **No Network Discovery**: Unraid servers must be manually configured (no SSDP/mDNS discovery)
* **Disk SMART Data**: SMART queries can be slow on large arrays; storage polling is less frequent to compensate
* **Container/VM Actions**: Start/stop operations may take up to 60 seconds to complete
* **SSL Certificates**: Self-signed certificates require enabling "Allow insecure connections" (or configuring custom CA)
* **Notification History**: Notification event entities represent newly received notifications. Use the unread notification sensor for the current unread count, and Unraid itself for full notification history

## Custom Polling Intervals

Polling intervals are fixed per Home Assistant Core integration guidelines. If you need more frequent updates for specific sensors (e.g., disk temperatures for fan control), use the `homeassistant.update_entity` service with a time-pattern automation:

```yaml
automation:
  - alias: "Update disk temperatures every 60 seconds"
    trigger:
      - trigger: time_pattern
        seconds: "/60"
    action:
      - action: homeassistant.update_entity
        target:
          entity_id:
            - sensor.unraid_tower_disk1_temperature
            - sensor.unraid_tower_disk2_temperature
            # Add all disk temperature sensors you need
```

This allows custom refresh rates while keeping the integration compliant with HA Core standards.

## Automation Examples

### Alert on Parity Check Errors

```yaml
automation:
  - alias: "Unraid Parity Check Error Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.unraid_tower_parity_valid
        to: "off"
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Unraid Parity Error"
          message: "Parity check has detected errors on your Unraid server."
```

### Notify When Array Stops

```yaml
automation:
  - alias: "Unraid Array Stopped"
    trigger:
      - platform: state
        entity_id: binary_sensor.unraid_tower_array_started
        to: "off"
    action:
      - service: notify.mobile_app
        data:
          title: "Unraid Array"
          message: "The Unraid array has stopped."
```

### Start Container on Schedule

```yaml
automation:
  - alias: "Start Plex at 6PM"
    trigger:
      - platform: time
        at: "18:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.unraid_tower_plex
```

### Forward Important Unraid Notifications to Mobile

This example listens for new Unraid notifications and forwards warnings or alerts to a Home Assistant notification service. Replace `event.tower_notifications` and `notify.mobile_app_your_phone` with your own entity and notify service.

```yaml
automation:
  - alias: "[system|nas] Notify on important Unraid notifications"
    id: yaml_automation_system_nas_notify_on_important_unraid_notifications
    description: >
      Sends a mobile notification when the Unraid notification event entity
      receives a new WARNING or ALERT notification.
    mode: queued
    trigger:
      - platform: state
        entity_id: event.tower_notifications
    condition:
      - condition: template
        value_template: >-
          {{ trigger.to_state is not none
             and trigger.to_state.attributes.event_type == 'notification_created'
             and trigger.to_state.attributes.importance in ['WARNING', 'ALERT'] }}
    action:
      - variables:
          notification_title: >-
            {{ trigger.to_state.attributes.title | default('Unraid notification') }}
          notification_subject: >-
            {{ trigger.to_state.attributes.subject | default('') }}
          notification_description: >-
            {{ trigger.to_state.attributes.description | default('') }}
          notification_importance: >-
            {{ trigger.to_state.attributes.importance | default('UNKNOWN') }}
          notification_timestamp: >-
            {{ trigger.to_state.attributes.formatted_timestamp
               | default(trigger.to_state.attributes.timestamp | default('')) }}
      - service: notify.mobile_app_your_phone
        data:
          title: "⚠️ Unraid {{ notification_importance }}: {{ notification_title }}"
          message: >-
            {{ notification_subject }}
            {%- if notification_description %}

            {{ notification_description }}
            {%- endif %}
            {%- if notification_timestamp %}

            Time: {{ notification_timestamp }}
            {%- endif %}
```

### Log All Unraid Notification Event Data

This example is useful while developing or troubleshooting notification automations. It writes the full event payload to the Home Assistant log whenever a new Unraid notification event is emitted.

```yaml
automation:
  - alias: "[system|nas] Log Unraid notification event data"
    id: yaml_automation_system_nas_log_unraid_notification_event_data
    description: >
      Writes all available Unraid notification event entity data to the Home
      Assistant log whenever a new notification_created event is emitted.
    mode: queued
    trigger:
      - platform: state
        entity_id: event.tower_notifications
    condition:
      - condition: template
        value_template: >-
          {{ trigger.to_state is not none
             and trigger.to_state.attributes.event_type == 'notification_created' }}
    action:
      - service: system_log.write
        data:
          level: info
          logger: homeassistant.components.automation.unraid_notification_event
          message: >-
            Unraid notification event received.
            Entity: {{ trigger.entity_id }};
            From state: {{ trigger.from_state.state if trigger.from_state else 'none' }};
            To state: {{ trigger.to_state.state }};
            Event type: {{ trigger.to_state.attributes.event_type | default('none') }};
            Notification ID: {{ trigger.to_state.attributes.notification_id | default('none') }};
            Title: {{ trigger.to_state.attributes.title | default('none') }};
            Subject: {{ trigger.to_state.attributes.subject | default('none') }};
            Description: {{ trigger.to_state.attributes.description | default('none') }};
            Timestamp: {{ trigger.to_state.attributes.timestamp | default('none') }};
            Formatted timestamp: {{ trigger.to_state.attributes.formatted_timestamp | default('none') }};
            Importance: {{ trigger.to_state.attributes.importance | default('none') }};
            Type: {{ trigger.to_state.attributes.notification_type | default('none') }};
            Link: {{ trigger.to_state.attributes.link | default('none') }};
            All attributes: {{ trigger.to_state.attributes | to_json }}
```

## Development

### Prerequisites

* Docker Desktop
* VS Code with Dev Containers extension

### Setup

```bash
git clone https://github.com/ruaan-deysel/ha-unraid.git
cd ha-unraid
code .
# Reopen in Dev Container when prompted
```

### Commands

```bash
./script/setup    # Install dependencies
./script/lint     # Format and lint (run after every change!)
pytest             # Run tests
./script/develop  # Start Home Assistant for testing
```

### Code Quality

This project enforces strict code quality:

* All changes must pass `./script/lint` with zero warnings
* All tests must pass before committing
* Type hints required for all functions

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make changes and run `./script/lint`
4. Run tests with `pytest`
5. **Keep PRs small and focused** - one issue/feature per PR
6. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

Licensed under the Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Disclaimer

Unraid® is a registered trademark of Lime Technology, Inc. This integration is not affiliated with, endorsed, or sponsored by Lime Technology, Inc.
