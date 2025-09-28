try:
    import asyncio
except Exception:
    import pygbag.aio as asyncio

import random, math, os
import pygame

# Screen dimensions
WIDTH, HEIGHT = 700, 700
# Boid settings
NUM_BOIDS = 10
MAX_SPEED = 5
MAX_FORCE = 1
OBJECT_PUSH_FORCE = 0.2
NEIGHBOR_RADIUS = 300
SEPARATION_RADIUS = 10
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
SPAWN_INTERVALS = 1000
MAX_ANTS = 400
DEFINITE_FOOD_HEALTH = 60  # Track food health across levels

# Click effect variables for showing stomp radius
click_effects = []  # List of {'pos': Vector2, 'time': int, 'radius': int}
CLICK_EFFECT_DURATION = 500  # milliseconds

# Game states
GAME_STATE_SPLASH = "splash"
GAME_STATE_MENU = "menu"
GAME_STATE_SHOP = "shop"
GAME_STATE_KILL_TUTORIAL = "kill_tutorial"
GAME_STATE_DONT_DIE_TUTORIAL = "dont_die_tutorial"
GAME_STATE_MAIN_GAME = "main_game"
current_game_state = GAME_STATE_SPLASH

# Shop and shoe system
TOTAL_KILLS = 0  # Total ants killed across all games
CURRENT_SHOE = "tiny"  # Current equipped shoe
UPGRADE_NOTIFICATION = None  # {"text": str, "time": int} for showing upgrades
UPGRADE_DISPLAY_DURATION = 3000  # 3 seconds

# Shoe data: size, stomp_radius, kills_required, description
SHOES = {
    "tiny": {"size": 24, "stomp_radius": 20, "kills_required": 0, "description": "Tiny boot - starter shoe"},
    "small": {"size": 32, "stomp_radius": 25, "kills_required": 25, "description": "Small boot - basic range"},
    "medium": {"size": 48, "stomp_radius": 35, "kills_required": 75, "description": "Medium boot - decent reach"},
    "large": {"size": 64, "stomp_radius": 50, "kills_required": 150, "description": "Large boot - good coverage"},
    "xl": {"size": 80, "stomp_radius": 65, "kills_required": 300, "description": "XL boot - wide destruction"},
    "giant": {"size": 96, "stomp_radius": 80, "kills_required": 500, "description": "Giant boot - massive impact"},
    "mega": {"size": 128, "stomp_radius": 100, "kills_required": 1000, "description": "MEGA BOOT - ultimate power!"}
}

OWNED_SHOES = {"tiny"}  # Shoes the player owns

# Splash screen settings
SPLASH_DISPLAY_TIME = 2000  # 2 seconds in milliseconds
FADE_DURATION = 500  # 0.5 second fade duration
splash_start_time = None
splash_image = None

# Spawn holes configuration
NUM_SPAWN_HOLES = 4
SPAWN_HOLE_RADIUS = 20
spawn_holes = []

L1 = {"character": "ants"}

def load_splash_image():
    """Load and scale the splash screen image to fill entire screen"""
    global splash_image
    try:
        splash_image = pygame.image.load("killbugs.png").convert_alpha()
        # Stretch to fill entire screen dimensions
        splash_image = pygame.transform.scale(splash_image, (WIDTH, HEIGHT))
        print(f"Splash image stretched to full screen: {WIDTH}x{HEIGHT}")
        
    except pygame.error as e:
        print(f"Warning: killbugs.png not found or invalid: {e}")
        splash_image = None
    except Exception as e:
        print(f"Error loading splash image: {e}")
        splash_image = None

def draw_splash_screen(screen, current_time):
    """Draw the splash screen with fade effect"""
    global splash_start_time
    
    if splash_start_time is None:
        splash_start_time = current_time
    
    elapsed = current_time - splash_start_time
    
    # Fill background
    screen.fill((0, 0, 0))  # Black background
    
    if splash_image:
        # Calculate alpha for fade effect
        if elapsed < SPLASH_DISPLAY_TIME:
            alpha = 255  # Full opacity during display time
        elif elapsed < SPLASH_DISPLAY_TIME + FADE_DURATION:
            # Fade out
            fade_progress = (elapsed - SPLASH_DISPLAY_TIME) / FADE_DURATION
            alpha = int(255 * (1.0 - fade_progress))
        else:
            alpha = 0
        
        if alpha > 0:
            # Create a copy of the image with alpha
            faded_image = splash_image.copy()
            faded_image.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
            
            # Center the image on screen
            image_rect = faded_image.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(faded_image, image_rect)
    else:
        # Fallback text splash screen
        font = pygame.font.Font(None, 72)
        text = font.render("KILL BUGS", True, (255, 255, 255))
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        
        # Calculate alpha for text fade
        if elapsed < SPLASH_DISPLAY_TIME:
            alpha = 255
        elif elapsed < SPLASH_DISPLAY_TIME + FADE_DURATION:
            fade_progress = (elapsed - SPLASH_DISPLAY_TIME) / FADE_DURATION
            alpha = int(255 * (1.0 - fade_progress))
        else:
            alpha = 0
        
        if alpha > 0:
            # Create surface with alpha for text
            text_surface = pygame.Surface(text.get_size(), pygame.SRCALPHA)
            text_surface.fill((255, 255, 255, alpha))
            text_surface.blit(text, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(text_surface, text_rect)
    
    return elapsed >= SPLASH_DISPLAY_TIME + FADE_DURATION

def create_spawn_holes():
    """Create spawn holes in random locations around the edges"""
    global spawn_holes
    spawn_holes = []
    
    for _ in range(NUM_SPAWN_HOLES):
        # Choose random edge (0=top, 1=right, 2=bottom, 3=left)
        edge = random.randint(0, 3)
        
        if edge == 0:  # top edge
            x = random.randint(SPAWN_HOLE_RADIUS * 2, WIDTH - SPAWN_HOLE_RADIUS * 2)
            y = SPAWN_HOLE_RADIUS * 2
        elif edge == 1:  # right edge
            x = WIDTH - SPAWN_HOLE_RADIUS * 2
            y = random.randint(SPAWN_HOLE_RADIUS * 2, HEIGHT - SPAWN_HOLE_RADIUS * 2)
        elif edge == 2:  # bottom edge
            x = random.randint(SPAWN_HOLE_RADIUS * 2, WIDTH - SPAWN_HOLE_RADIUS * 2)
            y = HEIGHT - SPAWN_HOLE_RADIUS * 2
        else:  # left edge
            x = SPAWN_HOLE_RADIUS * 2
            y = random.randint(SPAWN_HOLE_RADIUS * 2, HEIGHT - SPAWN_HOLE_RADIUS * 2)
        
        spawn_holes.append(pygame.Vector2(x, y))

def spawn_ant_from_hole():
    """Spawn an ant from a random spawn hole"""
    if not spawn_holes:
        create_spawn_holes()
    
    # Choose random spawn hole
    hole_pos = random.choice(spawn_holes)
    
    # Spawn ant near the hole with smaller random offset
    offset_range = SPAWN_HOLE_RADIUS // 2
    offset_x = random.randint(-offset_range, offset_range)
    offset_y = random.randint(-offset_range, offset_range)
    
    x = hole_pos.x + offset_x
    y = hole_pos.y + offset_y
    
    # Ensure ant spawns within screen bounds with margin
    margin = 15
    x = max(margin, min(x, WIDTH - margin))
    y = max(margin, min(y, HEIGHT - margin))
    
    return Boid(x, y)

def draw_spawn_holes(screen):
    """Draw the spawn holes as dark circles"""
    for hole_pos in spawn_holes:
        # Draw hole as dark brown/black circle
        pygame.draw.circle(screen, (50, 30, 20), (int(hole_pos.x), int(hole_pos.y)), SPAWN_HOLE_RADIUS)
        # Draw hole border
        pygame.draw.circle(screen, (30, 20, 10), (int(hole_pos.x), int(hole_pos.y)), SPAWN_HOLE_RADIUS, 3)

def draw_click_effects(screen):
    """Draw click effects showing stomp radius"""
    global click_effects
    
    current_time = pygame.time.get_ticks()
    # Remove expired effects
    click_effects[:] = [effect for effect in click_effects 
                       if current_time - effect['time'] < CLICK_EFFECT_DURATION]
    
    for effect in click_effects:
        elapsed = current_time - effect['time']
        progress = elapsed / CLICK_EFFECT_DURATION
        
        # Fade out over time
        alpha = int(255 * (1 - progress))
        radius = effect['radius']
        
        # Create a surface with per-pixel alpha for the circle
        circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
        # Draw expanding circle
        circle_radius = int(radius * (0.5 + 0.5 * progress))
        pygame.draw.circle(circle_surface, (255, 255, 0, alpha), (radius, radius), circle_radius, 3)
        
        # Blit to screen
        circle_rect = circle_surface.get_rect(center=(effect['pos'].x, effect['pos'].y))
        screen.blit(circle_surface, circle_rect)

def draw_upgrade_notification(screen):
    """Draw upgrade notification if active"""
    global UPGRADE_NOTIFICATION
    
    if UPGRADE_NOTIFICATION is None:
        return
    
    current_time = pygame.time.get_ticks()
    elapsed = current_time - UPGRADE_NOTIFICATION["time"]
    
    # Remove notification after display duration
    if elapsed > UPGRADE_DISPLAY_DURATION:
        UPGRADE_NOTIFICATION = None
        return
    
    # Create notification box
    try:
        font = pygame.font.SysFont(None, 48)
        small_font = pygame.font.SysFont(None, 32)
    except Exception:
        font = pygame.font.Font(None, 48)
        small_font = pygame.font.Font(None, 32)
    
    # Calculate fade effect
    fade_progress = min(1.0, elapsed / 500)  # Fade in over 0.5 seconds
    if elapsed > UPGRADE_DISPLAY_DURATION - 500:  # Fade out in last 0.5 seconds
        fade_progress = (UPGRADE_DISPLAY_DURATION - elapsed) / 500
    
    alpha = int(255 * fade_progress)
    
    # Create notification surface
    notification_text = font.render(UPGRADE_NOTIFICATION["text"], True, (255, 255, 0))
    subtitle_text = small_font.render("Stomp radius increased!", True, (255, 200, 0))
    
    # Background box
    box_width = max(notification_text.get_width(), subtitle_text.get_width()) + 40
    box_height = notification_text.get_height() + subtitle_text.get_height() + 30
    box_x = (WIDTH - box_width) // 2
    box_y = 150
    
    # Create surface with per-pixel alpha
    notification_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    notification_surface.fill((0, 0, 0, min(180, alpha)))  # Semi-transparent black background
    
    # Add border
    pygame.draw.rect(notification_surface, (255, 255, 0, alpha), (0, 0, box_width, box_height), 3)
    
    # Add text
    notification_text.set_alpha(alpha)
    subtitle_text.set_alpha(alpha)
    
    text_x = (box_width - notification_text.get_width()) // 2
    text_y = 10
    notification_surface.blit(notification_text, (text_x, text_y))
    
    subtitle_x = (box_width - subtitle_text.get_width()) // 2
    subtitle_y = text_y + notification_text.get_height() + 5
    notification_surface.blit(subtitle_text, (subtitle_x, subtitle_y))
    
    screen.blit(notification_surface, (box_x, box_y))

def get_current_stomp_radius():
    """Get the stomp radius of the currently equipped shoe"""
    return SHOES[CURRENT_SHOE]["stomp_radius"]

def load_boot_image():
    """Load boot image with current shoe size"""
    try:
        boot_image = pygame.image.load("boot.png").convert_alpha()
        current_shoe_size = SHOES[CURRENT_SHOE]["size"]
        boot_image = pygame.transform.smoothscale(boot_image, (current_shoe_size, current_shoe_size))
        return boot_image
    except Exception as e:
        print(f"Error loading boot.png: {e}")
        return None

def add_kill():
    """Add a kill to the total count and check for automatic upgrades"""
    global TOTAL_KILLS, CURRENT_SHOE, OWNED_SHOES, UPGRADE_NOTIFICATION
    TOTAL_KILLS += 1
    print(f"Kill! Total: {TOTAL_KILLS}")
    
    # Check for automatic upgrades
    for shoe_name, shoe_data in SHOES.items():
        if (TOTAL_KILLS >= shoe_data["kills_required"] and 
            shoe_name not in OWNED_SHOES):
            # Auto-unlock and equip the new shoe
            OWNED_SHOES.add(shoe_name)
            old_shoe = CURRENT_SHOE
            CURRENT_SHOE = shoe_name
            
            # Set upgrade notification
            UPGRADE_NOTIFICATION = {
                "text": f"UPGRADE! {shoe_name.title()} Boot Unlocked!",
                "time": pygame.time.get_ticks(),
                "reload_boot": True  # Signal that boot image needs reloading
            }
            
            print(f"🎉 UPGRADE! Unlocked {shoe_name.title()} Boot! (Stomp radius: {shoe_data['stomp_radius']}px)")
            break  # Only upgrade one shoe at a time

def draw_shop(screen):
    """Draw the shop interface"""
    screen.fill((40, 20, 60))  # Purple background
    
    try:
        title_font = pygame.font.SysFont(None, 72)
        button_font = pygame.font.SysFont(None, 28)
        small_font = pygame.font.SysFont(None, 20)
    except Exception:
        title_font = pygame.font.Font(None, 72)
        button_font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 20)
    
    # Title
    title_text = title_font.render("BOOT SHOP", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(WIDTH // 2, 60))
    screen.blit(title_text, title_rect)
    
    # Total kills display
    kills_text = button_font.render(f"Total Kills: {TOTAL_KILLS}", True, (255, 255, 0))
    screen.blit(kills_text, (20, 20))
    
    # Current shoe display
    current_text = button_font.render(f"Current: {CURRENT_SHOE.title()} Boot", True, (100, 255, 100))
    screen.blit(current_text, (20, 50))
    
    # Shop items
    start_y = 120
    item_height = 70
    buttons = []
    
    for i, (shoe_name, shoe_data) in enumerate(SHOES.items()):
        y = start_y + i * item_height
        
        # Item background
        item_rect = pygame.Rect(50, y, WIDTH - 100, item_height - 10)
        
        # Color based on ownership/availability
        if shoe_name in OWNED_SHOES:
            if shoe_name == CURRENT_SHOE:
                bg_color = (50, 100, 50)  # Green for equipped
                border_color = (100, 255, 100)
            else:
                bg_color = (100, 100, 50)  # Yellow for owned
                border_color = (255, 255, 100)
        elif TOTAL_KILLS >= shoe_data["kills_required"]:
            bg_color = (50, 50, 100)  # Blue for unlocked
            border_color = (100, 100, 255)
        else:
            bg_color = (100, 50, 50)  # Red for locked
            border_color = (255, 100, 100)
        
        pygame.draw.rect(screen, bg_color, item_rect)
        pygame.draw.rect(screen, border_color, item_rect, 3)
        
        # Boot preview (simple circle representation)
        boot_center = (item_rect.left + 40, item_rect.centery)
        boot_radius = min(shoe_data["size"] // 4, 25)  # Scale down for display
        pygame.draw.circle(screen, (139, 69, 19), boot_center, boot_radius)
        pygame.draw.circle(screen, (160, 82, 45), boot_center, boot_radius, 2)
        
        # Shoe info
        name_text = button_font.render(shoe_name.title() + " Boot", True, (255, 255, 255))
        screen.blit(name_text, (item_rect.left + 90, y + 5))
        
        desc_text = small_font.render(shoe_data["description"], True, (200, 200, 200))
        screen.blit(desc_text, (item_rect.left + 90, y + 25))
        
        radius_text = small_font.render(f"Stomp Radius: {shoe_data['stomp_radius']}px", True, (200, 200, 200))
        screen.blit(radius_text, (item_rect.left + 90, y + 45))
        
        # Status/Requirement
        if shoe_name in OWNED_SHOES:
            if shoe_name == CURRENT_SHOE:
                status_text = button_font.render("EQUIPPED", True, (100, 255, 100))
            else:
                status_text = button_font.render("EQUIP", True, (255, 255, 100))
        elif TOTAL_KILLS >= shoe_data["kills_required"]:
            status_text = button_font.render("UNLOCK", True, (100, 255, 100))
        else:
            needed = shoe_data["kills_required"] - TOTAL_KILLS
            status_text = small_font.render(f"Need {needed} more kills", True, (255, 100, 100))
        
        status_rect = status_text.get_rect(right=item_rect.right - 20, centery=item_rect.centery)
        screen.blit(status_text, status_rect)
        
        buttons.append((item_rect, shoe_name))
    
    # Back button
    back_button = pygame.Rect(50, HEIGHT - 80, 100, 40)
    pygame.draw.rect(screen, (100, 100, 100), back_button)
    pygame.draw.rect(screen, (200, 200, 200), back_button, 2)
    back_text = button_font.render("BACK", True, (255, 255, 255))
    back_text_rect = back_text.get_rect(center=back_button.center)
    screen.blit(back_text, back_text_rect)
    buttons.append((back_button, "back"))
    
    return buttons

def handle_shop_events(buttons):
    """Handle shop button clicks"""
    global CURRENT_SHOE, OWNED_SHOES
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            for button_rect, action in buttons:
                if button_rect.collidepoint(mouse_pos):
                    if action == "back":
                        return "back"
                    elif action in SHOES:
                        shoe_data = SHOES[action]
                        
                        if action in OWNED_SHOES:
                            # Equip the shoe
                            CURRENT_SHOE = action
                            print(f"Equipped {action} boot!")
                        elif TOTAL_KILLS >= shoe_data["kills_required"]:
                            # Unlock the shoe
                            OWNED_SHOES.add(action)
                            CURRENT_SHOE = action
                            print(f"Unlocked and equipped {action} boot!")
                        else:
                            needed = shoe_data["kills_required"] - TOTAL_KILLS
                            print(f"Need {needed} more kills to unlock {action} boot!")
                    
    return None
    global NUM_BOIDS, MAX_SPEED, MAX_FORCE, NEIGHBOR_RADIUS, SEPARATION_RADIUS, OBJECT_SEPERATION_RADIUS, WIDTH, HEIGHT
    font = pygame.font.SysFont(None, 15)

    a = 140
    b = 10
    c = 50
    d = 10

    return []

# Declare mouse_held as a global variable
mouse_held = False
last_add_time = 0  # Initialize outside the function

def manage_UI(buttons, boids, movable_objects, splats):
    global WIDTH, HEIGHT, MAX_SPEED, MAX_FORCE, NEIGHBOR_RADIUS, SEPARATION_RADIUS, OBJECT_SEPERATION_RADIUS, mouse_held, last_add_time, FOOD, LARVA, WORKERS, QUEENS
    dragging_object = False  # Flag to check if an object is being dragged

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
    
    # Shop button
    shop_button = pygame.Rect(WIDTH // 2 - button_width // 2, start_y + button_spacing * 2, button_width, button_height)
    pygame.draw.rect(screen, (100, 50, 100), shop_button)
    pygame.draw.rect(screen, (200, 100, 200), shop_button, 3)
    shop_text = button_font.render("BOOT SHOP", True, (255, 255, 255))
    shop_text_rect = shop_text.get_rect(center=shop_button.center)
    screen.blit(shop_text, shop_text_rect)
    
    # Main Game button
    main_game_button = pygame.Rect(WIDTH // 2 - button_width // 2, start_y + button_spacing * 3, button_width, button_height)
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
        "Boot Shop: Upgrade your stomping power",
        "Main Game: Full survival challenge"
    ]
    
    for i, instruction in enumerate(instructions):
        text = info_font.render(instruction, True, (150, 150, 150))
        text_rect = text.get_rect(center=(WIDTH // 2, start_y + button_spacing * 4 + 50 + i * 25))
        screen.blit(text, text_rect)
    
    return [kill_tutorial_button, dont_die_button, shop_button, main_game_button]

def handle_menu_events(buttons):
    """Handle menu button clicks"""
    global current_game_state
    
    kill_tutorial_button, dont_die_button, shop_button, main_game_button = buttons
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            if kill_tutorial_button.collidepoint(mouse_pos):
                return "kill_tutorial"
            elif dont_die_button.collidepoint(mouse_pos):
                return "dont_die_tutorial"
            elif shop_button.collidepoint(mouse_pos):
                return "shop"
            elif main_game_button.collidepoint(mouse_pos):
                return "main_game"
    
    return True

async def run_kill_tutorial(screen, clock):
    """Kill tutorial - focus on stomping bugs"""
    global current_game_state
    
    # Create spawn holes for tutorial
    create_spawn_holes()
    
    # Create fewer, slower bugs for tutorial
    tutorial_boids = [spawn_ant_from_hole() for _ in range(5)]
    tutorial_kills = 0
    tutorial_splats = []
    
    # Load boot image with current shoe size
    boot_image = load_boot_image()
    
    # Load tutorial illustration image
    tutorial_image = None
    #try:
    #    tutorial_image = pygame.image.load("kill_tutorial.png").convert_alpha()
    #    # Scale to reasonable size for tutorial display
    #    tutorial_image = pygame.transform.smoothscale(tutorial_image, (200, 150))
    #except Exception as e:
    #    print(f"Error loading kill_tutorial.png: {e}")
    #    tutorial_image = None
    
    # Load splat image
    splat_image = None
    try:
        splat_image = pygame.image.load("splat.png").convert_alpha()
        splat_image = pygame.transform.smoothscale(splat_image, (32, 32))
    except Exception as e:
        print(f"Error loading splat.png: {e}")
        splat_image = None
    
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
                # Kill bugs within stomp radius using current shoe
                stomp_radius = get_current_stomp_radius()
                bugs_to_remove = [boid for boid in tutorial_boids if boid.position.distance_to(mouse_pos) < stomp_radius]
                tutorial_kills += len(bugs_to_remove)
                
                # Add click effect to show stomp radius
                global click_effects
                click_effects.append({
                    'pos': mouse_pos.copy(),
                    'time': pygame.time.get_ticks(),
                    'radius': stomp_radius
                })
                
                for boid in bugs_to_remove:
                    tutorial_boids.remove(boid)
                    tutorial_splats.append({'pos': mouse_pos.copy(), 'time': pygame.time.get_ticks()})
                    add_kill()  # Track the kill
        
        # Spawn new bugs occasionally
        if len(tutorial_boids) < 3 and random.random() < 0.02:
            tutorial_boids.append(spawn_ant_from_hole())
        
        # Update bugs
        for boid in tutorial_boids:
            boid.update([], WIDTH, HEIGHT)
        
        # Remove old splats
        now = pygame.time.get_ticks()
        tutorial_splats[:] = [s for s in tutorial_splats if now - s['time'] < 2000]
        
        # Check if boot image needs reloading due to upgrade
        global UPGRADE_NOTIFICATION
        if (UPGRADE_NOTIFICATION is not None and 
            UPGRADE_NOTIFICATION.get("reload_boot", False)):
            boot_image = load_boot_image()
            UPGRADE_NOTIFICATION["reload_boot"] = False  # Clear the flag
        
        # Draw everything
        screen.fill((0, 100, 0))  # Green background
        
        # Draw spawn holes
        draw_spawn_holes(screen)
        
        # Draw tutorial text
        try:
            font = pygame.font.SysFont(None, 36)
            small_font = pygame.font.SysFont(None, 24)
        except Exception:
            font = pygame.font.Font(None, 36)
            small_font = pygame.font.Font(None, 24)
        
        title = font.render("KILL TUTORIAL", True, (255, 255, 255))
        screen.blit(title, (10, 10))
        
        # Display tutorial image if available
        if tutorial_image:
            # Position image in top-right area
            img_rect = tutorial_image.get_rect()
            img_rect.topright = (WIDTH - 10, 50)
            screen.blit(tutorial_image, img_rect)
        
        instructions = [
            "Use your boot to stomp and kill bugs by clicking!",
            "Click anywhere near a bug to eliminate it.",
            "The boot follows your mouse cursor.",
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
            if splat_image:
                rect = splat_image.get_rect(center=(int(splat['pos'].x), int(splat['pos'].y)))
                screen.blit(splat_image, rect)
            else:
                pygame.draw.circle(screen, (150, 0, 0), (int(splat['pos'].x), int(splat['pos'].y)), 8)
        
        # Draw boot cursor
        mouse_pos = pygame.mouse.get_pos()
        if boot_image:
            rect = boot_image.get_rect(center=mouse_pos)
            screen.blit(boot_image, rect)
        else:
            pygame.draw.circle(screen, (100, 100, 100), mouse_pos, 15, 2)
        
        # Draw upgrade notification
        draw_upgrade_notification(screen)
        
        pygame.display.flip()
        clock.tick(30)
    
    return True

async def run_dont_die_tutorial(screen, clock):
    """Don't die tutorial - focus on protecting food"""
    global current_game_state
    
    # Create spawn holes for tutorial
    create_spawn_holes()
    
    # Create tutorial setup with food to protect
    tutorial_boids = [spawn_ant_from_hole() for _ in range(3)]
    tutorial_food = [FoodObject(WIDTH//2 + 100, HEIGHT//2)]  # One food object to protect
    tutorial_kills = 0
    tutorial_splats = []
    
    start_time = pygame.time.get_ticks()
    tutorial_duration = 15000  # 15 seconds
    
    # Load boot image with current shoe size
    boot_image = load_boot_image()
    
    # Load splat image
    splat_image = None
    try:
        splat_image = pygame.image.load("splat.png").convert_alpha()
        splat_image = pygame.transform.smoothscale(splat_image, (32, 32))
    except Exception as e:
        print(f"Error loading splat.png: {e}")
        splat_image = None
    
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
                # Kill bugs within stomp radius using current shoe
                stomp_radius = get_current_stomp_radius()
                bugs_to_remove = [boid for boid in tutorial_boids if boid.position.distance_to(mouse_pos) < stomp_radius]
                tutorial_kills += len(bugs_to_remove)
                for boid in bugs_to_remove:
                    tutorial_boids.remove(boid)
                    tutorial_splats.append({'pos': mouse_pos.copy(), 'time': pygame.time.get_ticks()})
                    add_kill()  # Track the kill
        
        # Spawn new bugs occasionally
        if len(tutorial_boids) < 5:
            tutorial_boids.append(spawn_ant_from_hole())
        
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
        
        # Check if boot image needs reloading due to upgrade
        if (UPGRADE_NOTIFICATION is not None and 
            UPGRADE_NOTIFICATION.get("reload_boot", False)):
            boot_image = load_boot_image()
            UPGRADE_NOTIFICATION["reload_boot"] = False  # Clear the flag
        
        # Draw everything
        screen.fill((0, 100, 0))  # Green background
        
        # Draw spawn holes
        draw_spawn_holes(screen)
        
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
            if splat_image:
                rect = splat_image.get_rect(center=(int(splat['pos'].x), int(splat['pos'].y)))
                screen.blit(splat_image, rect)
            else:
                pygame.draw.circle(screen, (150, 0, 0), (int(splat['pos'].x), int(splat['pos'].y)), 8)
        
        # Draw boot cursor
        mouse_pos = pygame.mouse.get_pos()
        if boot_image:
            rect = boot_image.get_rect(center=mouse_pos)
            screen.blit(boot_image, rect)
        else:
            pygame.draw.circle(screen, (100, 100, 100), mouse_pos, 15, 2)
        
        # Draw upgrade notification
        draw_upgrade_notification(screen)
        
        pygame.display.flip()
        clock.tick(30)
    
    return True

class FoodObject:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        # Load strawberry image once for all FoodObjects
        if not hasattr(FoodObject, "strawberry_image"):
            try:
                img = pygame.image.load("strawberry.png").convert_alpha()
                FoodObject.strawberry_image = pygame.transform.smoothscale(img, (40, 40))
            except Exception as e:
                print(f"Error loading strawberry.png: {e}")
                FoodObject.strawberry_image = None
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
        # Draw strawberry image if available
        if hasattr(FoodObject, "strawberry_image") and FoodObject.strawberry_image:
            rect = FoodObject.strawberry_image.get_rect(center=(int(self.position.x), int(self.position.y)))
            screen.blit(FoodObject.strawberry_image, rect)
        else:
            # Fallback: draw food as a yellow circle
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

        # Keep boids within screen bounds with bouncing
        margin = 10  # Small margin from edges
        
        if self.position.x <= margin:
            self.position.x = margin
            self.velocity.x = abs(self.velocity.x)  # Bounce right
        elif self.position.x >= WIDTH - margin:
            self.position.x = WIDTH - margin
            self.velocity.x = -abs(self.velocity.x)  # Bounce left
            
        if self.position.y <= margin:
            self.position.y = margin
            self.velocity.y = abs(self.velocity.y)  # Bounce down
        elif self.position.y >= HEIGHT - margin:
            self.position.y = HEIGHT - margin
            self.velocity.y = -abs(self.velocity.y)  # Bounce up
        
        # Handle block collisions
        for block in blocks:
            block_rect = block.get_rect()
            boid_rect = pygame.Rect(self.position.x - 5, self.position.y - 5, 10, 10)
            if boid_rect.colliderect(block_rect):
                # Simple bounce: reverse direction
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
    pygame.init()
    try: 
        pygame.mixer.quit()
    except Exception: 
        pass
    
    # Set up display with proper sizing
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Kill Bugs — Stomp the Swarm")
    
    # Ensure we have the correct screen dimensions
    actual_size = screen.get_size()
    print(f"Screen size: {actual_size[0]}x{actual_size[1]}")
    
    clock = pygame.time.Clock()
    
    # Load splash screen image after screen is set up
    load_splash_image()
    
    global current_game_state
    
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        
        #for event in pygame.event.get():
        #    if event.type == pygame.QUIT:
        #        running = False
        
        if current_game_state == GAME_STATE_SPLASH:
            # Handle splash screen events (allow skipping)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            # Draw splash screen and check if it's finished
            splash_finished = draw_splash_screen(screen, current_time)
            if splash_finished:
                current_game_state = GAME_STATE_MENU
        
        elif current_game_state == GAME_STATE_MENU:
            # Handle menu events
            menu_buttons = draw_menu(screen)
            action = handle_menu_events(menu_buttons)
            
            if action == "kill_tutorial":
                current_game_state = GAME_STATE_KILL_TUTORIAL
            elif action == "dont_die_tutorial":
                current_game_state = GAME_STATE_DONT_DIE_TUTORIAL
            elif action == "shop":
                current_game_state = GAME_STATE_SHOP
            elif action == "main_game":
                current_game_state = GAME_STATE_MAIN_GAME
            elif not action:  # False means quit
                running = False
        
        elif current_game_state == GAME_STATE_SHOP:
            shop_buttons = draw_shop(screen)
            shop_action = handle_shop_events(shop_buttons)
            
            if shop_action == "back":
                current_game_state = GAME_STATE_MENU
            elif shop_action == "quit":
                running = False
        
        elif current_game_state == GAME_STATE_KILL_TUTORIAL:
            result = await run_kill_tutorial(screen, clock)
            if result == "menu":
                current_game_state = GAME_STATE_MENU
        
        elif current_game_state == GAME_STATE_DONT_DIE_TUTORIAL:
            result = await run_dont_die_tutorial(screen, clock)
            if result == "menu":
                current_game_state = GAME_STATE_MENU
        
        elif current_game_state == GAME_STATE_MAIN_GAME:
            result = await run_main_game(screen, clock)
            if result == "menu":
                current_game_state = GAME_STATE_MENU
        
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
    
    pygame.quit()

async def run_main_game(screen, clock):
    """Run the original main game"""
    global current_game_state, LEVEL, MAX_SPEED, SPAWN_INTEVALS, DEFINITE_FOOD_HEALTH
    
    # Create spawn holes for main game
    create_spawn_holes()
    
    last_add_time = pygame.time.get_ticks()
    init_goal_time = pygame.time.get_ticks()

    # Create boids from spawn holes
    boids = [spawn_ant_from_hole() for _ in range(NUM_BOIDS)]
    movable_object_1 = FoodObject(random.randint(0, WIDTH), random.randint(0, HEIGHT))
    movable_object_2 = FoodObject(random.randint(0, WIDTH), random.randint(0, HEIGHT))
    movable_object_3 = FoodObject(random.randint(0, WIDTH), random.randint(0, HEIGHT))

    objects = [movable_object_1, movable_object_2, movable_object_3]
    blocks = []

    # Load boot image once and size it based on current shoe
    boot_image = load_boot_image()

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
    success_display_time = None  # Track when success screen started showing

    exit_status = "success"

    final_points = None
    final_food_health = 60
    final_ants_killed = 0

    ant_spawn_timer = pygame.time.get_ticks()
    running = True
    while running:

        # Handle events first
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "menu"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.Vector2(event.pos)
                # Use current shoe's stomp radius
                stomp_radius = get_current_stomp_radius()
                boids_to_remove = [boid for boid in boids if boid.position.distance_to(mouse_pos) < stomp_radius]
                global KILLS
                KILLS += len(boids_to_remove)
                for boid in boids_to_remove:
                    add_kill()  # Track total kills across all games
                    boid.die(boids, splats)

        screen.fill((0, 100, 0))  # RGB for dark green
        
        # Draw spawn holes
        draw_spawn_holes(screen)
        
        now = pygame.time.get_ticks()
        # Spawn one ant every second during level one, but cap at MAX_ANTS
        global SPAWN_INTERVALS
        if not success_displayed and now - ant_spawn_timer >= SPAWN_INTERVALS and len(boids) < MAX_ANTS:
            boids.append(spawn_ant_from_hole())
            ant_spawn_timer = now

        # Timer logic
        elapsed = now - start_time
        time_left = max(0, (timer_duration - elapsed) // 1000)

        # Check for loss condition FIRST
        food_objects = [obj for obj in objects if isinstance(obj, FoodObject)]
        final_food_health = sum(obj.health for obj in food_objects)
        
        if final_food_health <= 0 and not success_displayed:
            print("YOU LOST!")
            exit_status = "loss"
            success_displayed = True
            success_display_time = now  # Start the 3-second timer
            final_ants_killed = KILLS if 'KILLS' in globals() else 0
            final_points = final_ants_killed * 5

        # Check for success
        # Check for success
                # Check for success
        elif elapsed >= timer_duration and not success_displayed:
            print("LEVEL COMPLETE!")
            exit_status = "success"
            success_displayed = True
            success_display_time = now  # Start the 3-second timer
            final_ants_killed = KILLS if 'KILLS' in globals() else 0
            final_food_health = sum(obj.health for obj in food_objects)  # Calculate BEFORE clearing
            final_points = final_food_health * 10 + final_ants_killed * 5
            DEFINITE_FOOD_HEALTH = final_food_health  # Store for next level
            
            # Clear objects immediately after calculating final_food_health
            boids.clear()
            objects.clear()
            
            # Level progression
            global MAX_FORCE, LEVEL, OBJECT_PUSH_FORCE, ATTRACTION_RADIUS
            MAX_FORCE += 0.5
            LEVEL += 1
            MAX_SPEED = min(MAX_SPEED * 1.25, 20)  # Cap max speed at 20
            SPAWN_INTERVALS *= 0.25  # Faster spawning, minimum 0.5 seconds
            OBJECT_PUSH_FORCE = min(OBJECT_PUSH_FORCE + 0.5, 10)  # Cap push force at 10
            ATTRACTION_RADIUS = min(ATTRACTION_RADIUS + 20, 300)  # Cap attraction radius at 300

        # Auto-advance after 5 seconds
        if success_displayed and success_display_time:
            time_since_success = now - success_display_time
            if time_since_success >= 5000:  # 5 seconds
                if exit_status == "success":
                    # Reset KILLS for next level
                    KILLS = 0
                    # Start next level by recursively calling run_main_game
                    return await run_main_game(screen, clock)
                else:
                    # Lost - return to menu
                    return "menu"

        # Draw end game messages
        if success_displayed:
            if exit_status == "loss":
                LEVEL = 1  # Reset level on loss
                complete_text = font.render("Level Failed :(", True, (255, 100, 100))
                sub_text = font.render("Returning to menu...", True, (200, 200, 200))
            else:
                complete_text = font.render(f"Level {LEVEL-1} Complete!", True, (100, 255, 100))
                sub_text = font.render(f"Starting Level {LEVEL}...", True, (200, 200, 200))

            screen.blit(complete_text, (WIDTH // 2 - complete_text.get_width() // 2, HEIGHT // 2 + 40))
            screen.blit(sub_text, (WIDTH // 2 - sub_text.get_width() // 2, HEIGHT // 2 + 90))
            
            points_text = font.render(f"Points: {final_points}", True, (0, 200, 255))
            screen.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, HEIGHT // 2 + 140))
            
            ants_text = font.render(f"Ants Killed: {final_ants_killed}", True, (0, 200, 255))
            screen.blit(ants_text, (WIDTH // 2 - ants_text.get_width() // 2, HEIGHT // 2 + 190))

            food_text = font.render(f"Food Health: {DEFINITE_FOOD_HEALTH}", True, (0, 200, 255))
            screen.blit(food_text, (WIDTH // 2 - food_text.get_width() // 2, HEIGHT // 2 + 240))
            
            # REMOVE THESE LINES - objects already cleared above
            # boids.clear()
            # objects.clear()

            # Show countdown
            if success_display_time:
                countdown = max(0, 3 - ((now - success_display_time) // 1000))
                countdown_text = font.render(f"Next in: {countdown}s", True, (255, 255, 0))
                screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2, HEIGHT // 2 + 290))

        # Only update game objects if not finished
        if not success_displayed:
            # Update boids
            for boid in boids:
                boid.scatter(boids, blocks, objects, target_position)
                boid.update(blocks, WIDTH, HEIGHT)
                boid.resolve_collision_with_ball(objects)
                boid.has_received = False

            # Update food objects (ONLY ONCE!)
            objects[:] = [obj for obj in objects if not (isinstance(obj, FoodObject) and obj.health <= 0)]
            for obj in objects:
                obj.update(target_position, boids)

        # Draw everything
        for boid in boids:
            boid.draw(screen)

        for obj in objects:
            obj.draw(screen)

        # Draw splats
        splats[:] = [s for s in splats if now - s['time'] < 2000]
        
        # Check if boot image needs reloading due to upgrade
        if (UPGRADE_NOTIFICATION is not None and 
            UPGRADE_NOTIFICATION.get("reload_boot", False)):
            boot_image = load_boot_image()
            UPGRADE_NOTIFICATION["reload_boot"] = False  # Clear the flag
        
        for s in splats:
            if splat_img:
                rect = splat_img.get_rect(center=(s['pos'].x, s['pos'].y))
                screen.blit(splat_img, rect)

        # Draw boot cursor
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        if boot_image:
            rect = boot_image.get_rect(center=(mouse_pos.x, mouse_pos.y))
            screen.blit(boot_image, rect)

        # Draw timer
        font = pygame.font.SysFont(None, 48)
        timer_text = font.render(f"Time Left: {time_left}s", True, (255, 255, 255))
        screen.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, 20))

        # Draw level info
        level_text = font.render(f"Level {LEVEL}", True, (255, 255, 255))
        screen.blit(level_text, (10, 10))

        # Draw shoe info
        shoe_info_text = pygame.font.SysFont(None, 24).render(f"Boot: {CURRENT_SHOE.title()} (Kills: {TOTAL_KILLS})", True, (255, 255, 0))
        screen.blit(shoe_info_text, (10, 50))

        # Draw upgrade notification
        draw_upgrade_notification(screen)

        pygame.display.flip()
        clock.tick(30)
        await asyncio.sleep(0)

    return "menu"

if __name__ == "__main__":
    asyncio.run(main())