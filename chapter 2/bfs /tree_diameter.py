from time import sleep
import pygame
from math import hypot
from collections import deque
from typing import List, Tuple ,Callable
pygame.init()
white = (255, 255, 255)
green = (0, 255, 0)
blue = (0, 0, 128)
red = (255, 0, 0)
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("tree_diameter")



long_end=None
diameter=None
long_start=None
NODE_RADIUS = 15

selected_node = None

font = pygame.font.SysFont(None, 24)

class Node:
    def __init__(self,pos):
        self.pos=pos
        self.Visited=False
        self.Neighbours=[]
        self.Distance=0

    
class Edge():
    def __init__(self,start,end):
        self.start=start
        self.end=end

    def other_end(self,node): 
        if node == self.end : return self.start
        if node == self.start : return self.end
        return False


nodes = List[Node]
edges = List[Node]


def reset_nodes(nodes:List[Node])->None:
    for node in nodes:
        node.Visited=False
        node.Distance=0

def bfs(draw:Callable, start:Node)-> Node :
    global selected_node
    qeue=deque([start])
    far_node=start
    while(qeue):
        corrent_node=qeue[0]
        if corrent_node.Visited:
            qeue.popleft()
        else:
            for node in corrent_node.Neighbours:
                qeue.append(node)
                if node.Distance==0 and node != start:
                    node.Distance=corrent_node.Distance+1
                    if node.Distance>far_node.Distance:
                        far_node=node
                    
            corrent_node.Visited=True
            selected_node=corrent_node
            draw()
            sleep(0.2)
            qeue.popleft()

    return far_node


def find_diameter(draw:Callable,selected_node:Node)->Tuple[Node, Node]:
    reset_nodes(nodes)
    start=bfs(draw,selected_node)
    sleep(0.5)
    reset_nodes(nodes)
    end=bfs(draw,start)
    return (start,end)
    



def draw():
    WIN.fill((25, 25, 25))
    text = font.render(f'diameter of this tree is : {long_end.Distance if long_end else "?" }', True, green)
    textRect = text.get_rect()
    textRect.center = (WIDTH-120,HEIGHT-20)
    WIN.blit(text, textRect)
    # Draw edges
    for edge in edges:
        pygame.draw.line(WIN, white, edge.start.pos,edge.end.pos, 3)

    # Draw nodes
    for node in nodes:
        pygame.draw.circle(WIN, (100, 180, 255), (node.pos), NODE_RADIUS)
        pygame.draw.circle(WIN, white, (node.pos), NODE_RADIUS, 2)
        text = font.render(f'{node.Distance}', True, green)
        textRect = text.get_rect()
        textRect.center = (node.pos[0],node.pos[1])
        WIN.blit(text, textRect)
    # Highlight selected node
    if selected_node:

        pygame.draw.circle(WIN, green, selected_node.pos, NODE_RADIUS + 4, 2)
    if long_start and long_end:

        pygame.draw.circle(WIN, red, long_start.pos, NODE_RADIUS + 4, 2)
        pygame.draw.circle(WIN, red, long_end.pos, NODE_RADIUS + 4, 2)



    pygame.display.update()

def get_node_at_pos(pos:Tuple[int,int])-> None|Node:
    x, y = pos
    for node in nodes:
        nx,ny=node.pos
        if hypot(nx - x, ny - y) <= NODE_RADIUS:
            return node
    return None

def main():
    global selected_node,long_end,long_start
    run = True
    while run:

        draw()
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                run = False

            # LEFT CLICK → Add node
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if get_node_at_pos(pos) is None:  # Avoid overlapping nodes
                    nodes.append(Node(pos))



            # RIGHT CLICK → Connect nodes
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                pos = event.pos
                clicked = get_node_at_pos(pos)
                # print(edges)
                if clicked:
                    if selected_node is None:
                        selected_node = clicked
                    else:
                        # Create edge if not duplicate
                        if clicked not in selected_node.Neighbours :
                            if selected_node != clicked:
                                selected_node.Neighbours.append(clicked)
                                clicked.Neighbours.append(selected_node)
                                edges.append(Edge(selected_node,clicked))
                        selected_node = None



            # removing selected node and all of it's edges by pressing r 
            if event.type == pygame.KEYDOWN and event.key == pygame.K_DELETE:
                if selected_node:
                    for edge in edges.copy():
                        if edge.other_end(selected_node):
                            edges.remove(edge)
                            del edge
                    nodes.remove(selected_node)
                    del selected_node
                    selected_node=None
                    # count-=1
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                long_end=None
                long_start=None
                reset_nodes(nodes)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:

                if selected_node:
                    long_start,long_end=find_diameter(draw,selected_node)
                    selected_node=None






                





    pygame.quit()

main()
