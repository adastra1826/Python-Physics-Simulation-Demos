Prompt:
add pockets and a counter for balls that go in them

Criteria:
1. The model should add 6 pockets to the pool table in the locations that a normal pool table would have. For example, it should include one in each of the four corners, and one halfway along the two long sides of the table.
2. The pockets should be represented as circles that are larger than the pool table balls.
3. The pool table pockets should be positioned such that the innermost point of each pocket (towards the inside of the table) does not extend past the innermost line of each rail. In other words, each pocket should be set off from the table and into the rails so that no part of the pocket is inside the table past the rails.
4. The pool table rails should not block the pockets and prevent the balls from being able to fully enter the pockets.
5. The model should add text in the GUI indicating how many pool balls have entered a pocket. 
6. The pocketed-balls text counter should be one counter for all pockets, not a counter for each individual pocket.
7. Balls should be removed from the simulation when they enter a pocket.
8. A ball should be considered to have entered a pocket if its center point is anywhere inside a pocket circle.
9. The pre-existing functionality of the simulation should not be affected. For example, the keyboard shortcuts ('r': reset, 'q': quit, and 'space': pause) should still work; the simulation should still start with the cue ball shooting at the racked balls from a random position; the balls should still behave as solid objects that move and collide with each other and the rails as if they were balls rolling on a table.
10. The pockets should be colored black.