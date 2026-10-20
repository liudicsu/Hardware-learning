"""pick_place.py: a collision-free pick and place with MoveIt 2 (MoveItPy) on the Panda arm.

The scene: a table, a 4 x 4 x 8 cm block on the right, and a 25 cm wall between it and the
place position on the left. Free moves are planned by OMPL (RRTConnect), the approach and
retreat as straight lines by Pilz LIN. The block is attached to the hand while it is
carried, so MoveIt keeps the block, not just the arm, clear of the wall. Needs bringup.launch.py
running. Usage: python3 pick_place.py
"""
import os
import time

import rclpy
from geometry_msgs.msg import Pose, PoseStamped
from moveit.core.robot_state import RobotState
from moveit.planning import MoveItPy, PlanRequestParameters
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_msgs.msg import AttachedCollisionObject, CollisionObject
from shape_msgs.msg import SolidPrimitive

HERE = os.path.dirname(os.path.abspath(__file__))
FINGER = 0.1034            # panda_hand origin to the fingertips, m
BLOCK = (0.04, 0.04, 0.08)
PICK, PLACE = (0.5, -0.25), (0.5, 0.25)
WALL = (0.30, 0.02, 0.25)   # length along x, thickness along y, height; centred at x = 0.5, y = 0


def box(name, size, xyz, op=CollisionObject.ADD):
    obj = CollisionObject()
    obj.id, obj.header.frame_id, obj.operation = name, "panda_link0", op
    prim = SolidPrimitive(type=SolidPrimitive.BOX, dimensions=list(size))
    pose = Pose()
    pose.position.x, pose.position.y, pose.position.z = xyz
    pose.orientation.w = 1.0
    obj.primitives, obj.primitive_poses = [prim], [pose]
    return obj


def hand_pose(x, y, z):
    """panda_hand pointing straight down with the fingertips at (x, y, z)."""
    p = PoseStamped()
    p.header.frame_id = "panda_link0"
    p.pose.position.x, p.pose.position.y, p.pose.position.z = x, y, z + FINGER
    q = p.pose.orientation
    q.x, q.y, q.z, q.w = 0.9238795, -0.3826834, 0.0, 0.0     # down (w defaults to 1: set it)
    return p


class Robot:
    def __init__(self):
        config = (MoveItConfigsBuilder("moveit_resources_panda")
                  .robot_description(file_path="config/panda.urdf.xacro",
                                     mappings={"ros2_control_hardware_type": "mock_components"})
                  .robot_description_semantic(file_path="config/panda.srdf")
                  .trajectory_execution(file_path="config/gripper_moveit_controllers.yaml")
                  .planning_pipelines(pipelines=["ompl", "pilz_industrial_motion_planner"])
                  .moveit_cpp(file_path=os.path.join(HERE, "moveit_py.yaml"))
                  .to_moveit_configs()).to_dict()
        self.moveit = MoveItPy(node_name="pick_place", config_dict=config)
        self.arm = self.moveit.get_planning_component("panda_arm")
        self.hand = self.moveit.get_planning_component("hand")
        self.scene = self.moveit.get_planning_scene_monitor()
        self.params = {k: PlanRequestParameters(self.moveit, k) for k in ("ompl_rrtc", "pilz_lin")}
        time.sleep(3.0)          # let MoveItPy's action clients connect to the controllers

    def run(self, label, group, planner, may_fail=False, **goal):
        tries = 3 if planner == "ompl_rrtc" else 1      # RRTConnect is random: try again if one search fails
        for _ in range(tries):
            group.set_start_state_to_current_state()
            group.set_goal_state(**goal)
            plan = group.plan(single_plan_parameters=self.params[planner])
            if plan:
                break
        if not plan:
            print(f"FAIL {label}: no plan ({planner}, {tries} tries)")
            if may_fail:
                return None
            raise SystemExit(1)
        traj = plan.trajectory
        status = self.moveit.execute(traj, controllers=[])
        if not status:
            print(f"FAIL {label}: execution {status.status}")
            raise SystemExit(1)
        print(f"ok   {label:24s} {planner:9s}  {len(traj):3d} waypoints, execution {status.status}")
        return traj

    def fingertips(self):
        with self.scene.read_only() as scene:
            scene.current_state.update()
            t = scene.current_state.get_global_link_transform("panda_hand")
        return t[0, 3], t[1, 3], t[2, 3] - FINGER

    def gripper(self, label, width):
        state = RobotState(self.moveit.get_robot_model())
        state.set_joint_group_positions("hand", [width / 2])
        return self.run(label, self.hand, "ompl_rrtc", robot_state=state)

    def carry_report(self, traj, grip_z):
        """Check the carry move twice: MoveIt's own collision check of every waypoint (with the
        block attached), and the lowest point of the block wherever it was above the wall."""
        with self.scene.read_only() as scene:
            valid = scene.is_path_valid(traj, "panda_arm", False, [])
        lowest = None
        for i in range(len(traj)):
            state = traj[i]
            state.update()                       # compute the link poses for this waypoint
            t = state.get_global_link_transform("panda_hand")
            above = (abs(t[0, 3] - 0.5) < (WALL[0] + BLOCK[0]) / 2 and       # block overlaps the wall
                     abs(t[1, 3]) < (WALL[1] + BLOCK[1]) / 2)
            if above:
                z = t[2, 3] - FINGER - grip_z    # fingertips are grip_z above the block's bottom
                lowest = z if lowest is None else min(lowest, z)
        return valid, lowest


def main():
    rclpy.init()
    r = Robot()
    with r.scene.read_write() as scene:
        for obj in (box("table", (1.2, 1.2, 0.04), (0.4, 0.0, -0.03)),
                    box("wall", WALL, (0.5, 0.0, WALL[2] / 2)),
                    box("block", BLOCK, (PICK[0], PICK[1], BLOCK[2] / 2))):
            scene.apply_collision_object(obj)
        scene.current_state.update()
    print(f"scene: table, wall {WALL[2]:.2f} m high at y = 0, block at ({PICK[0]:.2f}, {PICK[1]:+.2f}) -> place at ({PLACE[0]:.2f}, {PLACE[1]:+.2f})")
    grip_z = BLOCK[2] - 0.02          # fingertips 2 cm below the block top: the palm stays clear of it
    r.run("ready", r.arm, "ompl_rrtc", configuration_name="ready")
    r.gripper("open gripper", 0.08)
    r.run("above the block", r.arm, "ompl_rrtc", pose_stamped_msg=hand_pose(*PICK, grip_z + 0.12), pose_link="panda_hand")
    r.run("straight down to it", r.arm, "pilz_lin", pose_stamped_msg=hand_pose(*PICK, grip_z), pose_link="panda_hand")
    print("     fingertips at (%.3f, %+.3f, %.3f) m" % r.fingertips())
    aco = AttachedCollisionObject(link_name="panda_hand", object=box("block", BLOCK, (0, 0, 0)),
                                  touch_links=["panda_hand", "panda_leftfinger", "panda_rightfinger"])
    aco.object.header.frame_id = "panda_link0"
    aco.object.primitive_poses[0].position.x, aco.object.primitive_poses[0].position.y = PICK
    aco.object.primitive_poses[0].position.z = BLOCK[2] / 2       # where the block really is
    with r.scene.read_write() as scene:
        scene.process_attached_collision_object(aco)
        scene.current_state.update()
    r.gripper("close on the block", BLOCK[0])
    print("     block attached to panda_hand")
    r.run("straight up", r.arm, "pilz_lin", pose_stamped_msg=hand_pose(*PICK, grip_z + 0.12), pose_link="panda_hand")
    carry = r.run("over the wall", r.arm, "ompl_rrtc", pose_stamped_msg=hand_pose(*PLACE, grip_z + 0.12), pose_link="panda_hand")
    valid, low = r.carry_report(carry, grip_z)     # checked now, while the block is still attached
    r.run("straight down to place", r.arm, "pilz_lin", pose_stamped_msg=hand_pose(*PLACE, grip_z + 0.002), pose_link="panda_hand")
    print("     fingertips at (%.3f, %+.3f, %.3f) m" % r.fingertips())
    r.gripper("open gripper", 0.08)
    aco.object.operation = CollisionObject.REMOVE
    with r.scene.read_write() as scene:
        scene.process_attached_collision_object(aco)
        scene.current_state.update()
    print("     block detached, left in the scene")
    r.run("straight up", r.arm, "pilz_lin", pose_stamped_msg=hand_pose(*PLACE, grip_z + 0.12), pose_link="panda_hand")
    r.run("ready", r.arm, "ompl_rrtc", configuration_name="ready")
    print(f"carry move, block attached: MoveIt collision check of all {len(carry)} waypoints: {'valid' if valid else 'IN COLLISION'}")
    if low is None:
        print("     route: around the end of the wall")
    else:
        print(f"     route: over the wall, block bottom at least {low:.3f} m up (wall top {WALL[2]:.2f} m)")
    with r.scene.read_only() as scene:
        b = scene.get_frame_transform("block")
    print(f"block now at ({b[0, 3]:.3f}, {b[1, 3]:+.3f}, {b[2, 3]:.3f}) m")
    print("and a goal inside the wall:")
    r.run("fingertips inside the wall", r.arm, "ompl_rrtc", may_fail=True,
          pose_stamped_msg=hand_pose(0.5, 0.0, 0.10), pose_link="panda_hand")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
