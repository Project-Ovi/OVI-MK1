# OVI-MK1

# Introduction
## Background
As production demands surge, factories are tasked with producing goods at an ever-increasing pace. This rapid output necessitates rigorous quality checking and sorting procedures. With each new batch, the pressure intensifies to maintain high standards. Implementing stringent quality control measures becomes vital to meet the demands of the near future, ensuring customer satisfaction and upholding the reputation of the brand in the face of escalating production volumes.

## Our goal
At OVI Robotics, we've developed an advanced system employing computer vision to recognize objects by colour and relocate them precisely. Our focus is on creating a reliable solution for sorting goods and maintaining quality control. We believe in the power of innovation to address real-world challenges efficiently. Our technology aims to streamline processes and minimize errors, offering industries a dependable tool for optimizing operations. With adaptability at its core, our system can cater to various sectors, promising enhanced efficiency and productivity. At OVI Robotics, we're committed to delivering practical, cutting-edge solutions that drive positive change in the world of automation.

# Inner workings
## Mechanical level
Our product showcases a dynamic design featuring two potent linear actuators, each delivering an impressive force of 1kN, stationed on a sturdy yet eco-friendly wooden platform, and maneuvered by a reliable motor. Adding to its functionality, the robotic arm is equipped with a high-quality gripper crafted from durable polylactide material, driven by a precise 9g servo motor. This amalgamation of robust components underscores our dedication to efficiency and reliability, ensuring optimal performance in various applications.

## Electronics level
The system employs affordable and easily accessible electronic components to ensure a competitive pricing strategy. Despite comprising basic transistors and Arduino NANOs, its electronics boast reliability. Every electrical connection undergoes meticulous manual soldering to enhance durability, while extensive coding efforts embedded within the NANOs contribute to its cost-effectiveness and dependability. Furthermore, opting for widely available components over custom-made ones minimizes environmental impact by reducing pollution and electronic waste. This approach not only underscores the system's affordability and reliability but also aligns with sustainability goals by promoting resource efficiency and eco-conscious manufacturing practices.

## Programming level
The programming behind this robot stands as a testament to ingenuity and precision. Employing a bespoke algorithm crafted in-house, it boasts a remarkable capability to discern objects based on their color. Upon identification, the intricately designed code seamlessly dispatches commands via the UART protocol to a master microcontroller. This masterful orchestration extends further as the microcontroller employs the I2C protocol to communicate with each slave, choreographing precise movements to fulfill its objectives.

Moreover, the application interface exudes sophistication, offering a comprehensive web interface that provides real-time insights into the robot's operations. Notably, users can seamlessly toggle its functionalities on and off. This feat is achieved through a meticulously constructed framework utilizing the TCP/IP protocol, facilitating seamless data transmission from the microcontrollers to a cutting-edge GO web server. The server, in turn, harnesses a blend of HTTP and WebSocket protocols to deliver vital information, ensuring a seamless user experience and unparalleled control over the robot's operations.

[Architecture](!assets/OVI-ARCHITECTURE.jpg)
