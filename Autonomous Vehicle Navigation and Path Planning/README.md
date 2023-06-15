# Autonomous Vehicle Navigation and Path Planning

The project work is the Robotics and Autonomous Systems Coursework, which involves navigation and path planning for an autonomous vehicle on a given environment using webots. The main objectives acheived in this project are : 
- Using RGB Cameras to navigate on the provided track (followed a very basic approach) and Detecting stop signs (in the upload version, used simple template mapping, but Yolo works best).
- When low battery, initiate <b>Path planning</b> to navigate to the charging area
   - Provided the GPS coordinates, the algorithm builds a mini map dynamically based on the vehicle's exploration.
   - Once the charging point is detected, plans and executes required actions to follows the path to the target location.

## Steps of Path Planning

1. Building a Mini Map
   - Using the GPS coordinates, rescale and transform the values to fit in a map of required size.
   - While exploring, keep recording the positon and updating it as the path.
   - Once reached any milestone or special places, like charging areas, mark them as per requirement.

   ![Alt text](Exploration%20-%20Building%20Mini%20Map.gif)


2. Finding the Shortest Path
   - If charging locations are known, excutes algorithms like Djksthras or A* to find the path.
   - If charging is area is not discovered, the vehicles keeps taking random turns
   - At every turn, it recalculates the shortest path

   ![Alt text](Path%20Planning.gif)





## Conclusion
Although the approaches and algorithms followed and implemented are no way close to state-of-the-art techniques, these gave a better understanding on the subject, power of computer vision, and autonomous systems in general. And, I'm a bit proud of what I was able to acheive for Path Planning, by dynamically building mini map from scratch.