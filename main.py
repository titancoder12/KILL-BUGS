try:
    import asyncio
except Exception:
    import pygbag.aio as asyncio

import random, math, os
import pygame

# Screen dimensions
WIDTH, HEIGHT = 1000, 1000
# Boid settings
NUM_BOIDS = 10
MAX_SPEED = 5
MAX_FORCE = 1
OBJECT_PUSH_FORCE = 0.2
NEIGHBOR_RADIUS = 200
SEPARATION_RADIUS = 30
OBJECT_SEPERATION_RADIUS = 50
TRIANGLE_SIZE = 5
ATTRACTION_RADIUS = 100
OBJECTS_IN_GOAL = False  # Flag to check if all objects are in the goal
BROADCAST_RADIUS = 100
TARGET_HOLD_TIME = 3000  # 3 seconds in milliseconds
target_start_time = None  # Tracks when all objects entered the target
QUEENS = 1
WORKERS = 10
LARVA = 0
FOOD = 0
KILLS = 0
BOOT_EQUIPPED = False
LEVEL = 1

# Game states
GAME_STATE_MENU = "menu"
GAME_STATE_KILL_TUTORIAL = "kill_tutorial"
GAME_STATE_DONT_DIE_TUTORIAL = "dont_die_tutorial"
GAME_STATE_MAIN_GAME = "main_game"
current_game_state = GAME_STATE_MENU

def render_UI(screen, boids):
    global NUM_BOIDS, MAX_SPEED, MAX_FORCE, NEIGHBOR_RADIUS, SEPARATION_RADIUS, OBJECT_SEPERATION_RADIUS, WIDTH, HEIGHT
    font = pygame.font.SysFont(None, 15)

    a = 140
    b = 10
    c = 50
    d = 10

    button_add_boids = pygame.Rect(a, b, c, d)  # Button to add boids
    button_remove_boids = pygame.Rect(a+60, b, c, d)  # Button to remove boids
    button_add_speed = pygame.Rect(a, b+20, c, d)  # Button to increase speed
    button_remove_speed = pygame.Rect(a+60, b+20, c, d)
    button_add_force = pygame.Rect(a, b+40, c, d)  # Button to increase force
    button_remove_force = pygame.Rect(a+60, b+40, c, d)
    button_add_neighbor_radius = pygame.Rect(a, b+60, c, d)
    button_remove_neighbor_radius = pygame.Rect(a+60, b+60, c, d)
    button_add_separation_radius = pygame.Rect(a, b+80, c, d)
    button_remove_separation_radius = pygame.Rect(a+60, b+80, c, d)
    button_add_object_separation_radius = pygame.Rect(a, b+100, c, d)
    button_remove_object_separation_radius = pygame.Rect(a+60, b+100, c, d)
    button_hatch_worker = pygame.Rect(a+60, b+240, c+40, d)
    button_hatch_queen = pygame.Rect(a+60, b+260, c+40, d)

    pygame.draw.rect(screen, (255, 255, 255), button_add_boids)
    pygame.draw.rect(screen, (255, 255, 255), button_remove_boids)
    pygame.draw.rect(screen, (255, 255, 255), button_add_speed)
    pygame.draw.rect(screen, (255, 255, 255), button_remove_speed)
    pygame.draw.rect(screen, (255, 255, 255), button_add_force)
    pygame.draw.rect(screen, (255, 255, 255), button_remove_force)
    pygame.draw.rect(screen, (255, 255, 255), button_add_neighbor_radius)
    pygame.draw.rect(screen, (255, 255, 255), button_remove_neighbor_radius)
    pygame.draw.rect(screen, (255, 255, 255), button_add_separation_radius)
    pygame.draw.rect(screen, (255, 255, 255), button_remove_separation_radius)
    pygame.draw.rect(screen, (255, 255, 255), button_add_object_separation_radius)
    pygame.draw.rect(screen, (255, 255, 255), button_remove_object_separation_radius)
    pygame.draw.rect(screen, (255, 255, 255), button_hatch_worker)
    pygame.draw.rect(screen, (255, 255, 255), button_hatch_queen)

    for button, label in [
            (button_add_boids, "+"),
            (button_remove_boids, "-"),
            (button_add_speed, "+"),
            (button_remove_speed, "-"),
            (button_add_force, "+"),
            (button_remove_force, "-"),
            (button_add_neighbor_radius, "+"),
            (button_remove_neighbor_radius, "-"),
            (button_add_separation_radius, "+"),
            (button_remove_separation_radius, "-"),
            (button_add_object_separation_radius, "+"),
            (button_remove_object_separation_radius, "-")
        ]:
            text = font.render(label, True, (0, 0, 0))  # Black text
            text_rect = text.get_rect(center=button.center)
            screen.blit(text, text_rect)

    boid_count_text = font.render(f"LEVEL {LEVEL}", True, (255, 255, 255))  # White text
    max_speed_text = font.render(f"Max Speed: {MAX_SPEED}", True, (255, 255, 255))
    max_force_text = font.render(f"Max Force: {round(MAX_FORCE, 2)}", True, (255, 255, 255))
    neighbor_radius_text = font.render(f"Neighbor Radius: {NEIGHBOR_RADIUS}", True, (255, 255, 255))
    separation_radius_text = font.render(f"Separation Radius: {SEPARATION_RADIUS}", True, (255, 255, 255))
    width_text = font.render(f"Window Width: {WIDTH}", True, (255, 255, 255))
    height_text = font.render(f"Window Height: {HEIGHT}", True, (255, 255, 255))
    object_separation_radius_text = font.render(f"Object Separation: {OBJECT_SEPERATION_RADIUS}", True, (255, 255, 255))
    queens_text = font.render(f"Queens: {QUEENS}", True, (255, 255, 255))
    larva_text = font.render(f"Larva: {LARVA}", True, (255, 255, 255))
    food_text = font.render(f"Food: {FOOD}", True, (255, 255, 255))
    worker_text = font.render(f"Workers: {len(boids)}", True, (255, 255, 255))
    hatch_worker_text = font.render(f"Hatch Worker for 10 food and 1 larva", True, (255, 255, 255))
    hatch_queen_text = font.render(f"Hatch Queen for 500 food and 10 larva", True, (255, 255, 255))

    # Draw it on screen at top-left
    screen.blit(boid_count_text, (10, 10))  # Position: (x=10, y=10)
    screen.blit(max_speed_text, (10, 30))
    screen.blit(max_force_text, (10, 50))
    screen.blit(neighbor_radius_text, (10, 70))
    screen.blit(separation_radius_text, (10, 90))
    screen.blit(object_separation_radius_text, (10, 110))
    screen.blit(width_text, (10, 130))
    screen.blit(height_text, (10, 150))
    screen.blit(queens_text, (10, 170))
    screen.blit(larva_text, (10, 190))
    screen.blit(food_text, (10, 210))
    screen.blit(worker_text, (10, 230))
    screen.blit(hatch_worker_text, (10, 250))
    screen.blit(hatch_queen_text, (10, 270))

    return [
        button_add_boids,
        button_remove_boids,
        button_add_speed,
        button_remove_speed,
        button_add_force,
        button_remove_force,
        button_add_neighbor_radius,
        button_remove_neighbor_radius,
        button_add_separation_radius,
        button_remove_separation_radius,
        button_add_object_separation_radius,
        button_remove_object_separation_radius,
        button_hatch_worker,
        button_hatch_queen,
    ]

# Declare mouse_held as a global variable
mouse_held = False
last_add_time = 0  # Initialize outside the function

def manage_UI(buttons, boids, movable_objects, splats):
    global WIDTH, HEIGHT, MAX_SPEED, MAX_FORCE, NEIGHBOR_RADIUS, SEPARATION_RADIUS, OBJECT_SEPERATION_RADIUS, mouse_held, last_add_time, FOOD, LARVA, WORKERS, QUEENS
    dragging_object = False  # Flag to check if an object is being dragged

    button_add_boids = buttons[0]
    button_remove_boids = buttons[1]
    button_add_speed = buttons[2]
    button_remove_speed = buttons[3]
    button_add_force = buttons[4]
    button_remove_force = buttons[5]
    button_add_neighbor_radius = buttons[6]
    button_remove_neighbor_radius = buttons[7]
    button_add_separation_radius = buttons[8]
    button_remove_separation_radius = buttons[9]
    button_add_object_separation_radius = buttons[10]
    button_remove_object_separation_radius = buttons[11]
    button_hatch_worker = buttons[12]
    button_hatch_queen = buttons[13]
    
    dragging = False
    for event in pygame.event.get():
        
        if BOOT_EQUIPPED:
            mouse_pos = pygame.Vector2(event.pos)
            # Make the boot follow the mouse position
            for obj in movable_objects:
                obj.position = pygame.Vector2(pygame.mouse.get_pos())

        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_held = True
            found_object = False
            
            if (not found_object):
                global KILLS
                mouse_pos = pygame.Vector2(event.pos)
                boids_to_remove = [boid for boid in boids if boid.position.distance_to(mouse_pos) < 20]

                KILLS += len(boids_to_remove)
                for boid in boids_to_remove:
                    boid.die(boids, splats)
                print(f"Total kills: {KILLS}")

    # Get the current time
    current_time = pygame.time.get_ticks()

    # Check if the mouse is held and throttle actions
    if not dragging and mouse_held and current_time - last_add_time > 50:  # 50ms delay
        mouse_pos = pygame.mouse.get_pos()

        if button_add_boids.collidepoint(mouse_pos):
            new_boid = Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT))
            boids.append(new_boid)
        elif button_remove_boids.collidepoint(mouse_pos):
            if boids:
                boids.pop()
        elif button_add_speed.collidepoint(mouse_pos):
            MAX_SPEED += 1
        elif button_remove_speed.collidepoint(mouse_pos):
            if MAX_SPEED > 1:
                MAX_SPEED -= 1
        elif button_add_force.collidepoint(mouse_pos):
            MAX_FORCE += 0.1
        elif button_remove_force.collidepoint(mouse_pos):
            if MAX_FORCE > 0.1:
                MAX_FORCE -= 0.1
        elif button_add_neighbor_radius.collidepoint(mouse_pos):
            NEIGHBOR_RADIUS += 10
        elif button_remove_neighbor_radius.collidepoint(mouse_pos):
            if NEIGHBOR_RADIUS > 10:
                NEIGHBOR_RADIUS -= 10
        elif button_add_separation_radius.collidepoint(mouse_pos):
            SEPARATION_RADIUS += 10
        elif button_remove_separation_radius.collidepoint(mouse_pos):
            if SEPARATION_RADIUS > 10:
                SEPARATION_RADIUS -= 10
        elif button_add_object_separation_radius.collidepoint(mouse_pos):
            OBJECT_SEPERATION_RADIUS += 10
        elif button_remove_object_separation_radius.collidepoint(mouse_pos):
            if OBJECT_SEPERATION_RADIUS > 10:
                OBJECT_SEPERATION_RADIUS -= 10
        elif button_hatch_worker.collidepoint(mouse_pos):
            if FOOD >= 10 and LARVA >= 1:
                FOOD -= 10
                LARVA -= 1
                WORKERS += 1
                new_boid = Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT))
                boids.append(new_boid)
        elif button_hatch_queen.collidepoint(mouse_pos):
            if FOOD >= 500 and LARVA >= 10:
                FOOD -= 500
                LARVA -= 10
                QUEENS += 1
                new_boid = Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT))
                boids.append(new_boid)

        # Update the last action time
        last_add_time = current_time

    return True

def draw_menu(screen):
    """Draw the main menu with tutorial options"""
    screen.fill((20, 30, 40))  # Dark blue background
    
    # Title
    try:
        title_font = pygame.font.SysFont(None, 72)
        button_font = pygame.font.SysFont(None, 36)
    except Exception:
        title_font = pygame.font.Font(None, 72)
        button_font = pygame.font.Font(None, 36)
    
    title_text = title_font.render("KILL BUGS", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    screen.blit(title_text, title_rect)
    
    # Subtitle
    subtitle_text = button_font.render("Choose your game mode:", True, (200, 200, 200))
    subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 4 + 80))
    screen.blit(subtitle_text, subtitle_rect)
    
    # Menu buttons
    button_width = 300
    button_height = 50
    button_spacing = 70
    start_y = HEIGHT // 2 - 50
    
    # Kill Tutorial button
    kill_tutorial_button = pygame.Rect(WIDTH // 2 - button_width // 2, start_y, button_width, button_height)
    pygame.draw.rect(screen, (100, 50, 50), kill_tutorial_button)
    pygame.draw.rect(screen, (255, 100, 100), kill_tutorial_button, 3)
    kill_text = button_font.render("Kill Tutorial", True, (255, 255, 255))
    kill_text_rect = kill_text.get_rect(center=kill_tutorial_button.center)
    screen.blit(kill_text, kill_text_rect)
    
    # Don't Die Tutorial button
    dont_die_button = pygame.Rect(WIDTH // 2 - button_width // 2, start_y + button_spacing, button_width, button_height)
    pygame.draw.rect(screen, (50, 50, 100), dont_die_button)
    pygame.draw.rect(screen, (100, 100, 255), dont_die_button, 3)
    dont_die_text = button_font.render("Don't Die Tutorial", True, (255, 255, 255))
    dont_die_text_rect = dont_die_text.get_rect(center=dont_die_button.center)
    screen.blit(dont_die_text, dont_die_text_rect)
    
    # Main Game button
    main_game_button = pygame.Rect(WIDTH // 2 - button_width // 2, start_y + button_spacing * 2, button_width, button_height)
    pygame.draw.rect(screen, (50, 100, 50), main_game_button)
    pygame.draw.rect(screen, (100, 255, 100), main_game_button, 3)
    main_text = button_font.render("START GAME!", True, (255, 255, 255))
    main_text_rect = main_text.get_rect(center=main_game_button.center)
    screen.blit(main_text, main_text_rect)
    
    # Instructions
    try:
        info_font = pygame.font.SysFont(None, 24)
    except Exception:
        info_font = pygame.font.Font(None, 24)
    
    instructions = [
        "Kill Tutorial: Learn to stomp bugs",
        "Don't Die Tutorial: Protect your food",
        "Main Game: Full survival challenge"
    ]
    
    for i, instruction in enumerate(instructions):
        text = info_font.render(instruction, True, (150, 150, 150))
        text_rect = text.get_rect(center=(WIDTH // 2, start_y + button_spacing * 3 + 50 + i * 25))
        screen.blit(text, text_rect)
    
    return [kill_tutorial_button, dont_die_button, main_game_button]

def handle_menu_events(buttons):
    """Handle menu button clicks"""
    global current_game_state
    
    kill_tutorial_button, dont_die_button, main_game_button = buttons
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            if kill_tutorial_button.collidepoint(mouse_pos):
                current_game_state = GAME_STATE_KILL_TUTORIAL
                return True
            elif dont_die_button.collidepoint(mouse_pos):
                current_game_state = GAME_STATE_DONT_DIE_TUTORIAL
                return True
            elif main_game_button.collidepoint(mouse_pos):
                current_game_state = GAME_STATE_MAIN_GAME
                return True
    
    return True

async def run_kill_tutorial(screen, clock):
    """Kill tutorial - focus on stomping bugs"""
    global current_game_state
    
    # Create fewer, slower bugs for tutorial
    tutorial_boids = [Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(5)]
    tutorial_kills = 0
    tutorial_splats = []
    
    # Load boot image
    boot_image = None
    try:
        boot_image = pygame.image.load("boot.png").convert_alpha()
        boot_image = pygame.transform.smoothscale(boot_image, (48, 48))
    except Exception:
        pass
    
    running = True
    while running and current_game_state == GAME_STATE_KILL_TUTORIAL:
        await asyncio.sleep(0)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    current_game_state = GAME_STATE_MENU
                    return True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                # Kill bugs within stomp radius
                bugs_to_remove = [boid for boid in tutorial_boids if boid.position.distance_to(mouse_pos) < 30]
                tutorial_kills += len(bugs_to_remove)
                for boid in bugs_to_remove:
                    tutorial_boids.remove(boid)
                    tutorial_splats.append({'pos': mouse_pos.copy(), 'time': pygame.time.get_ticks()})
        
        # Spawn new bugs occasionally
        if len(tutorial_boids) < 3 and random.random() < 0.02:
            tutorial_boids.append(Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        
        # Update bugs
        for boid in tutorial_boids:
            boid.update([], WIDTH, HEIGHT)
        
        # Remove old splats
        now = pygame.time.get_ticks()
        tutorial_splats[:] = [s for s in tutorial_splats if now - s['time'] < 2000]
        
        # Draw everything
        screen.fill((0, 100, 0))  # Green background
        
        # Draw tutorial text
        try:
            font = pygame.font.SysFont(None, 36)
            small_font = pygame.font.SysFont(None, 24)
        except Exception:
            font = pygame.font.Font(None, 36)
            small_font = pygame.font.Font(None, 24)
        
        title = font.render("KILL TUTORIAL", True, (255, 255, 255))
        screen.blit(title, (10, 10))
        
        instructions = [
            "Click to stomp bugs!",
            f"Kills: {tutorial_kills}",
            "Press ESC to return to menu"
        ]
        
        for i, instruction in enumerate(instructions):
            text = small_font.render(instruction, True, (255, 255, 255))
            screen.blit(text, (10, 50 + i * 25))
        
        # Draw bugs
        for boid in tutorial_boids:
            boid.draw(screen)
        
        # Draw splats
        for splat in tutorial_splats:
            pygame.draw.circle(screen, (150, 0, 0), (int(splat['pos'].x), int(splat['pos'].y)), 8)
        
        # Draw boot cursor
        mouse_pos = pygame.mouse.get_pos()
        if boot_image:
            rect = boot_image.get_rect(center=mouse_pos)
            screen.blit(boot_image, rect)
        else:
            pygame.draw.circle(screen, (100, 100, 100), mouse_pos, 15, 2)
        
        pygame.display.flip()
        clock.tick(30)
    
    return True

async def run_dont_die_tutorial(screen, clock):
    """Don't die tutorial - focus on protecting food"""
    global current_game_state
    
    # Create tutorial setup with food to protect
    tutorial_boids = [Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(3)]
    tutorial_food = [FoodObject(WIDTH//2 + 100, HEIGHT//2)]  # One food object to protect
    tutorial_kills = 0
    tutorial_splats = []
    
    start_time = pygame.time.get_ticks()
    tutorial_duration = 15000  # 15 seconds
    
    # Load boot image
    boot_image = None
    try:
        boot_image = pygame.image.load("boot.png").convert_alpha()
        boot_image = pygame.transform.smoothscale(boot_image, (48, 48))
    except Exception:
        pass
    
    running = True
    while running and current_game_state == GAME_STATE_DONT_DIE_TUTORIAL:
        await asyncio.sleep(0)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    current_game_state = GAME_STATE_MENU
                    return True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                # Kill bugs within stomp radius
                bugs_to_remove = [boid for boid in tutorial_boids if boid.position.distance_to(mouse_pos) < 30]
                tutorial_kills += len(bugs_to_remove)
                for boid in bugs_to_remove:
                    tutorial_boids.remove(boid)
                    tutorial_splats.append({'pos': mouse_pos.copy(), 'time': pygame.time.get_ticks()})
        
        # Spawn new bugs occasionally
        if len(tutorial_boids) < 5:
            tutorial_boids.append(Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        
        # Update bugs and food
        target_position = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        for boid in tutorial_boids:
            boid.scatter(tutorial_boids, [], tutorial_food, target_position)
            boid.update([], WIDTH, HEIGHT)
            boid.has_received = False
        
        # Update food
        tutorial_food[:] = [food for food in tutorial_food if food.health > 0]
        for food in tutorial_food:
            food.update(target_position, tutorial_boids)
        
        # Check win/lose conditions
        now = pygame.time.get_ticks()
        elapsed = now - start_time
        
        if not tutorial_food:  # All food destroyed
            # Show lose message then return to menu
            current_game_state = GAME_STATE_MENU
            return True
        elif elapsed >= tutorial_duration:  # Survived the time
            # Show win message then return to menu
            current_game_state = GAME_STATE_MENU
            return True
        
        # Remove old splats
        tutorial_splats[:] = [s for s in tutorial_splats if now - s['time'] < 2000]
        
        # Draw everything
        screen.fill((0, 100, 0))  # Green background
        
        # Draw base circle
        pygame.draw.circle(screen, (0, 0, 0), (WIDTH // 2, HEIGHT // 2), 40)
        
        # Draw tutorial text
        try:
            font = pygame.font.SysFont(None, 36)
            small_font = pygame.font.SysFont(None, 24)
        except Exception:
            font = pygame.font.Font(None, 36)
            small_font = pygame.font.Font(None, 24)
        
        title = font.render("DON'T DIE TUTORIAL", True, (255, 255, 255))
        screen.blit(title, (10, 10))
        
        time_left = max(0, (tutorial_duration - elapsed) // 1000)
        instructions = [
            "Protect the food from bugs!",
            f"Time left: {time_left}s",
            f"Kills: {tutorial_kills}",
            "Press ESC to return to menu"
        ]
        
        for i, instruction in enumerate(instructions):
            text = small_font.render(instruction, True, (255, 255, 255))
            screen.blit(text, (10, 50 + i * 25))
        
        # Draw food
        for food in tutorial_food:
            food.draw(screen)
        
        # Draw bugs
        for boid in tutorial_boids:
            boid.draw(screen)
        
        # Draw splats
        for splat in tutorial_splats:
            pygame.draw.circle(screen, (150, 0, 0), (int(splat['pos'].x), int(splat['pos'].y)), 8)
        
        # Draw boot cursor
        mouse_pos = pygame.mouse.get_pos()
        if boot_image:
            rect = boot_image.get_rect(center=mouse_pos)
            screen.blit(boot_image, rect)
        else:
            pygame.draw.circle(screen, (100, 100, 100), mouse_pos, 15, 2)
        
        pygame.display.flip()
        clock.tick(30)
    
    return True

class FoodObject:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.size = 20  # radius for simplicity
        self.mass = 5
        self.held_in_goal = False
        self.last_goal_time = None
        self.object_remains_in_goal_time = None
        self.max_health = 20
        self.health = self.max_health
        self.touch_times = {}  # {boid_id: time_when_first_touched}

    def update(self, target_position, boids):
        # Check which boids are touching
        now = pygame.time.get_ticks()
        for boid in boids:
            boid_id = id(boid)
            if self.position.distance_to(boid.position) < self.size + 8:  # 8 is boid radius
                # If not already touching, record time
                if boid_id not in self.touch_times:
                    self.touch_times[boid_id] = now
                # If touched for >= 1000 ms, lose health and reset timer for this boid
                elif now - self.touch_times[boid_id] >= 1000:
                    if self.health > 0:
                        self.health -= 1
                    self.touch_times[boid_id] = now  # Reset timer for repeated touches
            else:
                # Remove boid from touch_times if not touching
                if boid_id in self.touch_times:
                    del self.touch_times[boid_id]

        # Clamp position to stay inside the frame
        self.position.x = max(self.size, min(self.position.x, WIDTH - self.size))
        self.position.y = max(self.size, min(self.position.y, HEIGHT - self.size))

    def draw(self, screen):
        # Draw food as a yellow circle
        pygame.draw.circle(screen, (255, 255, 0), self.position, self.size)
        # Draw health bar above
        bar_width = 40
        bar_height = 6
        health_ratio = self.health / self.max_health
        bar_x = self.position.x - bar_width // 2
        bar_y = self.position.y - self.size - 12
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

class Boid:
    ant_image = None
    ant_image_path = os.path.join(os.path.dirname(__file__), "ant.png")
    def __init__(self, x, y):
        # Initialize position and velocity
        self.position = pygame.Vector2(x, y)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * MAX_SPEED
        self.acceleration = pygame.Vector2(0, 0)
        self.color = (255, 0, 0)
        self.signal_time = pygame.time.get_ticks()
        self.goal_location = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        self.has_received = False  # Flag to check if boid has received a message
        # Load ant image once for all boids
        if Boid.ant_image is None:
            try:
                img = pygame.image.load("ant.png").convert_alpha()  # <- simple path
                Boid.ant_image = pygame.transform.smoothscale(img, (32, 32))
            except Exception as e:
                print("Error loading ant.png:", e)
                Boid.ant_image = None

    def update(self, blocks, WIDTH, HEIGHT):
        # Update velocity and position
        self.velocity += self.acceleration
        if self.velocity.length() > MAX_SPEED:
            self.velocity.scale_to_length(MAX_SPEED)
        self.position += self.velocity
        self.acceleration *= 0
        
        if pygame.time.get_ticks() - self.signal_time > 100:
            self.color = (255, 255, 255)

        # Screen bouncing
        if self.position.x <= 0 or self.position.x >= WIDTH:
            self.velocity.x *= -1
            # Clamp inside bounds
            self.position.x = max(0, min(self.position.x, WIDTH))

        if self.position.y <= 0 or self.position.y >= HEIGHT:
            self.velocity.y *= -1
            # Clamp inside bounds
            self.position.y = max(0, min(self.position.y, HEIGHT))
        
        for block in blocks:
            block_rect = block.get_rect()
            boid_rect = pygame.Rect(self.position.x, self.position.y, 5, 5)  # A small rect for collision
            if boid_rect.colliderect(block_rect):
                # Simple bounce: reverse direction
                # You can get fancier with angle of incidence/reflection later
                if block_rect.left <= self.position.x <= block_rect.right:
                    self.velocity.y *= -1
                if block_rect.top <= self.position.y <= block_rect.bottom:
                    self.velocity.x *= -1

    def apply_force(self, force):
        self.acceleration += force

    def align(self, boids):
        steering = pygame.Vector2(0, 0)
        total = 0
        for boid in boids:
            if boid != self and self.position.distance_to(boid.position) < NEIGHBOR_RADIUS:
                steering += boid.velocity
                total += 1
        if total > 0:
            steering /= total
            steering = (steering.normalize() * MAX_SPEED) - self.velocity
            if steering.length() > MAX_FORCE:
                steering.scale_to_length(MAX_FORCE)
        return steering

    def cohesion(self, boids):
        steering = pygame.Vector2(0, 0)
        total = 0
        for boid in boids:
            if boid != self and self.position.distance_to(boid.position) < NEIGHBOR_RADIUS:
                steering += boid.position
                total += 1
        if total > 0:
            steering /= total
            steering = (steering - self.position).normalize() * MAX_SPEED - self.velocity
            if steering.length() > MAX_FORCE:
                steering.scale_to_length(MAX_FORCE)
            return steering
        return pygame.Vector2(0, 0)

    def separation(self, boids, blocks):
        steering = pygame.Vector2(0, 0)
        total = 0
        for boid in boids:
            distance = self.position.distance_to(boid.position)
            if boid != self and distance < SEPARATION_RADIUS:
                diff = self.position - boid.position
                if distance != 0:
                    diff /= distance
                steering += diff
                total += 1
        # After self.position += self.velocity
        boid_rect = pygame.Rect(self.position.x, self.position.y, 5, 5)  # A small rect for collision
        
        for block in blocks:
            distance = self.position.distance_to(block.position)
            if distance < OBJECT_SEPERATION_RADIUS:
                diff = self.position - block.position
                if distance != 0:
                    diff /= distance
                steering += diff
                total += 1
            block = block.get_rect()
        
        if total > 0:
            steering /= total
        if steering.length() > 0:
            steering = steering.normalize() * MAX_SPEED - self.velocity
            if steering.length() > MAX_FORCE:
                steering.scale_to_length(MAX_FORCE)
        return steering

    def broadcast(self, boids, blocks, objects, goal_location):
        for boid in boids:
            if boid != self and not boid.has_received and self.position.distance_to(boid.position) < BROADCAST_RADIUS:
                boid.recieve(boids, blocks, objects, goal_location)

    def recieve(self, boids, blocks, objects, goal_location):
        if not self.has_received:
            self.has_received = True
            self.color = (0, 255, 0)
            self.broadcast(boids, blocks, objects, goal_location)
            self.goal_location = goal_location
            self.signal_time = pygame.time.get_ticks()
            self.attract_to_object(boids, blocks, objects, goal_location)
            self.apply_force(self.move_to_location(self.goal_location))
            self.flock(boids, blocks, objects, self.goal_location)

    def scatter(self, boids, blocks, objects, target_position):
        self.apply_force(pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)) * MAX_FORCE)
        self.push_object(objects, target_position)
        self.apply_force(self.attract_to_object(boids, blocks, objects, target_position))

    def push_object(self, objects, goal):
        for obj in objects:
            to_object = obj.position - self.position
            if to_object.length() < 30:
                # Modify this section in swarm-soccer.py
                if (goal - obj.position).length() != 0:
                    push_dir = (goal - obj.position).normalize()
                else:
                    push_dir = pygame.Vector2(0, 0)  # Fixed: Use pygame.Vector2 instead of Vector2
                force = push_dir * OBJECT_PUSH_FORCE
                #obj.apply_force(force)
    
    def move_to_location(self, location):
        direction = (location - self.position).normalize()
        steer = direction * MAX_SPEED - self.velocity
        if steer.length() > MAX_FORCE:
            steer.scale_to_length(MAX_FORCE)
        return steer

    def attract_to_object(self, boids, blocks, objects, target_position):
        closest_object = None
        min_distance = float('inf')

        # Find the closest object
        for obj in objects:
            # Check if the object is in the goal
            if obj.position.distance_to(target_position) < 30:
                if obj.object_remains_in_goal_time is None:
                    #print(f"None")
                    obj.object_remains_in_goal_time = pygame.time.get_ticks()
                    print("Object entered the goal")
                elif pygame.time.get_ticks() - obj.object_remains_in_goal_time > 7000:
                    #print(f"Skipping object {obj.position} because it remains in the goal for too long")
                    continue  # Permanently skip this object

            distance = self.position.distance_to(obj.position)
            if distance < min_distance:
                min_distance = distance
                closest_object = obj

        # If a closest object is found and within the attraction radius
        if closest_object and min_distance < ATTRACTION_RADIUS:
            self.broadcast(boids, blocks, objects, closest_object.position)
            return self.move_to_location(closest_object.position)

        return pygame.Vector2(0, 0)

    def resolve_collision_with_ball(self, objects):
        for ball in objects:
            distance = self.position.distance_to(ball.position)
            overlap = ball.size + 5 - distance  # 5 is boid "radius"

            if overlap > 0:
                # Push boid away from ball
                push_dir = (self.position - ball.position).normalize()
                self.position += push_dir * overlap  # move boid out
                self.velocity.reflect_ip(push_dir)  # reflect direction

                # Optional: also apply a force to the ball (Newton's Third Law)
                #ball.apply_force(-push_dir * 0.5)  # tweak force amount


    def flock(self, boids, blocks, objects, target_position):
        # Apply the three main forces
        alignment = self.align(boids)
        cohesion = self.cohesion(boids)
        separation = self.separation(boids, blocks)

        # Weigh the forces
        self.apply_force(alignment * 1.0)
        self.apply_force(cohesion * 1.0)
        self.apply_force(separation * 1.5)
    
    def die(self, boids, splats):
        if self in boids:
            boids.remove(self)
            splats.append({'pos': self.position.copy(), 'time': pygame.time.get_ticks()})

    def draw(self, screen):
        # Draw the ant sprite, rotated to match velocity direction
        if Boid.ant_image:
            angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
            rotated = pygame.transform.rotate(Boid.ant_image, angle)
            rect = rotated.get_rect(center=(self.position.x, self.position.y))
            screen.blit(rotated, rect)
        else:
            # fallback: draw a red circle
            pygame.draw.circle(screen, (255,0,0), (int(self.position.x), int(self.position.y)), 8)

class Splat:
    splat_image = None
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.start_time = pygame.time.get_ticks()
        if Splat.splat_image is None:
            splat_image_path = os.path.join(os.path.dirname(__file__), "splat.png")
            try:
                img = pygame.image.load(splat_image_path).convert_alpha()
                Splat.splat_image = pygame.transform.smoothscale(img, (32, 32))
            except Exception as e:
                print(f"Error loading splat.png: {e}")
                Splat.splat_image = None

    def draw(self, screen):
        if Splat.splat_image:
            rect = Splat.splat_image.get_rect(center=(self.position.x, self.position.y))
            screen.blit(Splat.splat_image, rect)

async def main():
    global NUM_BOIDS, MAX_SPEED, MAX_FORCE, NEIGHBOR_RADIUS, SEPARATION_RADIUS, WIDTH, HEIGHT, OBJECT_SEPERATION_RADIUS, OBJECTS_IN_GOAL, LARVA, QUEENS, FOOD, current_game_state
    pygame.init()
    try:
        pygame.mixer.quit()  # no audio on web
    except Exception:
        pass

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Kill Bugs - Tutorial Game")
    clock = pygame.time.Clock()

    running = True
    while running:
        await asyncio.sleep(0)
        
        if current_game_state == GAME_STATE_MENU:
            # Draw and handle menu
            menu_buttons = draw_menu(screen)
            running = handle_menu_events(menu_buttons)
            pygame.display.flip()
            clock.tick(30)
            
        elif current_game_state == GAME_STATE_KILL_TUTORIAL:
            running = await run_kill_tutorial(screen, clock)
            
        elif current_game_state == GAME_STATE_DONT_DIE_TUTORIAL:
            running = await run_dont_die_tutorial(screen, clock)
            
        elif current_game_state == GAME_STATE_MAIN_GAME:
            # Run the original main game
            running = await run_main_game(screen, clock)
    
    pygame.quit()

async def run_main_game(screen, clock):
    """Run the original main game"""
    global current_game_state
    
    last_add_time = pygame.time.get_ticks()
    init_goal_time = pygame.time.get_ticks()

    # Create boids
    boids = [Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(NUM_BOIDS)]
    movable_object_1 = FoodObject(random.randint(0, WIDTH), random.randint(0, HEIGHT))
    movable_object_2 = FoodObject(random.randint(0, WIDTH), random.randint(0, HEIGHT))
    movable_object_3 = FoodObject(random.randint(0, WIDTH), random.randint(0, HEIGHT))

    objects = [movable_object_1, movable_object_2, movable_object_3]
    blocks = []

    # Load boot image once
    boot_image_path = os.path.join(os.path.dirname(__file__), "boot.png")
    try:
        boot_image = pygame.image.load("boot.png").convert_alpha()
        boot_image = pygame.transform.smoothscale(boot_image, (48, 48))
    except Exception as e:
        print(f"Error loading boot.png: {e}")
        boot_image = None

    # Load splat image once
    splat_image_path = os.path.join(os.path.dirname(__file__), "splat.png")
    try:
        splat_img = pygame.image.load("splat.png").convert_alpha()
        splat_img = pygame.transform.smoothscale(splat_img, (32, 32))
    except Exception as e:
        print(f"Error loading splat.png: {e}")
        splat_img = None

    # Track splats as a list of dicts: {'pos': pygame.Vector2, 'time': int}
    splats = []

    # Target position
    target_position = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
    target_radius = 40

    one_second_ticker = pygame.time.get_ticks()

    start_time = pygame.time.get_ticks()
    timer_duration = 30000  # 30 seconds in milliseconds
    success_displayed = False
    final_points = None
    final_food_health = 0
    final_ants_killed = 0

    ant_spawn_timer = pygame.time.get_ticks()
    running = True
    while running:
        screen.fill((0, 100, 0))  # RGB for dark green

        # Draw a black filled circle in the middle of the screen as the base
        base_center = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        base_radius = 40
        pygame.draw.circle(screen, (0, 0, 0), base_center, base_radius)  # filled black # Draw base
        
        buttons = render_UI(screen, boids)
        running = manage_UI(buttons, boids, objects, splats)

        # Draw splats and remove after 2 seconds
        now = pygame.time.get_ticks()
        splats[:] = [s for s in splats if now - s['time'] < 2000]
        for s in splats:
            if splat_img:
                rect = splat_img.get_rect(center=(s['pos'].x, s['pos'].y))
                screen.blit(splat_img, rect)

        # Update and draw boids
        for boid in boids:
            boid.scatter(boids, blocks, objects, target_position)
            boid.update(blocks, WIDTH, HEIGHT)
            boid.resolve_collision_with_ball(objects)
            boid.draw(screen)
            boid.has_received = False

        for block in blocks:
            block.draw(screen)
        
        # Update and draw objects (food)
        objects[:] = [obj for obj in objects if not (isinstance(obj, FoodObject) and obj.health <= 0)]
        for obj in objects:
            obj.update(target_position, boids)
            obj.draw(screen)
        
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        if boot_image:
            rect = boot_image.get_rect(center=(mouse_pos.x, mouse_pos.y))
            screen.blit(boot_image, rect)

        # Timer logic
        now = pygame.time.get_ticks()
        elapsed = now - start_time
        time_left = max(0, (timer_duration - elapsed) // 1000)

        # Spawn one ant every second during level one
        if not success_displayed and elapsed < timer_duration:
            if now - ant_spawn_timer >= 1000:
                boids.append(Boid(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
                ant_spawn_timer = now

        # Draw timer at top center
        font = pygame.font.SysFont(None, 48)
        timer_text = font.render(f"Time Left: {time_left}s", True, (255, 255, 255))
        screen.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, 20))

        # Check for success
        if elapsed >= timer_duration and not success_displayed:
            food_objects = [obj for obj in objects if isinstance(obj, FoodObject)]
            if food_objects:
                success_text = font.render("Success!", True, (0, 255, 0))
                screen.blit(success_text, (WIDTH // 2 - success_text.get_width() // 2, HEIGHT // 2 - 24))
                # Calculate points
                final_food_health = sum(obj.health for obj in food_objects)
                final_ants_killed = KILLS if 'KILLS' in globals() else 0
                final_points = final_food_health * 10 + final_ants_killed * 5
                success_displayed = True
                # Clear all ants and food objects
                boids.clear()
                objects.clear()

        # Optionally, stop updating everything after level ends
        if success_displayed:
            # Draw "Level Complete" message
            complete_text = font.render("Level 1 Complete!", True, (255, 255, 0))
            screen.blit(complete_text, (WIDTH // 2 - complete_text.get_width() // 2, HEIGHT // 2 + 40))
            # Show points summary
            points_text = font.render(f"Points: {final_points}", True, (0, 200, 255))
            screen.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, HEIGHT // 2 + 90))
            health_text = font.render(f"Food Health Left: {final_food_health}", True, (0, 255, 0))
            screen.blit(health_text, (WIDTH // 2 - health_text.get_width() // 2, HEIGHT // 2 + 130))
            ants_text = font.render(f"Ants Killed: {final_ants_killed}", True, (255, 0, 0))
            screen.blit(ants_text, (WIDTH // 2 - ants_text.get_width() // 2, HEIGHT // 2 + 170))
        else:
            # Normal update/draw code for boids and objects
            for boid in boids:
                boid.scatter(boids, blocks, objects, target_position)
                boid.update(blocks, WIDTH, HEIGHT)
                boid.resolve_collision_with_ball(objects)
                boid.draw(screen)
                boid.has_received = False

            for block in blocks:
                block.draw(screen)

            objects[:] = [obj for obj in objects if not (isinstance(obj, FoodObject) and obj.health <= 0)]
            for obj in objects:
                obj.update(target_position, boids)
                obj.draw(screen)

        pygame.display.flip()
        clock.tick(30)

        # CRITICAL for pygbag/browser:
        await asyncio.sleep(0)


    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
