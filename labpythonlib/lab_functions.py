# =================================================
#	Course  :   legged robots
# 	Alumno  :   jhon charaja
# 	Info	:	useful functions for robotics labs
# =================================================

# ======================
#   required libraries
# ======================
import os
import numpy as np
import pinocchio as pin
from copy import copy
from numpy.linalg import inv
from numpy import multiply as mul
from numpy import matmul as mx
from numpy import transpose as tr
import pandas as pd


# =============
#   functions
# =============
def sinusoidal_reference_generator(q0, a, f, t_change, t):
    """
    @info: generates a sine signal for "t_change" seconds then change to constant reference.

    @inputs: 
    ------
        - q0: initial joint/cartesian position
        - a: amplitude
        - f: frecuency [hz]
        - t_change: change from sinusoidal to constant reference [sec]
        - t: simulation time [sec]
    @outputs:
    -------
        - q, dq, ddq: joint/carteisan position, velocity and acceleration
    """
    w = 2*np.pi*f               # [rad/s]
    if t<=t_change:
        q = q0 + a*np.sin(w*t)      # [rad]
        dq = a*w*np.cos(w*t)        # [rad/s]
        ddq = -a*w*w*np.sin(w*t)    # [rad/s^2]
    else:
        q = q0 + a*np.sin(w*t_change)   # [rad]
        dq = 0                          # [rad/s]
        ddq = 0                         # [rad/s^2]
    return q, dq, ddq

def step_reference_generator(q0, a, t_step, t):
    """
    @info: generate a constant reference.

    @inputs:
    ------
        - q0: initial joint/cartesian position
        - a: constant reference
        - t_step: start step [sec]
        - t: simulation time [sec]
    @outputs:
    -------
        - q, dq, ddq: joint/carteisan position, velocity and acceleration
    """
    if t>=t_step:
        q = q0 + a  # [rad]
        dq = 0      # [rad/s]
        ddq = 0     # [rad/s^2]
    else:
        q = copy(q0)    # [rad]
        dq = 0          # [rad/s]
        ddq = 0         # [rad/s^2]            
    return q, dq, ddq

def circular_trayectory_generator(t,radius=0.05, z_amp=0.02, rpy_amp=np.zeros(3), freq_xyz=0.1, freq_rpy=0.1):
    """
    @info generate points of a circular trayectory.

    @inputs:
    -------
        - t : simulation time [s]
        - radius: radius of circular trajectory on xy-plane [m]
        - z_amp: amplitude of sinusoidal trajectory on z-plane [m]
        - freq: frequency [hz]

    Outpus:
    -------
        - pose: end-effector position (xyz) and orientation (rpy)   
        - dpose: end-effector velocity (xyz) and dorientation (rpy)        
    """

    # Parameters of circular trayetory     
    w_xyz = 2*np.pi*freq_xyz   # angular velocity [rad/s]
    w_rpy = 2*np.pi*freq_rpy   # angular velocity [rad/s]
    pos0 = np.array([0.5, 0.0, 0.0]) # initial states

    # xyz position
    pos = np.array([pos0[0]+radius*np.cos(w_xyz*(t)), pos0[1]+radius*np.sin(w_xyz*(t)), pos0[2]+z_amp*np.sin(w_xyz*t)]) 
    # xyz velocity
    vel = np.array([radius*(-w_xyz)*np.sin(w_xyz*(t)), radius*(+w_xyz)*np.cos(w_xyz*(t)), z_amp*w_xyz*np.cos(w_xyz*t)])
    # rpy orientation
    R  = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])
    rpy = rot2rpy(R) + rpy_amp*np.sin(w_rpy*t)
    drpy = rpy_amp*w_rpy*np.cos(w_rpy*t)
    
    # return end-effector pose and its time-derivative
    return np.concatenate((pos, rpy), axis=0), np.concatenate((vel, drpy), axis=0)

def reference_trajectory(x_des, dx_des, x_ref0, dx_ref0, dt):
    """
    Info: Generates a reference trajectory based on a desired trajectory.

    Inputs: 
    ------
        - x_des:  desired trajectory
        - x_ref0: initial conditions of x_ref
        - dt:     sampling time 
    """
    psi = 1 # damping factor
    wn  = 4 # natural frecuency

    k0 = wn*wn
    k1 = 2*psi*wn
    # compute ddx_ref
    ddx_ref = np.multiply(dx_des,k1) + np.multiply(x_des,k0) -  np.multiply(dx_ref0,k1) - np.multiply(x_ref0,k0)
    # double integration 
    dx_ref = dx_ref0 + dt*ddx_ref
    x_ref  = x_ref0  + dt*dx_ref

    return x_ref, dx_ref, ddx_ref

def update_learning_rate(x, x_min=0.1, x_max=0.7, y_min=0.01, y_max=1):    
    """
    @info function to update learning rate
    @inputs:
    --------
        - x: input signal
        - x_min: behind this value the output is 1
        - x_mx: above this value the output is 0
    """
    #x = np.linspace(0, 1.2, 100)
    y = np.piecewise(x, [x < x_min, (x >=x_min)* (x< x_max),              x >= x_max], \
                        [y_max,         lambda x: (x_min-x)/(x_max-x_min)+1,  y_min ])
    
    return y
    
def tl(array):
    """
    @info: add element to list
    """
    return array.tolist()    

def rot2axisangle(R):
    """
    @info: computes axis/angle values from rotation matrix

    @inputs:
    --------
        - R: rotation matrix
    @outputs:
    --------
        - angle: angle of rotation
        - axis: axis of rotation
    """
    R32 = R[2,1]
    R23 = R[1,2]
    R13 = R[0,2]
    R31 = R[2,0]
    R21 = R[1,0]
    R12 = R[0,1]
    tr  = np.diag(R).sum()
    # angle
    angle = np.arctan2(0.5*np.sqrt( np.power(R21-R12,2)+np.power(R31-R13,2)+np.power(R32-R23,2)), 0.5*(tr-1))
    # axis
    if angle!=0:
        rx = (R32-R23)/(2*np.sin(angle))
        ry = (R13-R31)/(2*np.sin(angle))
        rz = (R21-R12)/(2*np.sin(angle))
        axis = np.array([rx, ry, rz]) 
    else:
        axis = np.zeros(3)
    return angle, axis

def angleaxis2rot(w):
    """
    @info: computes rotation matrix from angle/axis representation
    @inputs:
    ------
        -
    """
    print("development...")

def rot2quat(R):
    """
    @info: computes quaternion from rotation matrix
    
    @input:
    ------
        - R: Rotation matrix
    @output:
    -------
        - Q: Quaternion [w, ex, ey, ez]
    """
    dEpsilon = 1e-6
    Q = np.zeros(4)
    
    Q[0] = 0.5*np.sqrt(R[0,0]+R[1,1]+R[2,2]+1.0)
    if ( np.fabs(R[0,0]-R[1,1]-R[2,2]+1.0) < dEpsilon ):
        Q[1] = 0.0
    else:
        Q[1] = 0.5*np.sign(R[2,1]-R[1,2])*np.sqrt(R[0,0]-R[1,1]-R[2,2]+1.0)
    if ( np.fabs(R[1,1]-R[2,2]-R[0,0]+1.0) < dEpsilon ):
        Q[2] = 0.0
    else:
        Q[2] = 0.5*np.sign(R[0,2]-R[2,0])*np.sqrt(R[1,1]-R[2,2]-R[0,0]+1.0)
    if ( np.fabs(R[2,2]-R[0,0]-R[1,1]+1.0) < dEpsilon ):
        Q[3] = 0.0
    else:
        Q[3] = 0.5*np.sign(R[1,0]-R[0,1])*np.sqrt(R[2,2]-R[0,0]-R[1,1]+1.0)

    return Q      

def quatError(Qdes, Qmed):
    """
    @info: computes quaterion error (Q_e = Q_d . Q_m*).

    @inputs:
    ------
        - Qdes: desired quaternion
        - Q : measured quaternion

    @output:
    -------
        - Qe : quaternion error    
    """

    we = Qdes[0]*Qmed[0] + np.dot(Qdes[1:4].T,Qmed[1:4]) - 1
    e  = -Qdes[0]*Qmed[1:4] + Qmed[0]*Qdes[1:4] - np.cross(Qdes[1:4], Qmed[1:4])
    Qe = np.array([ we, e[0], e[1], e[2] ])

    return Qe               

def axisangle_error(R_des, R_med):
    """
    @info: computes orientation error and represent with angle/axis.
    @inputs:
    ------
        - R_d: desired orientation
        - R_m: measured orientation
    @outputs:
    --------
        - e_o: orientation error        
    """
    R_e = R_med.T.dot(R_des)
    angle_e, axis_e = rot2axisangle(R_e)
    e_o = R_med.dot(angle_e*axis_e) # w.r.t world frame
    return e_o

def rpy2rot(rpy):
    """
    @info: computes rotation matrix from roll, pitch, yaw (ZYX euler angles) representation
    
    @inputs:
    -------
        - rpy[0]: rotation in z-axis (roll)
        - rpy[1]: rotation in y-axis (pitch)
        - rpy[2]: rotation in x-axis (yaw)
    @outputs:
    --------
        - R: rotation matrix        
    """
    Rz = np.array([[ np.cos(rpy[0])  ,  -np.sin(rpy[0]) ,      0],
                [    np.sin(rpy[0])  ,   np.cos(rpy[0]) ,      0],
                [           0      ,        0       ,      1]])

    Ry = np.array([[np.cos(rpy[1])   ,   0   ,   np.sin(rpy[1])],
                [      0            ,   1   ,           0],
                [  -np.sin(rpy[1])   ,   0   ,   np.cos(rpy[1])]])

    Rx =  np.array([ [   1   ,    0           ,        0], 
                        [0   ,    np.cos(rpy[2]) ,  -np.sin(rpy[2])],
                        [0   ,    np.sin(rpy[2]) ,   np.cos(rpy[2])]])

    R =  np.dot(np.dot(Rz, Ry), Rx)
    return R

def rot2rpy(R):
    """
    @info: computes roll, pitch, yaw (ZYX euler angles) from rotation matrix
    
    @inputs:
    -------
        - R: rotation matrix        
    @outputs:
    --------
        - rpy[0]: rotation in z-axis (roll)
        - rpy[1]: rotation in y-axis (pitch)
        - rpy[2]: rotation in x-axis (yaw)
    """
    R32 = R[2,1]
    R31 = R[2,0]
    R33 = R[2,2]
    R21 = R[1,0]
    R11 = R[0,0]
    rpy = np.zeros(3)    
    rpy[1] = np.arctan2(-R31, np.sqrt(R32*R32 + R33*R33))
    rpy[0] = np.arctan2(R21/np.cos(rpy[1]), R11/np.cos(rpy[1]))
    rpy[2] = np.arctan2(R32/np.cos(rpy[1]), R33/np.cos(rpy[1]))

    return rpy

def rot2rpy_unwrapping(R, rpy_old):
    """
    @info: computes roll, pitch, yaw (ZYX euler angles) from rotation matrix
    
    @inputs:
    -------
        - R: rotation matrix        
    @outputs:
    --------
        - rpy[0]: rotation in z-axis (roll)
        - rpy[1]: rotation in y-axis (pitch)
        - rpy[2]: rotation in x-axis (yaw)
    """
    R32 = R[2,1]
    R31 = R[2,0]
    R33 = R[2,2]
    R21 = R[1,0]
    R11 = R[0,0]
    rpy = np.zeros(3)    
    rpy[1] = np.arctan2(-R31, np.sqrt(R32*R32 + R33*R33))
    rpy[0] = np.arctan2(R21/np.cos(rpy[1]), R11/np.cos(rpy[1]))
    rpy[2] = np.arctan2(R32/np.cos(rpy[1]), R33/np.cos(rpy[1]))

    for i in range(3):
        if(rpy[i]<=(rpy_old[i]-np.pi)):
            rpy[i] +=2*np.pi
        elif(rpy[i]>=(rpy_old[i]+np.pi)):
            rpy[i] -=2*np.pi 
    return rpy 


def rpy2angularVel(rpy, drpy):
    """
    @info: compute angular velocity (w) from euler angles (roll, pitch and yaw) and its derivaties
    @inputs:
    -------
        - rpy[0]: rotation in z-axis (roll)
        - rpy[1]: rotation in y-axis (pitch)
        - rpy[2]: rotation in x-axis (yaw)
        - drpy[0]: rotation ratio in z-axis
        - drpy[1]: rotation ratio in y-axis
        - drpy[2]: rotation ratio in x-axis
    @outputs:
    --------
        - w: angular velocity
    """        
    E0 = np.array(  [[0, -np.sin(rpy[0]), np.cos(rpy[0])*np.cos(rpy[1])], \
                    [0,   np.cos(rpy[0]), np.sin(rpy[0])*np.cos(rpy[1])], \
                    [1,         0,          -np.sin(rpy[1])       ]])
    
    w = np.dot(E0, drpy)
    return w

def angularVel2rpy(w, rpy):
    """
    @info: compute angular velocity (w) from euler angles (roll, pitch and yaw) and its derivaties
    @inputs:
    -------
        - rpy[0]: rotation in z-axis (roll)
        - rpy[1]: rotation in y-axis (pitch)
        - rpy[2]: rotation in x-axis (yaw)
        - w: angular velocity
    @outputs:
    --------
        - drpy[0]: rotation ratio in z-axis
        - drpy[1]: rotation ratio in y-axis
        - drpy[2]: rotation ratio in x-axis

    """        
    E0 = np.array(  [[0, -np.sin(rpy[0]), np.cos(rpy[0])*np.cos(rpy[1])], \
                    [0,   np.cos(rpy[0]), np.sin(rpy[0])*np.cos(rpy[1])], \
                    [1,         0,          -np.sin(rpy[1])       ]])
    
    drpy = np.dot(inv(E0), w)
    return drpy

def rpy2angularAccel(rpy, drpy, ddrpy):
    """
    @info: compute angular velocity (w) from euler angles (roll, pitch and yaw) and its derivaties
    @inputs:
    -------
        - rpy[0]: rotation in z-axis (roll)
        - rpy[1]: rotation in y-axis (pitch)
        - rpy[2]: rotation in x-axis (yaw)
        - drpy[0]: rotation speed in z-axis
        - drpy[1]: rotation speed in y-axis
        - drpy[2]: rotation speed in z-axis
        - ddrpy[0]: rotation acceleration in z-axis
        - ddrpy[1]: rotation acceleration in y-axis
        - ddrpy[2]: rotation acceleration in x-axis        
    @outputs:
    --------
        - dw: angular acceleration
    """        
    E0 = np.array(  [[0, -np.sin(rpy[0]), np.cos(rpy[0])*np.cos(rpy[1])], \
                    [0,   np.cos(rpy[0]), np.sin(rpy[0])*np.cos(rpy[1])], \
                    [1,         0,          -np.sin(rpy[1])       ]])
    
    E1 = np.array( [[0, -np.cos(rpy[0])*drpy[0], -np.sin(rpy[0])*drpy[0]*np.cos(rpy[1])-np.cos(rpy[0])*np.sin(rpy[1])*drpy[1]], \
                    [0, -np.sin(rpy[0])*drpy[0],  np.cos(rpy[0])*drpy[0]*np.cos(rpy[1])-np.sin(rpy[0])*np.sin(rpy[1])*drpy[1]], \
                    [0,         0,               -np.cos(rpy[1])*drpy[1]   ]])
    dw = np.dot(E1, drpy) + np.dot(E0, ddrpy)
    return dw

def damped_pinv(M, lambda_=0.0000001):
    """
    @info: computes damped pseudo-inverse

    @inputs:
    ------
        - M: matrix
        - lambda_: damping term (optional)
    @outputs:
    -------
        - M_damped_inv: damped psedu-inverse of M            
    """
    ntask = M.shape[0]
    M_damped_inv =  np.dot(M.T, np.linalg.inv(np.dot(M, M.T) + lambda_*np.eye(ntask)))
    return M_damped_inv

class Robot(object):
    """
    @info: Class to load the .urdf of a robot. For thism Pinocchio library is used

    @methods:
        - foward_kinematics(q0)
        - geometric_jacobian(q0)
        - analityc_jacobian(q0)
        - geometric_jacobian_time_derivative(q0, dq0)
        - twist(q0, dq0)
        - send_control_command(u)
        - inverse_kinematics_position(x_des, q0)
        - inverse_kinematics_pose(x_des, R_des, q0)
    """    
    def __init__(self, q0, dq0, dt, urdf_path):
        # robot object
        self.robot = pin.robot_wrapper.RobotWrapper.BuildFromURDF(urdf_path)
        # degrees of freedom
        self.ndof = self.robot.model.nq
        # joint configuration: position, velocity and acceleration
        self.q = copy(q0)                
        self.dq = copy(dq0)               
        self.ddq = np.zeros(self.ndof)
        # inertia matrix
        self.M = np.zeros([self.ndof, self.ndof])
        # nonlinear effects vector
        self.b = np.zeros(self.ndof)
        # gravivty effects vector
        self.g = np.zeros(self.ndof)
        # vector of zeros
        self.z = np.zeros(self.ndof)
        # sampling time
        self.dt = copy(dt)     
        # frame id: end-effector
        self.frame_ee = self.robot.model.getFrameId('ee_link') 
        # end-effector: position, velocity and acceleration
        self.p = np.zeros(3)
        self.dp = np.zeros(3)
        self.ddp = np.zeros(3)
        # end-effector: orientation
        self.R = np.zeros([3,3])
        # end-effector: angular velocity and acceleration
        self.w = np.zeros(3)
        self.dw = np.zeros(3)
        # initial configuration: position (p) and orientation (R)
        self.p, self.R = self.forward_kinematics(self.q)
        # initial configuration: linear (dp) and angular (w) velocity
        self.dp, self.w = self.twist(self.q, self.dq)
        # initial configuration: linear (ddp) and angular (dw) acceleration
        self.ddp, self.dw = self.dtwist(self.q, self.dq, self.ddq)
        # initial configuration: dynamic model
        self.M = pin.crba(self.robot.model, self.robot.data, self.q)
        self.b = pin.rnea(self.robot.model, self.robot.data, self.q, self.dq, self.z)
        self.g = pin.rnea(self.robot.model, self.robot.data, self.q, self.z, self.z)        
  
    def forward_kinematics(self, q0):
        """
        @info: computes the position (xyz) and rotation (R) of the end-effector.

        @inputs:
        -----
            - q0: joint configuration (rad)
        
        @outputs:
        -------
            - p: position of the end-effector (m).
            - R: rotation matrix of the end-effector (rad).
        """      
        # commpute forward kinematics
        pin.forwardKinematics(self.robot.model, self.robot.data, q0) 
        # get position and orientation       
        p = pin.updateFramePlacement(self.robot.model, self.robot.data, self.frame_ee).translation
        R = pin.updateFramePlacement(self.robot.model, self.robot.data, self.frame_ee).rotation
        return p, R

    def analityc_jacobian(self, q0):
        """
        @info: computes analityc jacobian matrix of robot end-effector.
                The orientation is represented with quaternions.
        """
        print("development... ")

    def geometric_jacobian(self, q0):
        """
        @info: computes geometric jacobian matrix of the end-effector.

        @inputs:
        ------
            - q0: joint configuration (rad)
        @outputs:
        -------
            - J: geometric jacobian matrix            
        """
        pin.computeJointJacobians(self.robot.model, self.robot.data, q0)
        J = pin.getFrameJacobian(self.robot.model, self.robot.data, self.frame_ee, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED)
        return J
    
    def geometric_jacobian_time_derivative(self, q0, dq0):
        """
        @info: computes time derivative of jacobian matrix of the end-effector.

        @inputs:
        ------
            - q0: joint position/configuration (rad)
            - dq0: joint velocity (rad/s)
        @outputs:
        -------
            - dJ: time derivative of jacobian matrix            
        """        
        # compute time-derivative of jacobian matrix (end-effector frame)
        pin.computeJointJacobiansTimeVariation(self.robot.model, self.robot.data, q0, dq0)
        dJ = pin.getFrameJacobianTimeVariation(self.robot.model, self.robot.data, self.frame_ee, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED)
        return dJ
    
    def twist(self, q0, dq0):
        """
        @info: computes linear and angular velocity of robot end-effector
        @inputs:
        -------
            - q0: joint configuration/position (rad)
            - dq0: joint velocity (rad/s)
        @outputs:
        --------
            - v: linear velocity (m/s)
            - w: angular velocity (rad/s)             
        """
        J = self.geometric_jacobian(q0)
        v = J[0:3,0:6].dot(dq0)
        w = J[3:6,0:6].dot(dq0)
        return v, w
    
    def dtwist(self, q0, dq0, ddq0):
        """
        @info: computes linear and angular acceleration of robot end-effector
        @inputs:
        -------
            - q0: joint configuration/position (rad)
            - dq0: joint velocity (rad/s)
            - ddq0: joint acceleration (rad/s^2)
        @outputs:
        --------
            - a: linear acceleration (m/s^2)
            - dw: angular acceleration (rad/s^2)             
        """      
        J = self.geometric_jacobian(q0)
        dJ = self.geometric_jacobian_time_derivative(q0, dq0)
        a = dJ[0:3,0:6].dot(dq0) + J[0:3,0:6].dot(ddq0)
        dw = dJ[3:6,0:6].dot(dq0) + J[3:6,0:6].dot(ddq0)
        return a, dw

    def send_control_command(self, u):
        """
        @info: uses the control signal (u) to compute forward dynamics (ddq). 
              Then update joint configuration (q) and end-effector pose (p, R)
        """
        tau = np.squeeze(np.asarray(u))
        # compute dynamics model
        self.M = pin.crba(self.robot.model, self.robot.data, self.q)
        self.b = pin.rnea(self.robot.model, self.robot.data, self.q, self.dq, self.z)
        self.g = pin.rnea(self.robot.model, self.robot.data, self.q, self.z, self.z)
        # forward dynamics
        self.ddq = np.linalg.inv(self.M).dot(tau-self.b)
        # update joint position/configuration
        self.dq = self.dq + self.dt*self.ddq
        self.q = self.q + self.dt*self.dq + 0.5*self.dt*self.dt*self.ddq
        # update end-effector: linear and angular position, velocity and acceleration
        self.p, self.R = self.forward_kinematics(self.q)
        self.dp, self.w = self.twist(self.q, self.dq)
        self.ddp, self.dw = self.dtwist(self.q, self.dq, self.ddq)
                
    def inverse_kinematics_position(self, x_des, q0):
        """
        @info: computes joint position (q) from cartesian position (xyz) using 
               the method of damped pseudo-inverse.
        @inputs:
        -------
            - xdes  :   desired position vector
            - q0    :   initial joint configuration (it's very important)
        @outputs:
        --------        
            - q_best  : joint position
        """         
        best_norm_e     = 1e-6 
        max_iter        = 10
        delta           = 1
        lambda_         = 0.0000001
        q               = copy(q0)

        for i in range(max_iter):
            p, _ = self.forward_kinematics(q) # current position
            e   = x_des - p      # position error
            J   = self.geometric_jacobian(q)[0:3, 0:self.ndof] # position jacobian [3x6]
            J_damped_inv =  damped_pinv(J, lambda_) # inverse jacobian [6x3]
            dq  = np.dot(J_damped_inv, e)
            q   = q + delta*dq
                       
            # evaluate convergence criterion
            if (np.linalg.norm(e)<best_norm_e):
                best_norm_e = np.linalg.norm(e)
                q_best = copy(q) 
        return q_best 

    def inverse_kinematics_pose(self, x_des, R_des, q0, max_iter=10):
        """
        @info: computes joint position (q) from cartesian position (xyz) and orientation(axis/angle) 
               using the method of damped pseudo-inverse.
        @inputs:
        -------
            - x_des: desired cartesian position
            - R_des: desired rotation matrix
            - q0: initial joint configuration (it's very important)
        @outputs:
        --------        
            - q_best  : joint position
        """         
        best_norm_e     = 1e-6 
        delta           = 1
        lambda_         = 0.0000001
        q               = copy(q0)

        for i in range(max_iter):
            p, R = self.forward_kinematics(q) # current position
            # error: position (xyz)
            e_p = x_des[0:3] - p                  
            # error: orientation axis/angle
            e_o = axisangle_error(R_des, R)
            # error: position and orientation
            e = np.concatenate((e_p,e_o), axis=0) # [6x1] 
            # jacobian
            J   = self.geometric_jacobian(q) # [6x6]
            # jacobian: pseudo-inverse
            J_damped_inv = damped_pinv(J, lambda_) # [6x6]
            dq  = np.dot(J_damped_inv, e)
            q   = q + delta*dq
            #print("e_o: ", e_o)                       
            # evaluate convergence criterion
            if (np.linalg.norm(e)<best_norm_e):
                best_norm_e = np.linalg.norm(e)
                q_best = copy(q) 
        return q

    def read_joint_position_velocity_acceleration(self):
        return self.q, self.dq, self.ddq

    def read_cartesian_position_velocity_acceleration(self):
        return self.p, self.dp, self.ddp

    def read_ee_position(self):
        return self.p

    def read_ee_orientation(self):
        return self.R

    def read_ee_angular_velocity_acceleration(self):        
        return self.w, self.dw

    def read_ee_linear_velocity(self):
        return self.v        

    def get_M(self):
        return self.M

    def get_b(self):
        return self.b

    def get_g(self):
        return self.g

class MultipleKalmanDerivator:
    """
    @info creates a kalman filter for each degree of freedom
    @inputs:
    -------
        - deltaT: samping time
        - n_obs: number of observable states
        - x0, dx0, ddx0: initial states [n_dof,]
        - sigmaR: covariance matrix that indicates model uncertainty / motion noise
        - sigmaQ: covariance matrix that indicates measurement noise  
    """
    def __init__(self, deltaT, x0, dx0, ddx0, n_obs=2, sigmaR = 1e-3, sigmaQ = 1):
        # initial conditions
        self.q = copy(x0)
        self.dq = copy(dx0)
        self.ddq = copy(ddx0)
        self.n_dof = len(self.q)
        # samping time
        self.deltaT = deltaT
        # list to store KalmanDerivator objects 
        self.derivators = []
        # create and initialiZe KalmanDerivator objects 
        for i in range(self.n_dof):
            x0 = np.array([self.q[i], self.dq[i], self.ddq[i]])
            self.derivators.append(KalmanDerivator(x0, n_obs, self.deltaT, sigmaR, sigmaQ))
                
    def update(self, qr, dqr):
        # update the kalman filter for each degree of freedom
        for i in range(self.n_dof):
            q, dq, ddq = self.derivators[i].run_kalman_filter(qr[i], dqr[i])
            self.q[i] = q
            self.dq[i] = dq
            self.ddq[i] = ddq
        # return filtered signal
        return self.q, self.dq, self.ddq

class KalmanDerivator:
    """
    @info implement the kalman filter algorithm of the book "Probabilistic Robotics (Thrun 2000, pg. 36)" 
    @inputs:
    -------
        - x_est0: initial states
        - n_obs: number of observable states
        - deltaT: samping time
        - sigmaR: covariance matrix that indicates model uncertainty / motion noise
        - sigmaQ: covariance matrix that indicates measurement noise  
    """
    def __init__(self, x_est0, n_obs, deltaT, sigmaR = 1e-3, sigmaQ = 1):
        # useful parameters
        self.deltaT = deltaT # samping time
        self.n_input = len(x_est0) # input states
        self.n_obs = n_obs # output states

        # prediction stage: initial values
        self.F = np.array([[1., self.deltaT, self.deltaT**2/2],[0., 1., self.deltaT],[0.,0.,1.]])
        self.x_hat = np.zeros((self.n_input,1)) # [q0, dq0, ddq0]
        self.P_hat =  np.zeros((self.n_input, self.n_input))

        # observation-correction stage: initial values
        self.H = self.create_H(self.n_obs, self.n_input)
        self.x_est = copy(x_est0).reshape((self.n_input,1)) # [q, dq ,ddq]
        self.P_est = np.zeros((self.n_input, self.n_input))
        
        # covariance matrices
        self.R = sigmaR*np.eye(self.n_input)  # model uncertainty
        self.Q = sigmaQ*np.eye(self.n_obs) # measurement noise

        # kalman gain: initial value
        self.K = np.zeros((self.n_input,self.n_obs))         

        self.I = np.eye(self.n_input)

    def create_H(self, n_obs, n_input):
        if n_input-n_obs !=0:
            return np.concatenate((np.eye(n_obs), np.zeros((n_obs,n_input-n_obs))), axis=1)
        else:
            return np.eye(n_input)
        
    def run_kalman_filter(self, q, dq):
        # measurements
        self.z = np.array([[q],[dq]])
        # prediction stage
        self.x_hat = mx(self.F,self.x_est)
        self.P_hat = mx(self.F, mx(self.P_est, tr(self.F))) +  self.R

        # kalman gain
        self.K = mx(mx(self.P_hat, tr(self.H)), inv(mx(self.H, mx(self.P_hat, tr(self.H))) + self.Q))   

        # observation-correction stage      
        self.x_est = self.x_hat + mx(self.K, (self.z - mx(self.H, self.x_hat)))
        self.P_est = mx(self.I - mx(self.K,self.H), self.P_hat)
        
        # return position, velocity and acceleration
        return self.x_est[0][0], self.x_est[1][0], self.x_est[2][0]


class DataReader:
    """
    @info: Class to obtain kinematics measurements from external dataset (JIGSAWS)

    @methods:
        - read_dataset(Boolean right_arm)
        - calculate()
        - check()
        - dataset_trajectory_generator()
    """ 
    def __init__(self, path, dt = 0.01):
        
        self.datapath = path
        self.xs = np.array([])
        self.dxs = np.array([])
        self.ddxs = np.array([])
        self.dddxs = np.array([])
        self.dt = dt
        self.max_count = 0
        self.df = None
        self.i = 0
        self.rpy_old = np.zeros(3)

    def read_dataset(self, right_arm = False):
        self.df = pd.read_csv(self.datapath, delimiter = r"\s+", header = None)
        df = self.df
        pose = []
        vel = []
        nrows = df.shape[0]
        self.max_count = nrows- 2


        if right_arm == False:
            # Master
            ix, iy, iz  = 1, 2, 3
            iRs, iRe = 4, 12
            idx, idy, idz = 13, 14, 15
            iwx, iwy, iwz = 16, 17, 18

            # Slave
            # ix, iy, iz  = 39,40,41
            # iRs, iRe = 42,50
            # idx, idy, idz = 51,52,53
            # iwx, iwy, iwz = 54,55,56
        else: 
            # Master
            ix, iy, iz  = 20, 21, 22
            iRs, iRe = 23, 31
            idx, idy, idz = 32,33,34
            iwx, iwy, iwz = 35,36,37
        
            # Slave
            # ix, iy, iz  = 58, 59, 60
            # iRs, iRe = 61, 69
            # idx, idy, idz = 70,71,72
            # iwx, iwy, iwz = 73,74, 75

        for i in np.arange(nrows):
            x = df.iloc[i, ix - 1] # 0.4#- 0.6#- 0.4#+ (right_arm)*(-0.1) + (1 - right_arm)*(0.1) #+0.0#
            y = df.iloc[i, iy - 1] - 0.5 #+ (right_arm)*(-0.45) + (1 - right_arm)*(0.45) #+0.2#
            z = df.iloc[i, iz - 1] - 0.1 #+ 0.8 #+0.5#

            R = df.iloc[i, iRs-1:iRe].to_numpy().reshape(3,3)
            rpy=rot2rpy_unwrapping(R, self.rpy_old)
            self.rpy_old = copy(rpy)

            roll = rpy[0]
            pitch = rpy[1]
            yaw = rpy[2]

            dx = df.iloc[i, idx - 1]
            dy = df.iloc[i, idy - 1]
            dz = df.iloc[i, idz - 1]

            wx = df.iloc[i, iwx - 1]
            wy = df.iloc[i, iwy - 1]
            wz = df.iloc[i, iwz - 1]

            pose.append( [x, y, z, roll, pitch, yaw] )
            vel.append( [dx, dy, dz, wx, wy, wz])

        self.xs = np.array(pose)
        self.dxs = np.array(vel)

    def calculate(self):
        self.ddxs = np.diff(self.dxs, axis = 0) / self.dt
        self.dddxs = np.diff(self.ddxs, axis = 0) / self.dt

        self.xs = self.xs[:-4,:]
        self.dxs = self.dxs[:-4,:]
        self.ddxs = self.ddxs[:-3,:]
        self.dddxs = self.dddxs[:-2,:]

    def dataset_trajectory_generator(self):
        x = self.xs[self.i,:]
        dx = self.dxs[self.i,:]
        ddx = self.ddxs[self.i,:]
        dddx = self.dddxs[self.i,:]

        self.i += 1
        return x, dx, ddx, dddx

    def check(self):
        if self.i >= self.max_count-4:
            return True 
        return False


    def reset(self):
        self.i = 0


def softmax(x_e, dx_e):
    prob = np.exp(x_e)/(np.exp(x_e) + np.exp(dx_e))
    return prob