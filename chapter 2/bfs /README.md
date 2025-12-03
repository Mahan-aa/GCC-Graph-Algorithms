♟️ Chess Piece Shortest Path Visualizer (BFS)

at first this supposed to be Knight Shortest Path Visualizer but it was fun so i extended the code to work for every chess piece (i made this on mac using opengl 4.1 and i did not test it on windows or newer version of opengl if you are on windows run python version)


💻 Technical Details

Algorithm: Breadth-First Search (BFS)

BFS is used because it is guaranteed to find the shortest path in terms of the number of moves (the minimum number of edges in an unweighted graph).

State Representation: Each square on the board is treated as a node in the graph. The board dimensions are constants (BOARD_SIZE = 8).

BFS Data Structures:

std::deque<Point> queue: Stores the nodes to be explored, ensuring FIFO (First-In, First-Out) order to guarantee shortest path.

std::set<Point> visited: Tracks already processed nodes to prevent infinite loops and redundant work.

std::map<Point, Point> parents: Used to store the predecessor of each node, enabling path reconstruction once the goal is found.

Movement Functions: Specific C++ functions (knightMoves, kingMoves, rookMoves, etc.) implement the legal moves for each chess piece. These functions handle boundary checks to ensure generated moves remain within the 8x8 grid. Sliding pieces (Rook, Bishop, Queen) generate multiple immediate neighbors in a single direction, unlike the King or Knight.

Graphics and Libraries

C++: Core language.

GLFW: Used for creating the OpenGL context, managing the window, and handling user input (mouse and keyboard callbacks).

OpenGL (Fixed-Function Pipeline): Utilized for basic 2D rendering primitives (rectangles for the board, lines for edges, and circles/shapes for the pieces) using commands like glBegin/glEnd, glColor3f, and glRectf.

⚙️ How to Compile and Run

Prerequisites

A C++ compiler (e.g., GCC, Clang, MSVC).

GLFW Library: Must be installed on your system or configured in your build environment.

Build Steps (Example using CMake or simple GCC)

Assuming you are compiling on Linux or macOS and have GLFW installed via a package manager (brew install glfw or sudo apt install libglfw3-dev):

# Compile the source file
`g++ bfs.cpp -o chess_bfs -lglfw -lGL -lGLEW -lglut -lm -lpthread`

# Run the executable
`./chess_bfs`

# Run the python version
`pip install -r requerments.txt`
`python3 bfs.py`

Usage Instructions

Select Start Position: Click the desired square for the starting point.

Select Goal Position: Click the desired square for the target.

Select Piece: Press the corresponding number key (1-5) to choose a piece type.

Start Search: Press the SPACEBAR to begin the BFS visualization.

Reset: Press the R key or click the mouse again to reset the setup.