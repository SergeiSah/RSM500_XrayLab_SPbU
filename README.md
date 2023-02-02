## Elements of the RSM-500

![plot](https://github.com/SergeiSah/RSM500_XrayLab_SPbU/blob/master/Files/analyzing_camera_layout_1.0.png)

## Working principle

Program works as a command prompt. User should input a command in one of the two ways:
1. `> command <param_1> <param_2> ...`
2. `> command`

Inputting a command without parameters results in the hints. To close the
program, one should input `close`, `quit`, `exit`, `c` or `q`.
If one inputs `params` after a command, names of the parameters will appear. In the case of `doc` a docstrings of the 
command will be output.


## Commands

- `escan <start_rev> <step_num> <step_rev> <exposure_sec>`

    Run the energy scan (measurement of the reflection spectrum) 
    with the given parameters.
    - `start_rev` - position of the motor 0 in the rev of the reel, 
       from which the scan will be started
    - `step_num` - number of steps in the scan
    - `step_rev` - value of each step in the rev of the reel
    - `exposure` - exposure time of the detectors in seconds


- `ascan <motor> <start_position> <step_num> <step> <exposure>`

  Run scanning by the given motor from the specified absolute position.
  - `motor` - number of the motor
  - `start_position` - specifies position, to which motor will move before scanning
  - `step` - value of each step


- `mscan <exposure_sec=1> <time_steps_on_plot=30>`
    
    Continuously displays CPS values on a plot over time.
    - `time_steps_on_plot` - number of the x-axis ticks on a plot


- `move <motor> <step>`
    
   Move the specified motor by the given step relative to the position where the motor is currently located. 
   Step for the motor 0 are in the revs of the reel, for motor 1 and 2 in grads, for the motor 3 in `!!!`.
  - `<motor>` - number of the motor
  - `<step>` - value of step to move


- `amove <motor> <position>`

  Move the given motor to the specified absolute position.
  - `<motor>` - number of the motor
  - `<position>` - the absolute position to which the motor will be moved


- `setV <voltage_det_1> <voltage_det_2>`

  Set voltage on the photocathodes of the detectors.
  - `<voltage_det_>` - value of the voltage on the photocathode of the detector


- `setT <detector_num> <lower_threshold> <upper_threshold>`

  Set the lower and upper thresholds for the given detector.
  - `<detector_num>` - number of the detector
  - `<_threshold>` - value of the corresponding threshold


- `set2T <lower_threshold> <upper_threshold>`

  Set the same thresholds for the both detectors.


- `setAPos <motor>`

  Set absolute position of the motor in the `settings.ini` file to zero.


- `getV`

  Output the voltage values applied to the photocathodes to the console.


- `getT`

  Output the thresholds set on the detectors to the console.


- `getApos`

  Output the absolute positions of the motors 1, 2 and 3 to the console.


- `info` or `help`

  Output the basic information about the program to the console. 

## Limitations

There are following confines for different parameters of the RSM's element:
- `exposure` of the detectors: \[0.1, 999]
- `threshold` of the detectors: \[0, 4096)
- `voltage` on the photocathodes: \[0, 2048)