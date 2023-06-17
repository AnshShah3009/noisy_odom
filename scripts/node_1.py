#! /usr/bin/env python
import rospy
from math import *
import numpy as np
from nav_msgs.msg import Odometry
import tf
from geometry_msgs.msg import Twist


last_odom = None
twist_flag = False

pose = [0.0, 0.0, 0.0]
a1 = 0.0
a2 = 0.0
a3 = 0.0
a4 = 0.0

new_odom_frame = ""
odom_frame = ""


def callback_twist(data):
    rospy.logdebug("twist callback")
    twist_flag = False
    v_x = data.linear.x
    v_y = data.linear.y
    v_z = data.linear.z
    w_z = data.angular.z
    w_y = data.angular.y
    w_x = data.angular.x
    if (v_x != 0.0 or v_y != 0.0 or v_z != 0 or w_x != 0 or w_y != 0 or w_z != 0):
        twist_flag = True
    return


def callback(data):
    global last_odom
    global new_odom_frame
    global odom_frame
    global pose
    global a1
    global a2
    global a3
    global a4

    q = [data.pose.pose.orientation.x,
         data.pose.pose.orientation.y,
         data.pose.pose.orientation.z,
         data.pose.pose.orientation.w]

    (r, p, theta2) = tf.transformations.euler_from_quaternion(q)

    if (last_odom == None):
        last_odom = data
        pose[0] = data.pose.pose.position.x
        pose[1] = data.pose.pose.position.y
        pose[2] = theta2
    elif (twist_flag and last_odom.header.stamp != data.header.stamp):
        # rospy.Subscriber("/husky_velocity_controller/cmd_vel", Twist)
        dx = data.pose.pose.position.x - last_odom.pose.pose.position.x
        dy = data.pose.pose.position.y - last_odom.pose.pose.position.y
        trans = sqrt(dx*dx + dy*dy)
        q = [last_odom.pose.pose.orientation.x,
             last_odom.pose.pose.orientation.y,
             last_odom.pose.pose.orientation.z,
             last_odom.pose.pose.orientation.w]

        (r, p, theta1) = tf.transformations.euler_from_quaternion(q)
        rot1 = atan2(dy, dx) - theta1
        rot2 = theta2-theta1-rot1

        sd_rot1 = a1*abs(rot1) + a2*trans
        sd_rot2 = a1*abs(rot2) + a2*trans
        sd_trans = a3*trans + a4*(abs(rot1) + abs(rot2))

        trans += np.random.normal(0, sd_trans*sd_trans)
        rot1 += np.random.normal(0, sd_rot1*sd_rot1)
        rot2 += np.random.normal(0, sd_rot2*sd_rot2)

        pose[0] += trans*cos(theta1+rot1)
        pose[1] += trans*sin(theta1+rot1)
        pose[2] += rot1 + rot2
        last_odom = data
    else:
        last_odom

    pub = rospy.Publisher("/new_odom_topic", Odometry, queue_size=10)
    # publish corrected odom
    odom_corrupted = Odometry()
    # odom_corrupted.child_frame_id = new_odom_frame
    # odom_corrupted.pose.pose.position.x = pose[0]
    # odom_corrupted.pose.pose.position.y = pose[1]
    # odom_corrupted.pose.pose.position.z = 0.0
    # odom_corrupted.pose.pose.orientation.x = 0.0
    # odom_corrupted.pose.pose.orientation.y = 0.0
    # odom_corrupted.pose.pose.orientation.z = sin(pose[2]/2.0)
    # odom_corrupted.pose.pose.orientation.w = cos(pose[2]/2.0)
    # odom_corrupted.twist.twist.linear.x = data.twist.twist.linear.x
    # odom_corrupted.twist.twist.linear.y = data.twist.twist.linear.y
    # odom_corrupted.twist.twist.linear.z = data.twist.twist.linear.z
    # odom_corrupted.twist.twist.angular.x = data.twist.twist.angular.x
    # odom_corrupted.twist.twist.angular.y = data.twist.twist.angular.y
    # odom_corrupted.twist.twist.angular.z = data.twist.twist.angular.z
    # odom_corrupted.header.stamp = data.header.stamp
    # odom_corrupted.header.frame_id = odom_frame
    # odom_corrupted.pose.covariance = data.pose.covariance
    # odom_corrupted.twist.covariance = data.twist.covariance

    odom_corrupted.child_frame_id = new_odom_frame
    odom_corrupted.pose.pose.position.x = data.pose.pose.position.x
    odom_corrupted.pose.pose.position.y = data.pose.pose.position.y
    odom_corrupted.pose.pose.position.z = data.pose.pose.position.z
    odom_corrupted.pose.pose.orientation.x = 0.0
    odom_corrupted.pose.pose.orientation.y = 0.0
    odom_corrupted.pose.pose.orientation.z = sin(
        data.pose.pose.orientation.z/2.0)
    odom_corrupted.pose.pose.orientation.w = cos(
        data.pose.pose.orientation.z/2.0)
    odom_corrupted.twist.twist.linear.x = data.twist.twist.linear.x
    odom_corrupted.twist.twist.linear.y = data.twist.twist.linear.y
    odom_corrupted.twist.twist.linear.z = data.twist.twist.linear.z
    odom_corrupted.twist.twist.angular.x = data.twist.twist.angular.x
    odom_corrupted.twist.twist.angular.y = data.twist.twist.angular.y
    odom_corrupted.twist.twist.angular.z = data.twist.twist.angular.z
    odom_corrupted.header.stamp = data.header.stamp
    odom_corrupted.header.frame_id = odom_frame
    odom_corrupted.pose.covariance = data.pose.covariance
    odom_corrupted.twist.covariance = data.twist.covariance
    pub.publish(odom_corrupted)

    # publish tf
    br = tf.TransformBroadcaster()
    br.sendTransform((pose[0] - data.pose.pose.position.x, pose[1] - data.pose.pose.position.y, 0),
                     tf.transformations.quaternion_from_euler(
                         0, 0, pose[2] - theta2),
                     data.header.stamp,
                     odom_frame,
                     new_odom_frame)

    twist_flag = False


if __name__ == '__main__':

    rospy.init_node('noisy_odometry', anonymous=True)

    # alpha 1 is degree/degree
    if rospy.has_param("~alpha1"):
        a1 = rospy.get_param("~alpha1")

    else:
        rospy.logwarn("alpha1 is set to default")
        a1 = 0.05

    # alpha 2 is degree/m
    if rospy.has_param("~alpha2"):
        a2 = rospy.get_param("~alpha2")

    else:
        a2 = 10.0*pi/180.0
        rospy.logwarn("alpha2 is set to default")

    # alpha 3 is m/meter
    if rospy.has_param("~alpha3"):
        a3 = rospy.get_param("~alpha3")

    else:
        a3 = 0.05
        rospy.logwarn("alpha3 is set to default")

    # alpha 4 is m/degree
    if rospy.has_param("~alpha4"):
        a4 = rospy.get_param("~alpha4")

    else:
        a4 = 0.01
        rospy.logwarn("alpha4 is set to default")

    # get odom topic
    if rospy.has_param("~old_odom_topic"):
        odom_topic = rospy.get_param("~old_odom_topic")

    else:
        odom_topic = "/odometry/filtered"

    # get base frame
    if rospy.has_param("~new_odom_frame"):
        new_odom_frame = rospy.get_param("~new_odom_frame")

    else:
        new_odom_frame = "base_link"

    # get base frame
    if rospy.has_param("~odom_frame"):
        odom_frame = rospy.get_param("~odom_frame")

    else:
        odom_frame = "odom_corrupted"

    rospy.Subscriber("/husky_velocity_controller/cmd_vel",
                     Twist, callback=callback_twist)
    rospy.Subscriber(odom_topic, Odometry, callback)
    rospy.spin()
