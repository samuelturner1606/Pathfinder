import ctypes
import pygame as pg
import math
import random

vec = pg.math.Vector2  # saves time typing it out...


class Barricade(pg.sprite.Sprite):  # Subclass of PyGame Sprite class
    def __init__(self, radius, colour):
        super().__init__()
        self.image = pg.Surface([2 * radius, 2 * radius])  # creates surface with width and height of 2*radius
        self.image.set_colorkey(pg.Color('black'))  # makes black a transparent colour in the surface
        self.rect = self.image.get_rect()  # PyGame Rect class object of the surface: <rect(x, y, w, h)>
        pg.draw.circle(self.image, colour, self.rect.center, radius)  # draws a circle representing the class graphics
        self._layer = 2  # Since "AllSprites" is a layered group, this affects the order this is drawn to the screen
        self.radius = radius  # hitbox radius
        self.rect.center = MousePos  # drawn at the mouse position when left clicking
        self.health = 1000
        if not pg.sprite.spritecollide(self, Portals, False):  # barricades can't be built on portals
            self.add(AllSprites, Barricades)  # adds itself on creation to these groups

    def update(self, t):
        self.health -= 5  # Every frame, health is reduced
        if self.health <= 0:
            self.kill()  # this means the sprite is removed from all sprite groups containing it, so stops being drawn
        else:
            if MouseState[2]:  # right click. In a more complete version of the game this would be a different condition
                # like Alien hitting them, projectiles, explosions etc
                # region Following code chain deletes barricades
                if self.rect.collidepoint(MousePos):  # If the sprite is being clicked on
                    del_barricades = [self]
                    for c in del_barricades:  # chain reaction as touching barricades are added to the iterated list
                        touching_barricades = pg.sprite.spritecollide(c, Barricades, True, pg.sprite.collide_circle)
                        # True means the colliding sprites are killed
                        [del_barricades.append(t) for t in touching_barricades if t not in del_barricades]
                        # The list comprehension functions the same as doing it with a for loop
                # endregion


class Player(pg.sprite.Sprite):
    def __init__(self, radius, colour):
        super().__init__()
        self.image = pg.Surface([2 * radius, 2 * radius])
        self.image.set_colorkey(pg.Color('black'))
        self.rect = self.image.get_rect()
        pg.draw.circle(self.image, colour, self.rect.center, radius)
        self.rect.x, self.rect.y = ScreenW/2, ScreenH/2
        self._layer = 2
        self.radius = radius
        self.pos = vec(self.rect.centerx, self.rect.centery)  # Not sure why I'm getting yellow warnings with vec(x, y)
        self.vel = vec()
        self.acc = vec()
        self.constant_acc = 0.001  # A variable in a settings file or something could set this when the sprite is made
        self.health = 100
        self.add(AllSprites, Players)

    def update(self, t):
        if pg.sprite.spritecollide(self, Aliens, False, pg.sprite.collide_circle):
            self.health -= 10
            if self.health <= 0:
                self.kill()
                global Running  # Currently the game ends and exits when the player dies
                Running = False

        self.acc = vec()  # resets the acceleration to 0 every frame so that it is constant
        # The player won't accelerate in a direction unless the user is pressing a key
        if KeyState[pg.K_w]:
            self.acc.y = -self.constant_acc
        if KeyState[pg.K_s]:
            self.acc.y = self.constant_acc
        if KeyState[pg.K_a]:
            self.acc.x = -self.constant_acc
        if KeyState[pg.K_d]:
            self.acc.x = self.constant_acc

        # Equations of motion. t doesn't need to be here but it makes the players speed independent from FPS
        self.vel += self.acc * t
        self.pos += self.vel * t + 0.5 * self.acc * t ** 2

        collision = False  # Before checking whether a collision occurs in a frame, the variable is reset to False
        if self.pos.y < self.radius:  # These checks are for collisions with the screen walls
            self.pos.y = self.radius
            collision = True
        if self.pos.x < self.radius:
            self.pos.x = self.radius
            collision = True
        if self.pos.x > ScreenW - self.radius:
            self.pos.x = ScreenW - self.radius
            collision = True
        if self.pos.y > ScreenH - self.radius:
            self.pos.y = ScreenH - self.radius
            collision = True
        # region Player to circle barricade collisions
        # This has bugs because my math isn't quite correct when the collision isn't head on. More details in report
        hit = pg.sprite.spritecollide(self, Barricades, False, pg.sprite.collide_circle)
        if hit:
            collision = True
            new_to_barricade_dist = vec(hit[0].rect.centerx - self.pos.x, hit[0].rect.centery - self.pos.y).length()
            overlap_dist = self.radius + hit[0].radius - new_to_barricade_dist
            # I assume hit[0] is always the first circle it collides with. Unless PyGame doesn't order the list
            if self.vel:  # Can't scale a vec of length 0 so this condition is here
                self.vel.scale_to_length(overlap_dist + 2)  # +n where n is the desired distance away from the surface
                # n gets around my slightly incorrect math
                self.pos -= self.vel  # corrected pos vec = new pos vec that caused collision minus vel
        # endregion
        if collision:
            self.vel = vec()  # reset's vel to 0. Coding elastic collisions is a bit out of my skill level for now

        self.rect.centerx, self.rect.centery = self.pos.x, self.pos.y  # updates the sprite pos to whatever pos vec is


class Portal(pg.sprite.Sprite):
    def __init__(self, x, y, colour):
        super().__init__()
        self.image = pg.Surface(portal_size)
        self.image.set_colorkey(pg.Color('black'))
        self.rect = self.image.get_rect()
        pg.draw.ellipse(self.image, pg.Color(colour), self.rect, 5)
        self._layer = 2
        self.rect.x, self.rect.y = x, y
        self.add(AllSprites, Portals)  # Might be able to fix the portal bugs with an update function like other sprites


class Alien(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pg.Surface([AlienWidth, AlienWidth])  # just a square for now but images can be loaded easily
        self.image.fill(pg.Color('red'))
        self.rect = self.image.get_rect()
        self._layer = 4
        self.rect.x, self.rect.y = random.randint(0, ScreenW - AlienWidth), random.randint(0, ScreenH - AlienWidth)
        # self.rect.x, self.rect.y = 0, 0
        self.radius = AlienWidth/2
        self.max_speed = 0.2
        self.pos = vec(self.rect.x, self.rect.y)
        self.vel = vec()
        self.prev_portal_coord, self.prev_barricade_coord = None, None  # used so pathing behaviour functions properly
        self.path, self.path_list_length, self.path_progress, = [], None, None  # this is just temporary
        self.add(AllSprites, Aliens)

    def update(self, t):
        # if MouseState[0]:  # when user draws barricades, alien will path find again. This can be incorporated into a
            # self.path = []  # difficulty level. Harder difficulty means this is done to make smarter pathing.
        alien_barricade = pg.sprite.spritecollide(self, Barricades, False)
        if alien_barricade:  # if path was obstructed
            for b in alien_barricade:
                b.health -= 10
            if self.prev_barricade_coord != (alien_barricade[0].rect.x, alien_barricade[0].rect.y):
                self.path = []
                self.prev_barricade_coord = (alien_barricade[0].rect.x, alien_barricade[0].rect.y)

        portal_collision = pg.sprite.spritecollide(self, Portals, False, pg.sprite.collide_circle)
        if portal_collision:
            portal_coord = (portal_collision[0].rect.x, portal_collision[0].rect.y)
            if portal_coord != self.prev_portal_coord:
                if portal_coord in PortalDict.keys():
                    portal_other_side = PortalDict[portal_coord]
                else:
                    portal_other_side = rev_portal_dict[portal_coord]
                self.prev_portal_coord = portal_other_side
                self.pos.x, self.pos.y = portal_other_side[0], portal_other_side[1]
                self.rect.x, self.rect.y = self.pos.x, self.pos.y

        if not self.path:  # if alien doesn't have a path
            self.vel = vec()
            self.radius = AlienProximity  # to check if the player is close to trigger aggro path finding
            proximity_collision = pg.sprite.spritecollide(self, Players, False, pg.sprite.collide_circle)
            _Circle(self.rect.centerx, self.rect.centery, AlienProximity, 'green')
            self.radius = AlienWidth/2  # radius changed back
            player_colliding = pg.sprite.spritecollide(self, Players, False, pg.sprite.collide_circle)
            if not player_colliding:
                if proximity_collision:  # alien will search for a path to the player but can use portals in it's path
                    pathfinder(self.radius, (self.pos.x, self.pos.y), self, Players, True, Barricades)
                else:  # it will search until it finds either a portal or player
                    pathfinder(self.radius, (self.pos.x, self.pos.y), self, Players, False, Barricades)
        else:
            if self.path_progress != self.path_list_length:  # meaning alien hasn't finished following the path
                next_path_coord = self.path[self.path_progress]
                _Square(next_path_coord[0], next_path_coord[1], 'darkred')
                next_coord = vec(next_path_coord[0], next_path_coord[1])
                self.vel = next_coord - self.pos
                if self.vel.length() <= self.max_speed * t:  # * t to make vel independent of frame rate
                    self.pos = next_coord
                else:
                    self.vel.scale_to_length(self.max_speed*t)  # this effects how fast the alien travels
                    self.pos += self.vel
                if self.pos == next_coord:
                    self.path_progress += 1
                self.rect.x, self.rect.y = self.pos.x, self.pos.y
            else:  # alien has finished following the path
                self.path = []  # to start path finding again


class _Square(pg.sprite.Sprite):  # used to bug fix the path finder and showcase it
    def __init__(self, x, y, colour):
        super().__init__()
        self.image = pg.Surface([AlienWidth, AlienWidth])
        self.image.set_alpha(100)
        self.image.fill(pg.Color(colour))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self._layer = 1
        self.health = 100  # used so they don't last too long on the screen. A buildup of sprites reduces FPS
        self.add(AllSprites)

    def update(self, t):
        self.health -= 2
        if self.health <= 0:
            self.kill()


class _Circle(pg.sprite.Sprite):  # used to display the AlienProximity
    def __init__(self, x, y, r, colour):
        super().__init__()
        self.image = pg.Surface([2 * r, 2 * r])
        self.image.set_colorkey(pg.Color('black'))
        self.rect = self.image.get_rect()
        self.image.set_alpha(50)
        pg.draw.circle(self.image, pg.Color(colour), self.rect.center, r)
        self.rect.x, self.rect.y = x-r, y-r
        self._layer = 2
        self.health = 100
        self.add(AllSprites)

    def update(self, t):
        self.health -= 10
        if self.health <= 0:
            self.kill()


def pathfinder(r, start_coord, sprite, end_group, is_aggro, obstacle_group):
    # Read my report and view my demo to understand. It's like a dynamic Dijkstra's algorithm that took me weeks to make
    def new_coord_entry(key, value):
        coord_list.append(key)
        coord_dict[key] = value

    def adj__cycle():
        cycle = [(x - d, y - d), (x + d, y + d), (x - d, y + d), (x + d, y - d), (x - d, y), (x, y + d), (x, y - d),
                 (x + d, y)]
        # currently cycle is NW, SE, SW, NE, W, S, N & E. I believe this order to be most efficient
        for adj_coord in cycle:
            sprite.rect.x, sprite.rect.y = adj_coord[0], adj_coord[1]

            if adj_coord[0] != coord[0] and adj_coord[1] != coord[1]:  # meaning adj_coord is in diagonal direction
                distance = d * math.sqrt(2)  # distance to travel to the adj_coord
            else:  # linear direction
                distance = d

            if not path:  # meaning path == [] and algorithm is searching for an end
                sprite_end_collision = pg.sprite.spritecollideany(sprite, end_group)
                sprite_portal_collision = pg.sprite.spritecollideany(sprite, Portals)
                if sprite_end_collision:
                    path.append(adj_coord)
                    _Square(adj_coord[0], adj_coord[1], 'cyan')
                    return 'end found'
                elif sprite_portal_collision and is_aggro:
                    path.append(adj_coord)
                    _Square(adj_coord[0], adj_coord[1], 'cyan')
                    return 'end found'
                elif adj_coord in coord_dict:  # meaning revisited coord
                    if coord_dict[adj_coord] > coord_dict[coord] + distance:  # if travel distance to it can be reduced
                        coord_dict[adj_coord] = coord_dict[coord] + distance  # update existing travel distance
                else:
                    sprite_obstacle_collision = pg.sprite.spritecollideany(sprite, obstacle_group)
                    if not sprite_obstacle_collision and 0 <= adj_coord[0] <= ScreenW-d and 0 <= adj_coord[1] <= ScreenH-d:
                        new_coord_entry(adj_coord, coord_dict[coord] + distance)
                        _Square(adj_coord[0], adj_coord[1], 'cyan')  # You can remove these function calls
                        portal_collision = pg.sprite.spritecollide(sprite, Portals, False, pg.sprite.collide_circle)
                        if portal_collision:
                            portal_coord = (portal_collision[0].rect.x, portal_collision[0].rect.y)
                            if portal_coord in PortalDict.keys():  # for other side of portal
                                portal_other_side = PortalDict[portal_coord]
                                new_coord_entry(portal_other_side, coord_dict[adj_coord])
                            elif portal_coord in PortalDict.values():
                                portal_other_side = rev_portal_dict[portal_coord]
                                new_coord_entry(portal_other_side, coord_dict[adj_coord])
            else:  # pathing stage
                if adj_coord in coord_dict:
                    if adj_coord in PortalDict.keys():
                        adj_coord = PortalDict[adj_coord]  # other side of portal
                    elif adj_coord in PortalDict.values():
                        adj_coord = rev_portal_dict[adj_coord]
                    adj_dict[coord_dict[adj_coord]] = adj_coord  # travel distance: coord, entered into adj_dict

    # maps walkable coord's with travel distance until end found, then paths back through coord's of min distance
    coord_dict, coord_list, path, d = {start_coord: 0}, [start_coord], [], 2*r

    for coord in coord_list:  # previously was iterating over list(coord_dict) explained further in report
        x, y = coord[0], coord[1]
        if adj__cycle() == 'end found':
            break
    # one thing to note coord_list will stop gaining size and iteration will stop if there's no end in an enclosed space
    # print('coord_list: ' + str(coord_list))
    if path:  # meaning end was found
        for path_coord in path:  # starting at the end_node
            x, y, adj_dict = path_coord[0], path_coord[1], {}
            adj__cycle()
            if adj_dict and 0 not in adj_dict:
                path.append(adj_dict[min(a for a in adj_dict)])  # this is finding the coord with least travel cost

        path.reverse()  # because we travelled from end to start. We now flip around so the path is start to end
        # print('path' + str(path))
        for k in path:
            sprite.path.append(k)
            _Square(k[0], k[1], 'magenta')
        sprite.path_list_length, sprite.path_progress = len(path), 0
    sprite.rect.x, sprite.rect.y = start_coord[0], start_coord[1]
    # It was changed for collisions detection between obstacle groups etc, now it needs to be reset back
    # sprite.vel = vec(path[0], path[1]) - sprite.pos , this might have caused some of the of bugs
    sprite.vel = vec(path[0][0], path[0][1]) - sprite.pos


# When coding my game I didn't like having blocks of code I couldn't hide
# so I did some research and learnt to create folds with Ctrl+Alt+T and use commands like Ctrl+Shift+Minus or Plus
# region Initialize Game
ctypes.windll.user32.SetProcessDPIAware()  # Fixes resolution scaling for High DPI Displays Running Windows such as mine
pg.init()
pg.mixer.init()
ScreenW, ScreenH = pg.display.Info().current_w, pg.display.Info().current_h  # one method of getting display size
Screen = pg.display.set_mode((ScreenW, ScreenH), pg.FULLSCREEN)
Clock = pg.time.Clock()
AllSprites = pg.sprite.LayeredUpdates()  # Same as .Group() but sprite._layer is looked at when drawing to screen
Barricades, Portals, Aliens, Players = pg.sprite.Group(), pg.sprite.Group(), pg.sprite.Group(), pg.sprite.Group()

player = Player(10, pg.Color('blue'))  # Spawn player
AlienWidth = 100  # I couldn't easily implement this into function arguments
AlienProximity = 5 * AlienWidth  # this is circular radius that would cause aggressive Alien path finding
alien = Alien()  # Spawns an alien

portal_size = (50, 100)  # Again this would ideally be a function argument or in a settings file
# Portal_colours = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
Portal_colours = ['red']  # Make this list empty if your getting crashes!!!!!!!!!!!!!!!!!!!
# There's a bug somewhere in the path finder function or Alien update function which cause crashes with the portals.
# The concept works in my demo
# There's also a bug where the alien will go off screen if the player is at the screen walls. This causes a crash
PortalDict = {}
for i in range(len(Portal_colours)):
    x1, y1 = random.randint(0, ScreenW - portal_size[0]), random.randint(0, ScreenH - portal_size[1])
    x2, y2 = random.randint(0, ScreenW - portal_size[0]), random.randint(0, ScreenH - portal_size[1])
    Portal(x1, y1, Portal_colours[i])
    Portal(x2, y2, Portal_colours[i])
    PortalDict[(x1, y1)] = (x2, y2)
rev_portal_dict = {v: k for k, v in PortalDict.items()}
# I couldn't find a good module that did two way mapping with the same performance of dictionaries
# endregion

Running = True
while Running:
    ms_per_frame = Clock.tick(60)  # This is the max FPS of the game but it can drop lower
    pg.event.get()
    KeyState = pg.key.get_pressed()
    if KeyState[pg.K_ESCAPE]:
        Running = False  # This is currently the manual exit!
    else:
        # region Check Inputs
        MousePos = pg.mouse.get_pos()
        MouseState = pg.mouse.get_pressed()
        if MouseState[0]:  # creates barricades
            Barricade(20, pg.Color('darkgreen'))
        # endregion
        AllSprites.update(ms_per_frame)
        # region Draw
        Screen.fill(pg.Color('turquoise'))
        AllSprites.draw(Screen)
        pg.display.flip()
        # endregion
pg.quit()
print('Game Over')
# Given more time I would make start / end screens as well as weapon projectiles, health bars, character animations from
# loaded sprite images etc. They would be quite easy to implement given how I've structured the code into sprite classes
