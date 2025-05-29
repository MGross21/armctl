# JAKA

## Turning On the Robot

### Power On

Press the **Power** button if the control box LED isn't already breathing blue.

### Unlock Safety

Press and hold the **Lock** button for about 3 seconds until the LED turns green.

### Enable the Robot

Press the **Enable** or **Motor** button to power the joints.

You should hear a click or hum if it's working. Some models require you to press and hold briefly.

The LED or other feedback may indicate the robot is "ready."

## Documentation Reference

[JAKA TCP/IP Control Protocol](https://www.jaka.com/docs/en/guide/tcpip.html)

### Receiving Data

Port 10_000 Content Example:

```jsonc
{
    "len": Int,                // Length of the data packet (max ~5000 bytes)
    "drag_status": Bool,       // Indicates drag mode status
    "extio": Object{...},      // Extended IO modules configuration and status
    "errcode": "0x0",         // Error code from controller
    "errmsg": "",             // Error message corresponding to errcode
    "monitor_data": [6],       // Monitoring data for diagnosis
    "torqsensor": [2],         // End force sensor setup and status
    "joint_actual_position": [6], // Actual position of all 6 joints
    "joint_position": [6],     // Commanded position of 6 joints
    "actual_position": [6],    // Actual TCP position in Cartesian space
    "position": [6],           // Commanded TCP position in Cartesian space
    "din": [144],              // Status of all digital inputs in cabinet
    "dout": [144],             // Status of all digital outputs in cabinet
    "ain": [66],               // Status of all analog inputs in cabinet
    "aout": [66],              // Values of all analog outputs in cabinet
    "tio_key": [3],            // Tool IO key status
    "tio_din": [8],            // Tool digital inputs status
    "tio_dout": [8],           // Tool digital outputs status
    "tio_ain": [1],            // Tool analog inputs status
    "task_state": Int,         // Power and enabling status of the robot
    "homed": [9],              // Home status of each joint (obsolete)
    "task_mode": Int,          // Task mode of the robot
    "interp_state": Int,       // Program status (idle, loading, paused, running)
    "enabled": Bool,           // Robot enabling status
    "paused": Bool,            // Program pausing status
    "rapidrate": Int,          // Scale rate of robot movement
    "current_tool_id": Int,    // Index of current TCP
    "current_user_id": Int,    // Index of current user coordinate frame
    "on_soft_limit": Int,      // Indicates if on soft limit
    "emergency_stop": Int,     // Emergency stop status
    "drag_near_limit": [6],    // Dragged to limit position status
    "funcdi": [15],            // Function DI setup
    "powered_on": Int,         // Power status of the robot
    "inpos": Bool,             // Indicates if robot is in position
    "motion_mode": Int,        // Motion mode (obsolete)
    "curr_tcp_trans_vel": Int, // Current TCP movement speed
    "protective_stop": Int,    // Protective stop status
    "point_key": Int,          // Point button status at robot end
    "netState": Int            // Socket connection state (obsolete)
}
```
