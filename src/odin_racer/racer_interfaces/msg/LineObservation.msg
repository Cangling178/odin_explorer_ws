# Atomic camera observation: acquisition stamp/frame are carried by path.header.
# image_valid certifies projection/image health, not visibility of a line.
nav_msgs/Path path
bool image_valid
bool path_valid
float32 confidence
string reason
bool corner_valid
geometry_msgs/Point corner
geometry_msgs/Vector3 exit_direction
uint8 exits
