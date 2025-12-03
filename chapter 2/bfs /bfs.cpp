// main.cpp
#include <GLFW/glfw3.h>
#include <iostream>
#include <vector>
#include <deque>
#include <set>
#include <map>
#include <cmath>
#include <thread>
#include <chrono>
#include <functional>
#include <string>

const int SCREEN_WIDTH = 640;
const int SCREEN_HEIGHT = 640;
const int BOARD_SIZE = 8;
const int SQUARE_SIZE = SCREEN_WIDTH / BOARD_SIZE;
const float PI = 3.14159265359f;

// Colors (R, G, B) - Helper struct
struct Color {
    float r, g, b;
};

const Color WHITE = {1.0f, 1.0f, 1.0f};
const Color BLACK = {0.0f, 0.0f, 0.0f};
const Color GRAY_LIGHT = {240/255.0f, 217/255.0f, 181/255.0f};
const Color GRAY_DARK = {181/255.0f, 136/255.0f, 99/255.0f};
const Color BLUE_VISITED = {100/255.0f, 149/255.0f, 237/255.0f};
const Color YELLOW_CURRENT = {1.0f, 215/255.0f, 0.0f};
const Color GREEN_PATH = {50/255.0f, 205/255.0f, 50/255.0f};
const Color RED_GOAL = {220/255.0f, 20/255.0f, 60/255.0f};
const Color EDGE_COLOR = {50/255.0f, 50/255.0f, 50/255.0f};

// Point Helper
struct Point {
    int x, y;
    bool operator<(const Point& other) const {
        if (x != other.x) return x < other.x;
        return y < other.y;
    }
    bool operator==(const Point& other) const {
        return x == other.x && y == other.y;
    }
    bool operator!=(const Point& other) const {
        return !(*this == other);
    }
};

enum PieceType { KNIGHT_P, KING_P, ROOK_P, BISHOP_P, QUEEN_P };

// Pre-declared movement function type
using MoveFunc = std::function<std::vector<Point>(const Point&)>;

// Knight Moves (unchanged)
const std::vector<Point> KNIGHT_MOVES = {
    {2, 1}, {2, -1}, {-2, 1}, {-2, -1},
    {1, 2}, {1, -2}, {-1, 2}, {-1, -2}
};

// --- Movement functions for all pieces ---

std::vector<Point> knightMoves(const Point& p) {
    std::vector<Point> out;
    for (const auto &m : KNIGHT_MOVES) {
        Point n = {p.x + m.x, p.y + m.y};
        if (n.x >= 0 && n.x < BOARD_SIZE && n.y >= 0 && n.y < BOARD_SIZE) out.push_back(n);
    }
    return out;
}

std::vector<Point> kingMoves(const Point& p) {
    std::vector<Point> out;
    for (int dx = -1; dx <= 1; dx++) {
        for (int dy = -1; dy <= 1; dy++) {
            if (dx == 0 && dy == 0) continue;
            Point n = {p.x + dx, p.y + dy};
            if (n.x >= 0 && n.x < BOARD_SIZE && n.y >= 0 && n.y < BOARD_SIZE) out.push_back(n);
        }
    }
    return out;
}

// sliding helper: iterate in direction until edge
std::vector<Point> slidingMoves(const Point& p, const std::vector<std::pair<int,int>>& dirs) {
    std::vector<Point> out;
    for (auto d : dirs) {
        int dx = d.first, dy = d.second;
        int nx = p.x + dx, ny = p.y + dy;
        while (nx >= 0 && nx < BOARD_SIZE && ny >= 0 && ny < BOARD_SIZE) {
            out.push_back({nx, ny});
            nx += dx; ny += dy;
        }
    }
    return out;
}

std::vector<Point> rookMoves(const Point& p) {
    static const std::vector<std::pair<int,int>> dirs = {
        {1,0},{-1,0},{0,1},{0,-1}
    };
    return slidingMoves(p, dirs);
}

std::vector<Point> bishopMoves(const Point& p) {
    static const std::vector<std::pair<int,int>> dirs = {
        {1,1},{1,-1},{-1,1},{-1,-1}
    };
    return slidingMoves(p, dirs);
}

std::vector<Point> queenMoves(const Point& p) {
    static const std::vector<std::pair<int,int>> dirs = {
        {1,0},{-1,0},{0,1},{0,-1},
        {1,1},{1,-1},{-1,1},{-1,-1}
    };
    return slidingMoves(p, dirs);
}

// --- Visualizer class (adapted) ---
class KnightBFSVisualizer {
private:
    GLFWwindow* window;
    
    // State
    Point startPos = {-1, -1};
    Point goalPos = {-1, -1};
    bool hasStart = false;
    bool hasGoal = false;
    bool runningBFS = false;
    bool pathFound = false;
    bool animatingPath = false;
    
    // BFS Data
    std::deque<Point> queue;
    std::set<Point> visited;
    std::map<Point, Point> parents;
    std::vector<std::pair<Point, Point>> edgesExplored;
    Point currentNode = {-1, -1};
    
    // Path Animation Data
    std::vector<Point> shortestPath;
    size_t animIndex = 0;
    float animProgress = 0.0f;
    float renderX = -100.0f, renderY = -100.0f; // Offscreen initially

    // Timing
    double lastBFSStepTime = 0.0;

    // Piece selection
    PieceType currentPiece = KNIGHT_P;
    MoveFunc movementFunction = knightMoves;

public:

    KnightBFSVisualizer() {
        if (!glfwInit()) {
            std::cerr << "Failed to initialize GLFW" << std::endl;
            exit(-1);
        }

        window = glfwCreateWindow(SCREEN_WIDTH, SCREEN_HEIGHT, "Chess-Piece BFS Visualizer - C++ OpenGL", NULL, NULL);
        if (!window) {
            glfwTerminate();
            exit(-1);
        }

        glfwMakeContextCurrent(window);
        
        // Setup 2D Orthographic Projection (0,0 at top-left)
        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1);
        glMatrixMode(GL_MODELVIEW);
        
        // Input Callbacks
        glfwSetWindowUserPointer(window, this);
        glfwSetMouseButtonCallback(window, mouseCallback);
        glfwSetKeyCallback(window, keyCallback);
        
        reset();
    }

    ~KnightBFSVisualizer() {
        glfwDestroyWindow(window);
        glfwTerminate();
    }

    void reset() {
        hasStart = false;
        hasGoal = false;
        runningBFS = false;
        pathFound = false;
        animatingPath = false;
        
        queue.clear();
        visited.clear();
        parents.clear();
        edgesExplored.clear();
        shortestPath.clear();
        
        animIndex = 0;
        animProgress = 0.0f;
        renderX = -100.0f;
        currentNode = {-1,-1};
    }

    void setPiece(PieceType p) {
        currentPiece = p;
        switch(p) {
            case KNIGHT_P: movementFunction = knightMoves; break;
            case KING_P:   movementFunction = kingMoves; break;
            case ROOK_P:   movementFunction = rookMoves; break;
            case BISHOP_P: movementFunction = bishopMoves; break;
            case QUEEN_P:  movementFunction = queenMoves; break;
            default: movementFunction = knightMoves; break;
        }
    }

    void startBFS() {
        if (!hasStart || !hasGoal) return;
        runningBFS = true;
        queue.clear();
        visited.clear();
        parents.clear();
        edgesExplored.clear();
        shortestPath.clear();
        queue.push_back(startPos);
        visited.insert(startPos);
        parents[startPos] = {-1, -1};
        currentNode = {-1,-1};
        lastBFSStepTime = glfwGetTime();
    }

    void stepBFS() {
        if (queue.empty()) {
            runningBFS = false;
            return;
        }

        Point current = queue.front();
        queue.pop_front();
        currentNode = current;

        if (current == goalPos) {
            reconstructPath();
            runningBFS = false;
            pathFound = true;
            animatingPath = true;
            animIndex = 0;
            animProgress = 0.0f;
            // Place render at start of path
            if (!shortestPath.empty()) {
                renderX = shortestPath[0].x * SQUARE_SIZE;
                renderY = shortestPath[0].y * SQUARE_SIZE;
            }
            return;
        }
        // visited.insert(current);
        // Generate neighbors using selected movement function
        std::vector<Point> neighbors = movementFunction(current);
        for (const auto& neighbor : neighbors) {
            if (visited.find(neighbor) == visited.end()) {
                visited.insert(neighbor);
                parents[neighbor] = current;
                queue.push_back(neighbor);
                edgesExplored.push_back({current, neighbor});
            }
        }

        // optional little sleep to visually pace the BFS
        std::this_thread::sleep_for(std::chrono::milliseconds(60));
    }

    void reconstructPath() {
        Point curr = goalPos;
        std::vector<Point> tempPath;
        while (curr.x != -1) { // While not null parent
            tempPath.push_back(curr);
            if (curr == startPos) break;
            curr = parents[curr];
        }
        shortestPath.clear();
        for (int i = (int)tempPath.size() - 1; i >= 0; --i) {
            shortestPath.push_back(tempPath[i]);
        }
    }

    void updateAnimation() {
        if (shortestPath.empty()) return;
        if (animIndex >= shortestPath.size() - 1) {
            // finished
            animatingPath = false;
            renderX = shortestPath.back().x * SQUARE_SIZE;
            renderY = shortestPath.back().y * SQUARE_SIZE;
            return;
        }

        float speed = 0.06f; // tweak per taste
        animProgress += speed;

        Point startNode = shortestPath[animIndex];
        Point endNode = shortestPath[animIndex + 1];

        float sx = startNode.x * SQUARE_SIZE;
        float sy = startNode.y * SQUARE_SIZE;
        float ex = endNode.x * SQUARE_SIZE;
        float ey = endNode.y * SQUARE_SIZE;

        float curX = sx + (ex - sx) * animProgress;
        float curY = sy + (ey - sy) * animProgress;

        // Jump effect for knight-like motion; smaller for other pieces
        float jumpHeight = (currentPiece == KNIGHT_P) ? 20.0f : 8.0f;
        float jumpOffset = std::sin(animProgress * PI) * jumpHeight;

        renderX = curX;
        renderY = curY - jumpOffset;

        if (animProgress >= 1.0f) {
            animProgress = 0.0f;
            animIndex++;
            renderX = ex;
            renderY = ey;
        }
    }

    // --- Drawing Helpers ---

    void drawRect(float x, float y, float w, float h, Color c, bool filled = true) {
        glColor3f(c.r, c.g, c.b);
        if (filled) glBegin(GL_QUADS);
        else glBegin(GL_LINE_LOOP);
        
        glVertex2f(x, y);
        glVertex2f(x + w, y);
        glVertex2f(x + w, y + h);
        glVertex2f(x, y + h);
        
        glEnd();
    }

    void drawCircle(float cx, float cy, float r, Color c) {
        glColor3f(c.r, c.g, c.b);
        glBegin(GL_TRIANGLE_FAN);
        glVertex2f(cx, cy);
        int segments = 24;
        for (int i = 0; i <= segments; i++) {
            float theta = 2.0f * PI * float(i) / float(segments);
            float dx = r * cosf(theta);
            float dy = r * sinf(theta);
            glVertex2f(cx + dx, cy + dy);
        }
        glEnd();
    }

    void drawLine(float x1, float y1, float x2, float y2, Color c, float width) {
        glLineWidth(width);
        glColor3f(c.r, c.g, c.b);
        glBegin(GL_LINES);
        glVertex2f(x1, y1);
        glVertex2f(x2, y2);
        glEnd();
    }

    // Draw a simple symbol for each piece inside square at sx,sy (top-left)
    void drawPieceSymbol(const Point& p, PieceType piece, float sx, float sy) {
        float cx = sx + SQUARE_SIZE / 2.0f;
        float cy = sy + SQUARE_SIZE / 2.0f;
        float baseR = SQUARE_SIZE / 4.0f;

        switch (piece) {
            case KNIGHT_P:
                // Circle + small square center (like before)
                drawCircle(cx, cy - 4, baseR, {0.1f, 0.1f, 0.1f});
                drawCircle(cx, cy - 4, baseR - 3, WHITE);
                drawRect(cx - 6, cy - 6, 12, 12, BLACK);
                break;
            case KING_P:
                // Big circle + cross
                drawCircle(cx, cy, baseR, {0.15f, 0.15f, 0.15f});
                drawRect(cx - 3, cy - baseR/1.5f, 6, baseR/1.5f, WHITE);
                drawLine(cx - 8, cy - 2, cx + 8, cy - 2, BLACK, 3.0f);
                drawLine(cx, cy - 12, cx, cy + 6, BLACK, 3.0f);
                break;
            case ROOK_P:
                // Rectangle tower with notch
                drawRect(cx - baseR, cy - baseR + 4, baseR*2, baseR*1.6f, {0.1f,0.1f,0.1f});
                drawRect(cx - baseR + 4, cy - baseR + 8, baseR*2 - 8, baseR*1.2f, WHITE);
                // top battlements
                drawRect(cx - baseR, cy - baseR, baseR/2.0f, baseR/2.0f, BLACK);
                drawRect(cx, cy - baseR, baseR/2.0f, baseR/2.0f, BLACK);
                drawRect(cx + baseR/2.0f, cy - baseR, baseR/2.0f, baseR/2.0f, BLACK);
                break;
            case BISHOP_P:
                // Tall ellipse + diagonal cut (simple)
                drawCircle(cx, cy, baseR, {0.12f,0.12f,0.12f});
                drawCircle(cx, cy, baseR - 3, WHITE);
                // draw a slanted line (cut)
                drawLine(cx - 6, cy + 6, cx + 6, cy - 6, BLACK, 3.0f);
                break;
            case QUEEN_P:
                // Crown: three small circles on top + base
                drawRect(cx - baseR, cy - baseR/2.0f, baseR*2, baseR*1.2f, {0.12f,0.12f,0.12f});
                drawCircle(cx - baseR/2.0f + 2, cy - baseR/1.5f, baseR/4.0f, BLACK);
                drawCircle(cx, cy - baseR/1.5f, baseR/4.0f, BLACK);
                drawCircle(cx + baseR/2.0f - 2, cy - baseR/1.5f, baseR/4.0f, BLACK);
                break;
            default:
                drawCircle(cx, cy, baseR, BLACK);
                break;
        }
    }

    void draw() {
        glClear(GL_COLOR_BUFFER_BIT);

        // 1. Draw Board
        for (int r = 0; r < BOARD_SIZE; r++) {
            for (int c = 0; c < BOARD_SIZE; c++) {
                Color color = ((r + c) % 2 == 0) ? GRAY_LIGHT : GRAY_DARK;
                drawRect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE, color);
            }
        }

        // 2. Draw Visited
        for (const auto& p : visited) {
            if (p == startPos || p == goalPos) continue;
            drawRect(p.x * SQUARE_SIZE + 2, p.y * SQUARE_SIZE + 2, SQUARE_SIZE - 4, SQUARE_SIZE - 4, BLUE_VISITED);
        }

        // 3. Current Node
        if (runningBFS && currentNode.x != -1) {
             drawRect(currentNode.x * SQUARE_SIZE + 4, currentNode.y * SQUARE_SIZE + 4, SQUARE_SIZE - 8, SQUARE_SIZE - 8, YELLOW_CURRENT);
        }

        // 4. Edges
        for (const auto& edge : edgesExplored) {
            float sx = edge.first.x * SQUARE_SIZE + SQUARE_SIZE/2;
            float sy = edge.first.y * SQUARE_SIZE + SQUARE_SIZE/2;
            float ex = edge.second.x * SQUARE_SIZE + SQUARE_SIZE/2;
            float ey = edge.second.y * SQUARE_SIZE + SQUARE_SIZE/2;
            drawLine(sx, sy, ex, ey, EDGE_COLOR, 2.0f);
        }

        // 5. Shortest Path Overlay
        if (pathFound) {
            glLineWidth(4.0f);
            for (const auto& p : shortestPath) {
                drawRect(p.x * SQUARE_SIZE + 5, p.y * SQUARE_SIZE + 5, SQUARE_SIZE - 10, SQUARE_SIZE - 10, GREEN_PATH, false);
            }
        }

        // 6. Icons: start & goal
        if (hasStart) {
             // draw piece symbol at start (using currently selected piece type for visualization)
             drawPieceSymbol(startPos, currentPiece, startPos.x * SQUARE_SIZE, startPos.y * SQUARE_SIZE);
        }
        if (hasGoal) {
            float cx = goalPos.x * SQUARE_SIZE + SQUARE_SIZE/2;
            float cy = goalPos.y * SQUARE_SIZE + SQUARE_SIZE/2;
            drawCircle(cx, cy, SQUARE_SIZE/3, RED_GOAL);
        }

        // 7. Render moving piece (renderX/renderY)
        if (hasStart && !animatingPath && !runningBFS && !pathFound) {
             // Static at start
             renderX = startPos.x * SQUARE_SIZE;
             renderY = startPos.y * SQUARE_SIZE;
        }

        if (renderX >= 0) {
            // Draw piece depending on currentPiece at renderX,renderY (top-left)
            Point rp = {(int)(renderX / SQUARE_SIZE), (int)(renderY / SQUARE_SIZE)};
            drawPieceSymbol(rp, currentPiece, renderX, renderY);
        }


        glfwSwapBuffers(window);
    }

    void run() {
        while (!glfwWindowShouldClose(window)) {
            // Logic
            if (runningBFS) {
                double currentTime = glfwGetTime();
                if (currentTime - lastBFSStepTime > 0.02) {
                    stepBFS();
                    lastBFSStepTime = currentTime;
                }
            } else if (animatingPath) {
                updateAnimation();
                std::this_thread::sleep_for(std::chrono::milliseconds(18)); // ~60 FPS cap
            }

            draw();
            glfwPollEvents();
        }
    }

    // Input Handling
    void onMouseClick(int button, int action, int mods) {
        if (button == GLFW_MOUSE_BUTTON_LEFT && action == GLFW_PRESS) {
            double xpos, ypos;
            glfwGetCursorPos(window, &xpos, &ypos);
            int col = (int)xpos / SQUARE_SIZE;
            int row = (int)ypos / SQUARE_SIZE;

            if (col < 0 || col >= BOARD_SIZE || row < 0 || row >= BOARD_SIZE) return;

            if (pathFound || animatingPath) {
                reset();
            } else if (!hasStart) {
                startPos = {col, row};
                hasStart = true;
                renderX = col * SQUARE_SIZE;
                renderY = row * SQUARE_SIZE;
            } else if (!hasGoal && (col != startPos.x || row != startPos.y)) {
                goalPos = {col, row};
                hasGoal = true;
            } else if (!runningBFS) {
                // clicking again resets
                reset();
            }
        }
    }
    void onKey(int key, int scancode, int action, int mods) {
        if (action == GLFW_PRESS) {
            if (key == GLFW_KEY_SPACE) {
                if (hasStart && hasGoal && !runningBFS && !pathFound) {
                    startBFS();
                }
            }
            // Piece switching: 1-5
            if (key == GLFW_KEY_1) setPiece(KNIGHT_P);
            if (key == GLFW_KEY_2) setPiece(KING_P);
            if (key == GLFW_KEY_3) setPiece(ROOK_P);
            if (key == GLFW_KEY_4) setPiece(BISHOP_P);
            if (key == GLFW_KEY_5) setPiece(QUEEN_P);

            // reset with R
            if (key == GLFW_KEY_R) {
                reset();
            }
        }
    }

    // Static wrappers for GLFW callbacks
    static void mouseCallback(GLFWwindow* window, int button, int action, int mods) {
        KnightBFSVisualizer* app = static_cast<KnightBFSVisualizer*>(glfwGetWindowUserPointer(window));
        if (app) app->onMouseClick(button, action, mods);
    }

    static void keyCallback(GLFWwindow* window, int key, int scancode, int action, int mods) {
        KnightBFSVisualizer* app = static_cast<KnightBFSVisualizer*>(glfwGetWindowUserPointer(window));
        if (app) app->onKey(key, scancode, action, mods);
    }
};

int main() {
    KnightBFSVisualizer app;
    // default piece is knight - it's already set
    app.run();
    return 0;
}
