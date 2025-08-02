# Universal Robots

This document provides resources and references for interfacing with Universal Robots controllers, with a focus on communication protocols, data exchange, and available software libraries.

## Communication and Port Access

- [Remote Control via TCP/IP](https://www.universal-robots.com/articles/ur/interface-communication/remote-control-via-tcpip/): Official guide for accessing and controlling UR robots over TCP/IP.
- [URScript Programming Language](https://s3-eu-west-1.amazonaws.com/ur-support-site/77327/scriptManual_e-Series_5.9.4.pdf): Variables, types, and flow control statements.
- [URScript Programming Language for e-Series](https://s3-eu-west-1.amazonaws.com/ur-support-site/115824/scriptManual_SW5.11.pdf)
- [Socket Script Example Document](https://s3-eu-west-1.amazonaws.com/ur-support-site/29983/Script%20command%20Examples.pdf)

- [Full Port List Overview](https://forum.universal-robots.com/t/overview-of-used-ports-on-local-host/8889)

## Real-Time Data Exchange (RTDE)

RTDE is a proprietary protocol for real-time data synchronization with Universal Robots controllers.

- [RTDE Overview](https://www.universal-robots.com/developer/communication-protocol/rtde/)
- [Complete I/O Documentation](https://www.universal-robots.com/articles/ur/interface-communication/real-time-data-exchange-rtde-guide/)
- [Python Documentation](https://docs.universal-robots.com/tutorials/communication-protocol-tutorials/rtde-python-client-guide.html)

> [!Note]
> The following libraries are not currently used in this project but are provided for reference:
>
> - RTDE Python Client Library ([GitHub](https://github.com/UniversalRobots/RTDE_Python_Client_Library))
> - `ur_rtde`: 3rd Party Standalone Python Library ([GitLab](https://gitlab.com/sdurobotics/ur_rtde)) ([PyPI](https://pypi.org/project/ur-rtde/#data))

## Additional Resources

> [!Note]  
> The following libraries are not currently used in this project but are provided for reference:
> - [UR DH Parameters for Kinematics and Dynamics](https://www.universal-robots.com/articles/ur/application-installation/dh-parameters-for-calculations-of-kinematics-and-dynamics/)
> - `urx`: 3rd Party Python Library ([GitHub](https://github.com/SintefManufacturing/python-urx))
> - `.NET SDK`: 3rd Party Licensed ([Website](https://underautomation.com/universal-robots)) ([GitHub](https://github.com/underautomation/UniversalRobots.NET))
