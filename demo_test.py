import pygame
import random
from math import sqrt


def pathfinder(r, start_coord, end_coord_list, delay, portal_dict):  # r = alien radius, start = it's coord, end = players, vents, etc.
    def draw_circle(pos, colour):
        pygame.draw.circle(ScreenWindow, colour, pos, r)
        pygame.display.update((pos[0]-r, pos[1]-r, d, d))
        pygame.time.delay(delay)

    def new_coord_entry(key, value):
        coord_list.append(key)
        coord_dict[key] = value

    def adj__cycle():
        cycle = [(x-d, y-d), (x+d, y+d), (x-d, y+d), (x+d, y-d), (x-d, y), (x, y+d), (x, y-d), (x+d, y)]
        # currently cycle is NW, SE, SW, NE, W, S, N & E. I believe this order to be most efficient
        for adj_coord in cycle:

            if adj_coord[0] != coord[0] and adj_coord[1] != coord[1]:  # meaning adj_coord is in diagonal direction
                distance = d * sqrt(2)  # distance to travel to the adj_coord
            else:  # linear direction
                distance = d

            if not path:  # meaning path == [] and algorithm is searching for an end
                if adj_coord in end_coord_list:
                    if adj_coord != start_coord:  # used so when start = end, no path is returned but not essential
                        path.append(adj_coord)
                    return 'end found'
                elif adj_coord in coord_dict:  # meaning revisited coord
                    if coord_dict[adj_coord] > coord_dict[coord] + distance:  # if travel distance to it can be reduced
                        coord_dict[adj_coord] = coord_dict[coord] + distance  # update existing travel distance
                elif adj_coord not in obstacles and 320 <= adj_coord[0] <= 1480 and 200 <= adj_coord[1] <= 1000:
                    new_coord_entry(adj_coord, coord_dict[coord] + distance)
                    if adj_coord not in forward and adj_coord not in backward:
                        draw_circle(adj_coord, (75, 75, 75))
                    if adj_coord in portal_dict.keys():  # for other side of portal
                        new_coord_entry(portal_dict[adj_coord], coord_dict[adj_coord])
                    if adj_coord in portal_dict.values():
                        new_coord_entry(rev_portal_dict[adj_coord], coord_dict[adj_coord])

            else:  # pathing stage
                if adj_coord in coord_dict:
                    if adj_coord in portal_dict.keys():
                        adj_coord = portal_dict[adj_coord]  # other side of portal
                    elif adj_coord in portal_dict.values():
                        adj_coord = rev_portal_dict[adj_coord]
                    adj_dict[coord_dict[adj_coord]] = adj_coord  # travel distance: coord, entered into adj_dict
                    if adj_coord != start_coord and adj_coord not in forward and adj_coord not in backward:
                        draw_circle(adj_coord, (125, 125, 125))

    # maps walkable coord's with travel distance until end found, then paths back through coord's of min distance
    coord_dict, coord_list, path, d = {start_coord: 0}, [start_coord], [], 2 * r
    rev_portal_dict = {v: k for k, v in portal_dict.items()}
    pygame.draw.circle(ScreenWindow, (0, 255, 0), start_coord, r)
    for z in end_coord_list:
        pygame.draw.circle(ScreenWindow, (0, 100, 0), z, r)
    for j in obstacles:
        pygame.draw.circle(ScreenWindow, (255, 255, 255), j, r)
    n = 10
    m = 240
    for a, b in portal_dict.items():
        n += 45
        m -=45
        portals_colour = (n, 0, m)
        pygame.draw.circle(ScreenWindow, portals_colour, a, r)
        pygame.draw.circle(ScreenWindow, portals_colour, b, r)
    pygame.display.flip()

    for coord in coord_list:  # previously was iterating over list(coord_dict) but that is just an instance
        x, y = coord[0], coord[1]
        if adj__cycle() == 'end found':
            break  # coord_list will stop gaining size and iteration will stop if there's no end in an enclosed space

    if path:  # meaning end was found
        for path_coord in path:  # starting at the end_node
            if path_coord not in end_coord_list:
                draw_circle(path_coord, (0, 50, 0))
            x, y, adj_dict = path_coord[0], path_coord[1], {}
            adj__cycle()
            if adj_dict and 0 not in adj_dict:
                path.append(adj_dict[min(i for i in adj_dict)])
    path.reverse()
    for k in path:
        draw_circle(k, (0, 200, 0))
    global path_finder_finished
    path_finder_finished = True


pygame.init()
pygame.mixer.init()
w, h = pygame.display.Info().current_w, pygame.display.Info().current_h  # one method of getting display size
ScreenWindow = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
ScreenWindow.fill((0, 0, 0))

start = (random.randint(9, 36) * 40, random.randint(7, 23) * 40)
end = []
for i in range(3):
    a = (random.randint(9, 36) * 40, random.randint(10, 20) * 40)
    b = (random.randint(9, 36) * 40, random.randint(10, 20) * 40)
    end.append(a)


forward = []
backward = []
portals = {}
for i in range(5):
    a = (random.randint(9, 36) * 40, random.randint(7, 23) * 40)
    b = (random.randint(9, 36) * 40, random.randint(7, 23) * 40)
    if (a,b) != start and (a,b) not in end:
        forward.append(a), backward.append(b)
        portals[a] = b

obstacles = []

for i in range(300):
    n = (random.randint(8, 37)*40, random.randint(10, 20)*40)
    if n != start and n not in end and n not in portals:
        obstacles.append(n)

Running = True
path_finder_finished = False
while Running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            Running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            Running = False
    if not path_finder_finished:
        pathfinder(20, start, end, 100, portals)

pygame.quit()
