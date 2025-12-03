# Chess Piece Shortest Path Visualizer using Pygame
# This program finds and visualizes the shortest path for various chess pieces 
# on an 8x8 board using the Breadth-First Search (BFS) algorithm.

import pygame
import collections
import math
import time
import sys

# --- Constants ---
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 640
BOARD_SIZE = 8
SQUARE_SIZE = SCREEN_WIDTH // BOARD_SIZE
PI = math.pi
FPS = 60
BFS_DELAY_MS = 60  # Time delay between BFS steps in milliseconds

# --- Colors ---
GRAY_LIGHT = (240, 217, 181)
GRAY_DARK = (181, 136, 99)
BLUE_VISITED = (100, 149, 237)  # Nodes in the queue/visited
YELLOW_CURRENT = (255, 215, 0)   # Node being processed
GREEN_PATH = (50, 205, 50)      # Final shortest path
RED_GOAL = (220, 20, 60)        # Goal square
EDGE_COLOR = (50, 50, 50)       # Lines connecting edges
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# --- Data Structures ---

class Point:
    """Represents a coordinate (column, row) on the board."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __lt__(self, other):
        # Used for key in sets and maps (required for consistency)
        if self.x != other.x:
            return self.x < other.x
        return self.y < other.y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"({self.x}, {self.y})"

class PieceType:
    KNIGHT, KING, ROOK, BISHOP, QUEEN = range(5)

# --- Movement Functions ---

# Knight Moves (L-shapes offsets)
KNIGHT_MOVES = [
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2)
]

def is_on_board(p):
    """Checks if a Point is within the 8x8 board boundaries."""
    return 0 <= p.x < BOARD_SIZE and 0 <= p.y < BOARD_SIZE

def get_knight_moves(p):
    """Calculates all legal Knight moves from point p."""
    neighbors = []
    for dx, dy in KNIGHT_MOVES:
        n = Point(p.x + dx, p.y + dy)
        if is_on_board(n):
            neighbors.append(n)
    return neighbors

def get_king_moves(p):
    """Calculates all legal King moves from point p (1 step in any direction)."""
    neighbors = []
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx == 0 and dy == 0:
                continue
            n = Point(p.x + dx, p.y + dy)
            if is_on_board(n):
                neighbors.append(n)
    return neighbors

def sliding_moves(p, dirs):
    """
    Helper function for sliding pieces (Rook, Bishop, Queen).
    Iterates in specified directions until hitting the board edge.
    """
    neighbors = []
    for dx, dy in dirs:
        nx, ny = p.x + dx, p.y + dy
        while is_on_board(Point(nx, ny)):
            neighbors.append(Point(nx, ny))
            nx += dx
            ny += dy
    return neighbors

def get_rook_moves(p):
    """Calculates all legal Rook moves (orthogonal sliding)."""
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    return sliding_moves(p, dirs)

def get_bishop_moves(p):
    """Calculates all legal Bishop moves (diagonal sliding)."""
    dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    return sliding_moves(p, dirs)

def get_queen_moves(p):
    """Calculates all legal Queen moves (all sliding directions)."""
    dirs = [
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ]
    return sliding_moves(p, dirs)


# Map piece type to its movement function
MOVE_FUNCTIONS = {
    PieceType.KNIGHT: get_knight_moves,
    PieceType.KING: get_king_moves,
    PieceType.ROOK: get_rook_moves,
    PieceType.BISHOP: get_bishop_moves,
    PieceType.QUEEN: get_queen_moves,
}

# --- Visualizer Class ---

class BFSVisualizer:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Chess Piece BFS Visualizer")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

        # State Variables
        self.start_pos = None
        self.goal_pos = None
        self.current_piece = PieceType.KNIGHT
        self.running_bfs = False
        self.path_found = False
        self.animating_path = False
        
        # BFS Variables
        self.queue = collections.deque()
        self.visited = set()
        self.parents = {}
        self.edges_explored = []
        self.current_node = None
        self.last_bfs_step_time = 0

        # Animation Variables
        self.shortest_path = []
        self.anim_index = 0
        self.anim_progress = 0.0
        self.render_pos = (-SQUARE_SIZE, -SQUARE_SIZE) # Offscreen initially
        
        self.reset_state()

    def reset_state(self):
        """Resets all BFS and animation variables for a new run."""
        self.start_pos = None
        self.goal_pos = None
        self.running_bfs = False
        self.path_found = False
        self.animating_path = False
        self.queue.clear()
        self.visited.clear()
        self.parents.clear()
        self.edges_explored.clear()
        self.shortest_path.clear()
        self.anim_index = 0
        self.anim_progress = 0.0
        self.current_node = None
        self.render_pos = (-SQUARE_SIZE, -SQUARE_SIZE)

    def get_square_coords(self, p):
        """Returns the top-left pixel coordinates for a Point."""
        return (p.x * SQUARE_SIZE, p.y * SQUARE_SIZE)

    def start_bfs(self):
        """Initializes the BFS algorithm."""
        if not self.start_pos or not self.goal_pos or self.running_bfs:
            return

        # Reset search-specific variables
        self.queue.clear()
        self.visited.clear()
        self.parents.clear()
        self.edges_explored.clear()
        self.shortest_path.clear()
        self.path_found = False
        self.animating_path = False
        self.current_node = None
        
        # Initialize BFS
        self.queue.append(self.start_pos)
        self.visited.add(self.start_pos)
        self.parents[self.start_pos] = None
        self.running_bfs = True
        self.last_bfs_step_time = time.time()

    def step_bfs(self):
        """Performs one step of the BFS algorithm."""
        if not self.queue:
            self.running_bfs = False
            return

        current = self.queue.popleft()
        self.current_node = current

        # Check for goal
        if current == self.goal_pos:
            self.reconstruct_path()
            self.running_bfs = False
            self.path_found = True
            self.animating_path = True
            self.anim_index = 0
            self.anim_progress = 0.0
            x, y = self.get_square_coords(self.shortest_path[0])
            self.render_pos = (x, y)
            return

        # Expand neighbors using the appropriate move function
        move_func = MOVE_FUNCTIONS[self.current_piece]
        neighbors = move_func(current)

        for neighbor in neighbors:
            if neighbor not in self.visited:
                self.visited.add(neighbor)
                self.parents[neighbor] = current
                self.queue.append(neighbor)
                self.edges_explored.append((current, neighbor))

    def reconstruct_path(self):
        """Backtracks from goal to start using the parents map."""
        curr = self.goal_pos
        temp_path = []
        while curr is not None:
            temp_path.append(curr)
            if curr == self.start_pos: break
            curr = self.parents.get(curr)
        
        # Reverse to get start -> goal order
        self.shortest_path = temp_path[::-1]

    def update_animation(self):
        """Updates the interpolated position of the moving piece."""
        if not self.shortest_path: return
        
        if self.anim_index >= len(self.shortest_path) - 1:
            self.animating_path = False
            # Snap to final position
            x, y = self.get_square_coords(self.shortest_path[-1])
            self.render_pos = (x, y)
            return

        speed = 0.05  # Animation speed (higher is faster)
        self.anim_progress += speed
        
        start_node = self.shortest_path[self.anim_index]
        end_node = self.shortest_path[self.anim_index + 1]

        sx, sy = self.get_square_coords(start_node)
        ex, ey = self.get_square_coords(end_node)

        # Linear Interpolation
        cur_x = sx + (ex - sx) * self.anim_progress
        cur_y = sy + (ey - sy) * self.anim_progress

        # Jump effect (more pronounced for Knight)
        jump_height = 20 if self.current_piece == PieceType.KNIGHT else 8
        jump_offset = math.sin(self.anim_progress * PI) * jump_height
        
        cur_y -= jump_offset
        
        self.render_pos = (cur_x, cur_y)

        if self.anim_progress >= 1.0:
            self.anim_progress = 0.0
            self.anim_index += 1
            # Ensure position snaps to end_node exactly
            self.render_pos = (ex, ey) 

    # --- Drawing Methods ---
    
    def draw_board(self):
        """Draws the checkerboard pattern."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                color = GRAY_LIGHT if (r + c) % 2 == 0 else GRAY_DARK
                rect = pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(self.screen, color, rect)

    def draw_piece_symbol(self, surface, piece_type, x, y):
        """Draws a simple symbolic representation of a chess piece."""
        cx = x + SQUARE_SIZE // 2
        cy = y + SQUARE_SIZE // 2
        r = SQUARE_SIZE // 4
        
        # Draw piece based on type (simple geometric shapes)
        if piece_type == PieceType.KNIGHT:
            # Horse shape (simplified)
            pygame.draw.circle(surface, BLACK, (cx, cy - 4), r)
            pygame.draw.circle(surface, WHITE, (cx, cy - 4), r - 3)
            pygame.draw.rect(surface, BLACK, (cx - 6, cy - 6, 12, 12))
        elif piece_type == PieceType.KING:
            # Circle with a cross
            pygame.draw.circle(surface, BLACK, (cx, cy), r)
            pygame.draw.line(surface, WHITE, (cx - 8, cy), (cx + 8, cy), 3)
            pygame.draw.line(surface, WHITE, (cx, cy - 8), (cx, cy + 8), 3)
        elif piece_type == PieceType.ROOK:
            # Tower shape
            pygame.draw.rect(surface, BLACK, (cx - r, cy - r // 2, r * 2, r * 2))
            pygame.draw.rect(surface, WHITE, (cx - r + 3, cy - r // 2 + 3, r * 2 - 6, r * 2 - 6))
        elif piece_type == PieceType.BISHOP:
            # Oval shape with a cut
            pygame.draw.ellipse(surface, BLACK, (cx - r, cy - r * 1.5, r * 2, r * 3))
            pygame.draw.line(surface, WHITE, (cx - 5, cy - 5), (cx + 5, cy + 5), 3)
        elif piece_type == PieceType.QUEEN:
            # Crown shape
            pygame.draw.polygon(surface, BLACK, [(cx - r, cy + r), (cx + r, cy + r), (cx + r, cy - r), (cx, cy - r * 1.5), (cx - r, cy - r)])
            pygame.draw.circle(surface, WHITE, (cx, cy - r // 2), 5)


    def draw_scene(self):
        """Renders all game elements."""
        self.draw_board()

        # 1. Draw Visited Squares (Blue)
        for p in self.visited:
            if p != self.start_pos and p != self.goal_pos:
                rect = pygame.Rect(self.get_square_coords(p), (SQUARE_SIZE - 4, SQUARE_SIZE - 4))
                rect.move_ip(2, 2)
                pygame.draw.rect(self.screen, BLUE_VISITED, rect)

        # 2. Draw Edges (Gray lines)
        for p1, p2 in self.edges_explored:
            c1x, c1y = self.get_square_coords(p1)
            c2x, c2y = self.get_square_coords(p2)
            pygame.draw.line(self.screen, EDGE_COLOR, 
                             (c1x + SQUARE_SIZE // 2, c1y + SQUARE_SIZE // 2),
                             (c2x + SQUARE_SIZE // 2, c2y + SQUARE_SIZE // 2), 2)

        # 3. Draw Path Overlay (Green lines/rectangles)
        if self.path_found and not self.animating_path:
            for p in self.shortest_path:
                rect = pygame.Rect(self.get_square_coords(p), (SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                rect.move_ip(5, 5)
                pygame.draw.rect(self.screen, GREEN_PATH, rect, 3)

        # 4. Draw Current Node (Yellow)
        if self.running_bfs and self.current_node:
            rect = pygame.Rect(self.get_square_coords(self.current_node), (SQUARE_SIZE - 8, SQUARE_SIZE - 8))
            rect.move_ip(4, 4)
            pygame.draw.rect(self.screen, YELLOW_CURRENT, rect)

        # 5. Draw Start & Goal Markers
        if self.start_pos:
            x, y = self.get_square_coords(self.start_pos)
            self.draw_piece_symbol(self.screen, self.current_piece, x, y)
            
        if self.goal_pos:
            cx, cy = self.get_square_coords(self.goal_pos)
            pygame.draw.circle(self.screen, RED_GOAL, 
                               (cx + SQUARE_SIZE // 2, cy + SQUARE_SIZE // 2), 
                               SQUARE_SIZE // 3)

        # 6. Draw Moving Piece (Animation)
        if self.start_pos:
            rx, ry = self.render_pos
            self.draw_piece_symbol(self.screen, self.current_piece, rx, ry)
            
        pygame.display.flip()

    # --- Event Handling ---

    def handle_mouse_click(self, pos):
        """Converts mouse click position to board coordinates and sets Start/Goal."""
        col = pos[0] // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        p = Point(col, row)

        if not is_on_board(p):
            return

        if self.path_found or self.animating_path:
            self.reset_state()
        elif self.start_pos is None:
            self.start_pos = p
            self.render_pos = self.get_square_coords(p)
        elif self.goal_pos is None and p != self.start_pos:
            self.goal_pos = p
        elif not self.running_bfs:
            # Click again on the board to reset if not running
            self.reset_state()

    def handle_key_press(self, key):
        """Handles keyboard shortcuts for starting BFS and switching pieces."""
        if key == pygame.K_SPACE:
            if self.start_pos and self.goal_pos and not self.running_bfs and not self.path_found:
                self.start_bfs()
        elif key == pygame.K_r:
            self.reset_state()
        elif pygame.K_1 <= key <= pygame.K_5:
            self.current_piece = key - pygame.K_1
            # Reset state but keep start/goal if possible
            if self.start_pos and self.goal_pos:
                s, g = self.start_pos, self.goal_pos
                self.reset_state()
                self.start_pos, self.goal_pos = s, g
                self.render_pos = self.get_square_coords(s)
            else:
                self.reset_state()
                
    def run(self):
        """The main game loop."""
        running = True
        while running:
            current_time = time.time() * 1000 # Convert to milliseconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left click
                        self.handle_mouse_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_press(event.key)

            # Logic Update
            if self.running_bfs:
                # Controlled stepping of BFS based on delay
                if current_time - self.last_bfs_step_time > BFS_DELAY_MS:
                    self.step_bfs()
                    self.last_bfs_step_time = current_time
            elif self.animating_path:
                self.update_animation()

            # Drawing
            self.screen.fill(BLACK) # Clear screen
            self.draw_scene()
            
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    visualizer = BFSVisualizer()
    visualizer.run()