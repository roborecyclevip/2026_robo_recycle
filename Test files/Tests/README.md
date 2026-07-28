# What is this directory
This directory holds all the tests that are ran to draw dots on our Ultimaker S5 Gantry system.

# Tests that are ran
- [gantry_20mm.py](gantry_20mm.py): Draws from (20,20) to (220,220) a dot every 20mm
- [gantry_10mm.py](gantry_10mm.py): Draws from (20,20) to (220,220) a dot every 10mm
- [gantry_random.py](gantry_random.py): Draws dots at different random predefined coordinates multiple times to test reliability / stability of results
- [gantry_random_homing.py](gantry_random_homing.py): The earlier but we try homing as well 
- [gantry_diff_direction.py](gantry_diff_direction.py): Approaches from boundaries of printer to each coordinate from all 4 directions and attempts to draw a dot. If difference is large
- TODO: Implement Z axis one

# Running tests
To run any individual test, you can either have all the files are executable using `chmod u+rx <file_name>` followed by `./<file_name>`, or run them using `python3 <file_name>`. 

## Running all tests
you can use the `python3 gantry_run_all.py` to run all the tests. 

The combined test runner is currently `grantry_run_all.py`. It asks for the z coordinate once, uses one serial connection for every test, and waits for paper change confirmation between tests.
