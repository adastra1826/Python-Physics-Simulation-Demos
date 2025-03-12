Problems:
- The visual specifications were not at all followed even remotely. 
- Pressing `r` exited the simulation.
- The code contained multiple hardcoded values.
- There appeared to be no way to take control of the platform and move it around.
- The code looks atrocious. 

Fixes:

3 HOURS

Generate me a Python script that uses Pymunk to create a simple physics game. The game is balancing a stick on a platform.

Make sure the only code at the top level is global variables. Everything else should be inside a function or class. Make sure no values are hardcoded. All relevant variables should be global variables. You must use if name == main, and have a main() function, which calls a class constructor and a method to run the simulation inside the class. Include helper functions as necessary. This method returns True to reset, or False to quit the simulation.