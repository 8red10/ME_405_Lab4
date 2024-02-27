'''!
@file proportional_controller.py
This file contains code for the ProportionalController class that is built to drive an actuator
proportional to the error between the desired set point and the current position. The actuator 
and position sensor are interacted with by the actuate function and sense function input to 
the constructor of this class. There is no main function in this file, so when this file is 
run as main, nothing will happen. 

@author Jack Krammer and Jason Chang
@date   20-Feb-2024
@copyright (c) 2024 by mecha04 and released under MIT License
'''


import pyb
import utime
from cqueue import IntQueue

class ProportionalController:
    '''!
    This class implements a proportional controller.
    '''
    def __init__(self,Kp,setpoint,actuate,sense,data_points):
        '''!
        Creates a ProportionalController instance. This instance is expected to be run in a 
        feedback loop such that the run() function of this class can continuously change
        the input to the actuator based on the result read from the position sensor. 
        @param      Kp -> The control gain to initialize the proportional controller with.
                    Control gain is the gain to apply to the difference of the input setpoint
                    and the measured output to obtain the duty cycle. (i.e. to apply to a 
                    motor)
        @param      setpoint -> The setpoint to initialize the proportional controller with.
                    Setpoint is an integer representing the desired location of the actuator 
                    in units of encoder counts. (i.e. position of a motor)
        @param      actuate -> The function that is a member of the class of the actuator 
                    driver (e.g. MotorDriver). The only input to this function is a duty 
                    cycle in the range [-100,100], inclusive.
        @param      sense -> The function that is a member fo the class of the position sensor
                    driver (e.g. Encoder). Returns a value representing the current position.
                    There should be no required inputs to this function. 
        @param      data_points -> The number of data points that will be taken from the result
                    of the proportional controller. This is an integer that also represents the 
                    number of times the run() function is expected to be executed. This value 
                    will be used to initialize the queue length. If data collection is not 
                    desired, any postive integer can be used for this parameter.
        @returns    None.
        '''
        # initialize the control gain
        self.Kp = Kp
        # initialize the desired position
        self.setpoint = setpoint
        # initialize the function to control the actuator
        self.actuate = actuate
        # initialize the function to read from the sensor
        self.sense = sense
        # initialize the queue length
        self.queue_len = data_points
        # initialize a queue to store elapsed time data
        self.timeQ = IntQueue(self.queue_len)
        # initialize a queue to store position data
        self.positionQ = IntQueue(self.queue_len)

    def reset_queues(self):
        '''!
        Resets the time queue and position queue by clearing them of all data. 
        @param      None.
        @returns    None.
        '''
        # clear the time queue
        self.timeQ.clear()
        # clear the position queue
        self.positionQ.clear()
    
    def print_data(self):
        '''!
        Prints the data in the queues in CSV format: time_value,position_value. Also 
        adds headers to the beginning to identify the data printed. Lastly, prints 
        'End' to signal the end of the data.
        @param      None.
        @returns    None.
        '''
        # # prints the initial heading
        # print('Time (ms), Position (encoder ticks)') # gui will handle already
        # prints the contents of the queues in time_value,position_value format
        while self.timeQ.any():
            print(f'{self.timeQ.get()},{self.positionQ.get()}')
        # prints the terminating 'End'
        print('End')
        # clears the queues
        self.reset_queues()

    def set_data_points(self,num_data_points):
        '''!
        Sets the queue length variable to to the number of data points desired in each
        queue. This is essentially the same thing as the queues will only hold 
        queue_length number of data points.
        @param      num_data_points -> An integer representing the number of data points
                    the queues should hold. 
        @returns    None.
        '''
        # sets the queue length variable
        self.queue_len = num_data_points

    def run(self,setpoint,start_time):
        '''!
        Runs the control algorithm to position the actuator based on information from the 
        sensor. This is expected to be continuously run as to approximate a feedback loop.
        The desired setpoint is compared with the current position read from the sense 
        function inputted to the constructor of this class. The difference (error) in 
        position is multiplied with the gain to obtain the duty cycle that is then applied 
        to the acutator. Further, this function adds the time elapsed from start_time to
        the time queue and the actuator position read from the sensor to the position
        queue.
        @param      setpoint -> The desired destination position of the actuator.
        @param      start_time -> A utime.ticks_ms() object representing the starting time 
                    of the current feedback loop. To be used for time data associated with
                    the current position.
        @returns    The value sent to the actuator throught the actuate function inputted
                    to the constructor of this class.
        '''
        # sets the setpoint to the desired value
        self.setpoint = setpoint
        # gets the time difference
        d = utime.ticks_diff(utime.ticks_ms(), start_time)
        # print(f'this is the time difference we are putting into the timeQ: "{d}"') # will just add extra for the gui
        # adds the elapsed time to the time queue
        self.timeQ.put(d)
        # get the current position of the actuator
        current_position = self.sense()
        # adds the current position to the position queue
        self.positionQ.put(current_position)
        # calculate the value to apply to the actuator
        pwm = self.Kp * (self.setpoint - current_position)
        # set the acutator to the calculated value
        self.actuate(pwm)
        # return the value sent to the actuator
        return pwm

    def set_setpoint(self,setpoint):
        '''!
        Sets the setpoint to the input value.
        @param      setpoint -> the value to set the setpoint to.
        @returns    None.
        '''
        # sets the set point
        self.setpoint = setpoint

    def set_Kp(self,Kp):
        '''!
        Sets the control gain, Kp, to the desired value.
        @param      Kp -> the value to set the control gain to.
        @returns    None.
        '''
        # check that the input Kp value is a number
        if type(Kp) is not float:
            if type(Kp) is not int:
                raise ValueError('Kp value should be a positive nonzero number.')
        # check that the input Kp value is a positive nonzero number
        if Kp <= 0:
            raise ValueError('Kp value should be a positive nonzero number.')
        
        # sets the control gain
        self.Kp = Kp

