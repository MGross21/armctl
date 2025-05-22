# Universal Robotics

This document provides resources and references for interfacing with Universal Robots controllers, with a focus on communication protocols, data exchange, and available software libraries.

## Communication and Port Access

- [Remote Control via TCP/IP](https://www.universal-robots.com/articles/ur/interface-communication/remote-control-via-tcpip/): Official guide for accessing and controlling UR robots over TCP/IP.

## Real-Time Data Exchange (RTDE)

RTDE is a proprietary protocol for real-time data synchronization with Universal Robots controllers.

- [RTDE Overview](https://www.universal-robots.com/developer/communication-protocol/rtde/)
- [Complete I/O Documentation](https://www.universal-robots.com/articles/ur/interface-communication/real-time-data-exchange-rtde-guide/)

> [!Note]
> The following libraries are not currently used in this project but are provided for reference:
>
> - RTDE Python Client Library ([GitHub](https://github.com/UniversalRobots/RTDE_Python_Client_Library))
> - `ur_rtde`: 3rd Party Standalone Python Library ([GitLab](https://gitlab.com/sdurobotics/ur_rtde) ([PyPI](https://pypi.org/project/ur-rtde/#data)))

## Additional Resources

> [!Note]  
> The following libraries are not currently used in this project but are provided for reference:
> - [DH Parameters for Kinematics and Dynamics](https://www.universal-robots.com/articles/ur/application-installation/dh-parameters-for-calculations-of-kinematics-and-dynamics/)
> - `urx`: 3rd Party Python Library ([GitHub](https://github.com/SintefManufacturing/python-urx))
> - `.NET SDK`: 3rd Party Licensed ([Website](https://underautomation.com/universal-robots)) ([GitHub](https://github.com/underautomation/UniversalRobots.NET))
