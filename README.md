## Commands

- `escan <start_rev> <step_num> <step_rev> <exposure_sec>`

    Run the energy scan (measurement of the reflection spectrum) 
    with the given parameters.
    - `start_rev` - position of the motor 0 in the rev of the reel, 
       from which the scan will be started
    - `step_num` - number of steps in the scan
    - `step_rev` - value of each step in the rev of the reel
    - `exposure` - exposure time of the detectors in seconds
- 
- `mscan <exposure_sec=1> <time_steps_on_plot=30>`
    
    Continuously displays CPS values on a plot over time.
    - `exposure` - exposure time of the detectors in seconds
    - `time_steps_on_plot` - number of the x-axis ticks on a plot

## Limitations

- `exposure` of the detectors: \[0.1, 999]
- `threshold` of the detectors: \[0, 4096)
- `voltage` on the photocathodes: \[0, 2048)