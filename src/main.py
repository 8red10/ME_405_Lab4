'''!
@file main.py
    This file runs a motor with a proportional controller that is given positional 
    information from an encoder reader. The motor and encoder reader are parts of 
    the ME 405 lab kit. The proportional controller is run as a task and uses the 
    cotask and task_share imported files to do so. Running the controller as a task
    allows the possiblity of running multiple proportional controllers at once, each 
    with their own period (task frequency).
    
Task sharing helpful notes 
    - A shared variable is commonly referenced as a 'share'. 
    - A shared queue is commonly referenced simply as a 'queue'. 

Motor 1 Pin Setup:
    PC1 = Enable Pin (internal with the L6206);
    PA0 = Motor Input 1 (internal with the L6206);
    PA1 = Motor Input 2 (internal with the L6206)

Encoder 1 Pin Setup:
    PC6 = Encoder Input A;
    PC7 = Encoder Input B

Motor 2 Pin Setup:
    PA10 = Enable Pin (internal with the L6206)
    PB4  = Motor Input 1 (internal with the L6206)
    PB5  = Motor Input 2 (internal with the L6206)

Encoder 2 Pin Setup:
    PB6 = Encoder Input A
    PB7 = Encoder Input B

Motor Wire Connections:
    Blue	    = Encoder channel B;
    Yellow	    = Encoder channel A;
    Red	        = Encoder 5V supply (should be connected to the 3.3V supply);
    Black	    = Encoder ground;
    Orange	    = Motor power (for the motor + connection on the L6206);
    Green	    = Motor power (for the motor - connection on the L6206);
    (None)	    = No connection

@author Jack Krammer and Jason Chang
@date   27-Feb-2024
@copyright (c) 2024 by mecha04 and released under MIT License
'''

import gc
import pyb
import utime
import cotask
import task_share
import motor_driver as md
import encoder_reader as er
import proportional_controller as pc


def motor1_task_fun(share):
    '''!
    This task runs a closed-loop motor controller using the encoder reader as the position
    sensor. Motor driver is set up with enable pin PC1, motor input pin 1 PA0, and motor 
    input 2 pin PA1. Encoder reader is set up with encoder input A on PC6 and encoder input 
    B on PC7. Results are then printed in time,position CSV format for GUI to plot. 
    Task function inherently must be a generator function.
    @param      share -> A list of the shared variables. Should just be a float that 
                holds the control gain to use for this task.
    @returns    As a generator function, returns the state of the task.
    '''
    # access the shares
    kp_share = share

    # initialize the number of data points for the step response plot 
    DATA_POINTS = 100 # DATA_POINTS = 1000 ms sample period // 10 ms between task execution

    # indicate initializations
    print('Initializing motor driver, encoder reader, and proportional controller.')
    # create a motor driver object
    motor = md.MotorDriver(pyb.Pin.board.PC1, pyb.Pin.board.PA0, pyb.Pin.board.PA1, timer=5)
    # create an encoder reader object
    encoder = er.Encoder(pyb.Pin.board.PC6, pyb.Pin.board.PC7, timer_num=8)
    # create a proportional controller object
    control = pc.ProportionalController(Kp=2,
                                        setpoint=0,
                                        actuate=motor.set_duty_cycle,
                                        sense=encoder.read,
                                        data_points=DATA_POINTS
                                        )
    # initialize the destination setpoint for the proportional controller
    setpoint = 8150#10000
    # # initialize the control gain to use for the step response
    # kp_val = 0.05
    # indicate done with initializations
    print('Done initializing.')
    
    # stop actuating the motor
    motor.set_duty_cycle(0)
    # reset the encoder to zero
    encoder.zero()
    # set the control gain
    control.set_Kp(kp_share.get())

    # get the start time of the step response
    start_time = utime.ticks_ms()

    # execute step response
    for i in range(DATA_POINTS):
        # run the proportional controller
        control.run(setpoint, start_time)
        
        yield 0
    
    # after all data points are taken, stop the motor
    motor.set_duty_cycle(0)
    # then print the results
    control.print_data()

    # after step response, keep the generator function valid by yielding 0
    while True:

        yield 0


def motor2_task_fun(share):
    '''!
    This task runs a closed-loop motor controller using the encoder reader as the position
    sensor. Motor driver is set up with enable pin PA10, motor input pin 1 PB4, and motor 
    input 2 pin PB5. Encoder reader is set up with encoder input A on PB6 and encoder input 
    B on PB7. Results not printed for this task. 
    Task function inherently must be a generator function.
    @param      share -> A list of the shared variables. Should just be a float that 
                holds the control gain to use for this task.
    @returns    As a generator function, returns the state of the task.
    '''
    # access the shares
    kp_share = share

    # initialize the number of data points for the step response plot 
    DATA_POINTS = 100 # DATA_POINTS = 1000 ms sample period // 10 ms between task execution

    # indicate initializations
    print('Initializing motor driver, encoder reader, and proportional controller.')
    # create a motor driver object
    motor = md.MotorDriver(pyb.Pin.board.PA10, pyb.Pin.board.PB4, pyb.Pin.board.PB5, timer=3)
    # create an encoder reader object
    encoder = er.Encoder(pyb.Pin.board.PB6, pyb.Pin.board.PB7, timer_num=4)
    # create a proportional controller object
    control = pc.ProportionalController(Kp=2,
                                        setpoint=0,
                                        actuate=motor.set_duty_cycle,
                                        sense=encoder.read,
                                        data_points=DATA_POINTS
                                        )
    # initialize the destination setpoint for the proportional controller
    setpoint = 32000
    # # initialize the control gain to use for the step response
    # kp_val = 0.05
    # indicate done with initializations
    print('Done initializing motor 2.')
    
    # stop actuating the motor
    motor.set_duty_cycle(0)
    # reset the encoder to zero
    encoder.zero()
    # set the control gain
    control.set_Kp(kp_share.get())

    # get the start time of the step response
    start_time = utime.ticks_ms()

    # execute step response
    for i in range(DATA_POINTS):
        # run the proportional controller
        control.run(setpoint, start_time)
        
        yield 0
    
    # after all data points are taken, stop the motor
    motor.set_duty_cycle(0)
    # # then print the results
    # control.print_data()

    # after step response, keep the generator function valid by yielding 0
    while True:

        yield 0


def main():
    '''!
    This code is only run if this file is run as the main file. This code prompts the user 
    for a control gain value and a task execution period value. Two tasks are then created
    and these values are used to influence their behavior. These tasks are run at the same
    time with the help of cotask and task_share imports. The tasks are run until a 
    KeyboardInterrupt is caught, at which time the scheduler stops and the printouts show 
    diagnostic information about the tasks and the shared variable. Input for the control
    gain should be a positive nonzero float and the input for the task execution period 
    should be a postive nonzero integer.
    @param      None.
    @returns    None.
    '''
    # handle keyboard interrupts and incorrect values for the input control gain
    try:
        # wait for user input for the Kp control gain value
        Kp_input = input('Input the desired float type Kp value (control gain value) for the next sample: \r\n') # need to include the \r\n so the ser.readline() will not be blocking
        # format the Kp value
        Kp_val = float(Kp_input)
        print(f'Running test using kp = {Kp_val}')

        # wait for user input for the period of the task
        period_input = input('Input the desired integer type period for the task to run: \r\n') # need to include the \r\n so the ser.readline() will not be blocking
        # format the period
        period_val = int(period_input)
        print(f'Running test using period = {period_val}')

        # Create a shared float type variable for the control gain
        share_kp = task_share.Share('f', thread_protect=False, name="Share_Kp")
        share_kp.put(Kp_val)

        # Create the tasks. If trace is enabled for any task, memory will be
        # allocated for state transition tracing, and the application will run out
        # of memory after a while and quit. Therefore, use tracing only for 
        # debugging and set trace to False when it's not needed
        task1 = cotask.Task(motor1_task_fun, name="Motor_Task_1", priority=1, period=period_val, #10,
                            profile=True, trace=False, shares=(share_kp))
        task2 = cotask.Task(motor2_task_fun, name="Motor_Task_2", priority=2, period=period_val, #10,
                            profile=True, trace=False, shares=(share_kp))
        
        # Add the tasks to the task list
        cotask.task_list.append(task1)
        cotask.task_list.append(task2)

        # Run the memory garbage collector to ensure memory is as defragmented as
        # possible before the real-time scheduler is started
        gc.collect()

        # Run the scheduler with the chosen scheduling algorithm. Quit if ^C pressed
        while True:
            cotask.task_list.pri_sched()

    except ValueError:
        print(f'\nValueError: Incorrect input for Kp value or period value.')
        print(f'\tKp input was "{Kp_input}" and period input was "{period_input}".')
        print(f'\tBoth should be a positive nonzero number, Kp a float and period an integer.')
        print(f'Exiting.\n\n')
    except KeyboardInterrupt:
        print(f'\nExiting due to a KeyboardInterrupt.\n\n')
    
    # Print a table of task data and a table of shared information data
    print('\n' + str (cotask.task_list))
    print(task_share.show_all())
    print(task1.get_trace())
    print('')

# This main code is run if this file is the main program but won't run if this
# file is imported as a module by some other main program
if __name__ == '__main__':
    main()
