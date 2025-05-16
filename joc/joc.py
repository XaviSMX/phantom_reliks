import time
import sys
from pygame.locals import *
import pygame
import os

# Game states
LOADING = 0
MENU = 1
GAME = 2
CREDITS = 3
DIALOG = 4  # Nuevo estado para los diálogos

# Current game state
game_state = LOADING

# Tamaño finestra (mantenido en 600x600)
VIEW_WIDTH = 600
VIEW_HEIGHT = 600

# iniciem pygame
pygame.init()
pantalla = pygame.display.set_mode((VIEW_WIDTH, VIEW_HEIGHT))
pygame.display.set_caption("Phantom reliks")

# Inicializar el módulo de sonido
pygame.mixer.init()

# Cargar y reproducir música de fondo
try:
    music_file = 'assets/music/background_music.mp3'  # Ruta a la música
    pygame.mixer.music.load(music_file)
    pygame.mixer.music.play(-1)  # -1 significa reproducir en bucle infinito
    pygame.mixer.music.set_volume(0.5)  # Volumen al 50%
except:
    print("No se pudo cargar el archivo de música. Asegúrate de que exista en 'assets/music/'")
    # Intentar buscar cualquier archivo de música que pueda existir
    try:
        music_dir = 'assets/music'
        if os.path.exists(music_dir):
            for file in os.listdir(music_dir):
                if file.endswith('.mp3') or file.endswith('.ogg') or file.endswith('.wav'):
                    music_file = os.path.join(music_dir, file)
                    pygame.mixer.music.load(music_file)
                    pygame.mixer.music.play(-1)
                    pygame.mixer.music.set_volume(0.5)
                    print(f"Se ha cargado el archivo de música alternativo: {file}")
                    break
    except:
        print("No se encontraron archivos de música alternativos.")

# Fonts
font_big = pygame.font.SysFont('Arial', 50)
font_medium = pygame.font.SysFont('Arial', 30)
font_small = pygame.font.SysFont('Arial', 20)

# Carreguem imatge de fons
background_image = 'assets/fondo.jpg'
background_width = pygame.image.load(background_image).convert().get_width()
background_height = pygame.image.load(background_image).convert().get_height()

# Fondo para el menú
menu_background_image = 'assets/menu_background.jpg'
# Si la imagen no existe, usar un color de fondo
menu_background = None
try:
    menu_background = pygame.image.load(menu_background_image).convert()
except:
    menu_background = None

# Límits per moure el fons enlloc del personatge (ajustado a la nueva resolución)
MARGIN_X, MARGIN_Y = VIEW_WIDTH // 2, VIEW_HEIGHT // 2

# Carreguem imatge inicial personatge
player_image = pygame.image.load('assets/sprites/down0.png')
protagonist_speed = 8

# Colocamos el personaje inicialmente en la posición 700x900 del fondo
# Para esto, calculamos la posición del bg_x y bg_y para que el personaje aparezca en esas coordenadas
player_rect = player_image.get_rect(center=(VIEW_WIDTH // 2, VIEW_HEIGHT // 2))
bg_x = -(700 - VIEW_WIDTH // 2)
bg_y = -(900 - VIEW_HEIGHT // 2)

# Control de FPS
clock = pygame.time.Clock()
fps = 30

# Control de l'animació del personatge
# 1 up. 2 down. 3 right. 4 left
sprite_direction = "down"
sprite_index = 0
animation_protagonist_speed = 200
sprite_frame_number = 3
last_change_frame_time = 0
idle = False

# Loading screen variables
loading_progress = 0
loading_complete = False
loading_start_time = pygame.time.get_ticks()

# Variables del personaje interactuable (NPC)
npc_x = 700  # Posición X absoluta en el mundo
npc_y = 900  # Posición Y absoluta en el mundo

# NPC sprite variables
npc_sprite_direction = "down"  # Dirección inicial del NPC
npc_sprite_index = 0  # Índice del sprite actual
npc_animation_speed = 500  # Velocidad de animación más lenta que el protagonista
npc_last_change_frame_time = 0
npc_frame_number = 3  # Asumir que también tiene 3 frames por dirección como el protagonista
npc_idle = True  # Por defecto, el NPC está quieto

# Intentar cargar la imagen del NPC con sprites
try:
    npc_image = pygame.image.load(f'assets/sprites/npc/{npc_sprite_direction}{npc_sprite_index}.png')
except:
    try:
        # Intentar con otra estructura de directorios
        npc_image = pygame.image.load(f'assets/npc/{npc_sprite_direction}{npc_sprite_index}.png')
    except:
        # Si no existe la imagen, usar un placeholder
        npc_image = pygame.Surface((32, 48))
        npc_image.fill((255, 0, 255))  # Color magenta para el NPC
        print("No se pudo cargar la imagen del NPC. Usando placeholder.")

npc_rect = npc_image.get_rect()

# Distancia para interactuar con el NPC
interaction_distance = 60

# Diálogos del NPC
npc_dialogs = [
    "¡Ayuda! esto esta por empezar",
    "No puedo crerlo, estas aqui",
    "no pidas mucho esto es una alpha ",
    "¿Ya que estas? ¿deberias ganar?",
    "Venga va te lo mereces por escucharme",
    "ahora te sacare al menu por asustarme ",
    "boooo ooooo  ."
]
current_dialog = 0

# Definición de zonas de colisión basadas en la imagen del mapa
# Formato: [x1, y1, x2, y2] donde (x1,y1) es la esquina superior izquierda y (x2,y2) es la esquina inferior derecha
collision_zones = [
    # Bordes del mapa
    [0, 0, 1000, 300],  # Agua en la parte superior
    [0, 0, 150, 1200],  # Borde izquierdo
    [900, 0, 1000, 1000],  # Borde derecho
    [0, 200, 400, 600],  # Borde inferior

    # Colisión larga en el agua (puente en el centro superior)
    [150, 0, 500, 200],  # Parte izquierda del agua
    [700, 0, 1500, 200],  # Parte derecha del agua

    # Dos colisiones separadas en el centro del mapa
    [600, 400, 900, 600],  # Obstáculo en centro-izquierda
    [900, 500, 1000, 600]  # Obstáculo en centro-derecha
]


def check_collision(x, y):
    """
    Comprueba si la posición (x,y) colisiona con alguna zona definida
    en la lista collision_zones.

    Retorna True si hay colisión, False en caso contrario.
    """
    for zone in collision_zones:
        if zone[0] <= x <= zone[2] and zone[1] <= y <= zone[3]:
            return True
    return False


def imprimir_pantalla_fons(image, x, y):
    # Imprimeixo imatge de fons:
    background = pygame.image.load(image).convert()
    pantalla.blit(background, (x, y))


def draw_loading_screen():
    pantalla.fill((0, 0, 0))

    # Draw loading text
    loading_text = font_big.render("LOADING...", True, (255, 255, 255))
    pantalla.blit(loading_text, (VIEW_WIDTH // 2 - loading_text.get_width() // 2, VIEW_HEIGHT // 3))

    # Draw loading bar
    bar_width = 500  # Barra más ancha para la nueva resolución
    bar_height = 25  # Barra más alta
    bar_x = VIEW_WIDTH // 2 - bar_width // 2
    bar_y = VIEW_HEIGHT // 2

    # Border
    pygame.draw.rect(pantalla, (255, 255, 255), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), 2)

    # Progress
    global loading_progress
    progress_width = int(bar_width * (loading_progress / 100))
    pygame.draw.rect(pantalla, (0, 255, 0), (bar_x, bar_y, progress_width, bar_height))

    # Press SPACE text
    if loading_progress >= 100:
        space_text = font_medium.render("Press SPACE to continue", True, (255, 255, 255))
        pantalla.blit(space_text, (VIEW_WIDTH // 2 - space_text.get_width() // 2, VIEW_HEIGHT // 1.5))


def update_loading_screen():
    global loading_progress, loading_complete, loading_start_time

    # Simulate loading process
    current_time = pygame.time.get_ticks()
    elapsed_time = current_time - loading_start_time

    # Complete loading in 3 seconds
    if elapsed_time < 3000:
        loading_progress = min(100, int(elapsed_time / 3000 * 100))
    else:
        loading_progress = 100
        loading_complete = True


def draw_menu_screen():
    # Usar imagen de fondo para el menú si existe, si no usar un color azul oscuro
    if menu_background:
        # Escalar el fondo al nuevo tamaño si es necesario
        scaled_bg = pygame.transform.scale(menu_background, (VIEW_WIDTH, VIEW_HEIGHT))
        pantalla.blit(scaled_bg, (0, 0))
    else:
        pantalla.fill((0, 0, 50))

    # Title
    title_text = font_big.render("", True, (255, 255, 0))
    pantalla.blit(title_text, (VIEW_WIDTH // 2 - title_text.get_width() // 2, VIEW_HEIGHT // 4))

    # Menu options
    option1 = font_medium.render("1. Comenzar", True, (255, 255, 255))
    option2 = font_medium.render("2. Creditos", True, (255, 255, 255))
    option3 = font_medium.render("3. Salir", True, (255, 255, 255))

    pantalla.blit(option1, (VIEW_WIDTH // 2 - option1.get_width() // 2, VIEW_HEIGHT // 2))
    pantalla.blit(option2, (VIEW_WIDTH // 2 - option2.get_width() // 2, VIEW_HEIGHT // 2 + 50))
    pantalla.blit(option3, (VIEW_WIDTH // 2 - option3.get_width() // 2, VIEW_HEIGHT // 2 + 100))


def draw_credits_screen():
    pantalla.fill((0, 0, 0))

    # Credits title
    title_text = font_big.render("CREDITOS", True, (255, 255, 255))
    pantalla.blit(title_text, (VIEW_WIDTH // 2 - title_text.get_width() // 2, VIEW_HEIGHT // 4))

    # Credits content
    credit1 = font_medium.render("Hecho por: Xavi Balaña", True, (255, 255, 255))
    credit2 = font_medium.render("Arte hecho por:Xavi Balaña", True, (255, 255, 255))
    credit3 = font_medium.render("Musica por:", True, (255, 255, 255))
    back_text = font_medium.render("Press SPACE to return to menu", True, (255, 255, 255))

    pantalla.blit(credit1, (VIEW_WIDTH // 2 - credit1.get_width() // 2, VIEW_HEIGHT // 2))
    pantalla.blit(credit2, (VIEW_WIDTH // 2 - credit2.get_width() // 2, VIEW_HEIGHT // 2 + 40))
    pantalla.blit(credit3, (VIEW_WIDTH // 2 - credit3.get_width() // 2, VIEW_HEIGHT // 2 + 80))
    pantalla.blit(back_text, (VIEW_WIDTH // 2 - back_text.get_width() // 2, VIEW_HEIGHT - 60))


def handle_game_input():
    global bg_x, bg_y, sprite_direction, idle, sprite_index, last_change_frame_time, game_state

    current_time = pygame.time.get_ticks()
    # Moviment del jugador
    idle = True
    keys = pygame.key.get_pressed()

    # Verificar si se presiona ESC para volver al menú
    if keys[K_ESCAPE]:
        game_state = MENU
        return

    # Almacenar la posición actual antes de mover (para poder revertir si hay colisión)
    old_bg_x = bg_x
    old_bg_y = bg_y
    old_player_x = player_rect.x
    old_player_y = player_rect.y

    if keys[K_UP]:
        idle = False
        sprite_direction = "up"
        if player_rect.y > MARGIN_Y or bg_y >= 0:
            player_rect.y = max(player_rect.y - protagonist_speed, player_rect.height // 2)
        else:
            bg_y = min(bg_y + protagonist_speed, 0)
    if keys[K_DOWN]:
        idle = False
        sprite_direction = "down"
        if player_rect.y < VIEW_HEIGHT - MARGIN_Y or bg_y <= VIEW_HEIGHT - background_height:
            player_rect.y = min(player_rect.y + protagonist_speed, VIEW_HEIGHT - player_rect.height // 2)
        else:
            bg_y = max(bg_y - protagonist_speed, VIEW_HEIGHT - background_height)
    if keys[K_RIGHT]:
        idle = False
        sprite_direction = "right"
        if player_rect.x < VIEW_WIDTH - MARGIN_X or bg_x <= VIEW_WIDTH - background_width:
            player_rect.x = min(player_rect.x + protagonist_speed, VIEW_WIDTH - player_rect.width // 2)
        else:
            bg_x = max(bg_x - protagonist_speed, VIEW_WIDTH - background_width)
    if keys[K_LEFT]:
        idle = False
        sprite_direction = "left"
        if player_rect.x > MARGIN_X or bg_x >= 0:
            player_rect.x = max(player_rect.x - protagonist_speed, player_rect.width // 2)
        else:
            bg_x = min(bg_x + protagonist_speed, 0)

    # Calcular la posición absoluta del jugador en el mundo después del movimiento
    new_player_world_x = -bg_x + player_rect.centerx
    new_player_world_y = -bg_y + player_rect.centery

    # Verificar si la nueva posición colisiona con alguna zona de colisión
    if check_collision(new_player_world_x, new_player_world_y):
        # Si hay colisión, revertir el movimiento
        bg_x = old_bg_x
        bg_y = old_bg_y
        player_rect.x = old_player_x
        player_rect.y = old_player_y

    # frame number: (there are 3 frames only)
    # selccionem la imatge a mostrar
    if not idle:
        if current_time - last_change_frame_time >= animation_protagonist_speed:
            last_change_frame_time = current_time
            sprite_index = sprite_index + 1
            sprite_index = sprite_index % sprite_frame_number
    else:
        sprite_index = 0


def update_npc_animation():
    global npc_sprite_index, npc_last_change_frame_time

    current_time = pygame.time.get_ticks()

    # Si el NPC no está quieto (implementar lógica de movimiento más adelante)
    if not npc_idle:
        if current_time - npc_last_change_frame_time >= npc_animation_speed:
            npc_last_change_frame_time = current_time
            npc_sprite_index = (npc_sprite_index + 1) % npc_frame_number
    else:
        # Incluso cuando está quieto, hacer una animación lenta de "respiración"
        if current_time - npc_last_change_frame_time >= npc_animation_speed * 2:
            npc_last_change_frame_time = current_time
            npc_sprite_index = (npc_sprite_index + 1) % npc_frame_number


def check_npc_interaction():
    global game_state, current_dialog

    # Calcular la posición absoluta del jugador en el mundo
    player_world_x = -bg_x + player_rect.centerx
    player_world_y = -bg_y + player_rect.centery

    # Calcular la distancia entre el jugador y el NPC
    dx = player_world_x - npc_x
    dy = player_world_y - npc_y
    distance = (dx * dx + dy * dy) ** 0.5

    # Si el jugador está cerca del NPC y presiona E, iniciar diálogo
    keys = pygame.key.get_pressed()
    if distance < interaction_distance and keys[K_e]:
        game_state = DIALOG
        current_dialog = 0

        # Hacer que el NPC mire al jugador cuando habla
        if abs(dx) > abs(dy):
            # Más distancia horizontal que vertical
            if dx > 0:
                npc_sprite_direction = "left"  # NPC mira a la izquierda (hacia el jugador)
            else:
                npc_sprite_direction = "right"  # NPC mira a la derecha (hacia el jugador)
        else:
            # Más distancia vertical que horizontal
            if dy > 0:
                npc_sprite_direction = "up"  # NPC mira arriba (hacia el jugador)
            else:
                npc_sprite_direction = "down"  # NPC mira abajo (hacia el jugador)


def load_npc_sprite():
    global npc_image

    # Intentar cargar la imagen del sprite del NPC
    try:
        # Primero intenta esta estructura de directorio
        npc_image = pygame.image.load(f'assets/sprites/npc/{npc_sprite_direction}{npc_sprite_index}.png')
    except:
        try:
            # Si falla, intenta con esta otra estructura
            npc_image = pygame.image.load(f'assets/npc/{npc_sprite_direction}{npc_sprite_index}.png')
        except:
            try:
                # Y si también falla, intenta con la misma estructura que el protagonista
                npc_image = pygame.image.load(f'assets/sprites/{npc_sprite_direction}{npc_sprite_index}.png')
            except:
                # Si todas fallan, usa un placeholder
                if not isinstance(npc_image, pygame.Surface):
                    npc_image = pygame.Surface((32, 48))
                    npc_image.fill((255, 0, 255))  # Color magenta para el NPC


def draw_game_screen():
    global player_image, player_rect

    # Dibuixar el fons
    imprimir_pantalla_fons(background_image, bg_x, bg_y)

    # Actualizar animación del NPC
    update_npc_animation()

    # Cargar el sprite actual del NPC
    load_npc_sprite()

    # Dibujar  el NPC en la posición 700x900 del mundo
    # Convertir coordenadas del mundo a coordenadas de pantalla
    npc_screen_x = npc_x + bg_x
    npc_screen_y = npc_y + bg_y
    npc_rect.center = (npc_screen_x, npc_screen_y)
    pantalla.blit(npc_image, npc_rect)

    # Calcular la distancia entre el jugador y el NPC
    player_world_x = -bg_x + player_rect.centerx
    player_world_y = -bg_y + player_rect.centery
    dx = player_world_x - npc_x
    dy = player_world_y - npc_y
    distance = (dx * dx + dy * dy) ** 0.5

    # Si el jugador está cerca del NPC, mostrar un texto de interacción
    if distance < interaction_distance:
        interact_text = font_small.render("Presiona E para hablar", True, (255, 255, 255))
        pantalla.blit(interact_text, (npc_screen_x - interact_text.get_width() // 2, npc_screen_y - 40))

    # dibuixar el jugador
    player_image = pygame.image.load('assets/sprites/' + sprite_direction + str(sprite_index) + '.png')
    pantalla.blit(player_image, player_rect)

    # mantenir el jugador dins la finestra
    player_rect.clamp_ip(pantalla.get_rect())

    # Mostrar texto de ayuda para ESC
    esc_text = font_medium.render("ESC: Menu", True, (255, 255, 255))
    pantalla.blit(esc_text, (10, 10))

    # Mostrar coordenadas del personaje en el mundo (posición absoluta)
    pos_x = -bg_x + player_rect.centerx
    pos_y = -bg_y + player_rect.centery
    pos_text = font_medium.render(f"Pos: {pos_x}, {pos_y}", True, (255, 255, 255))
    pantalla.blit(pos_text, (10, 50))

    # DEBUG: Dibujar zonas de colisión (útil para depuración)
    for zone in collision_zones:
        x1, y1, x2, y2 = zone
        # Convertir coordenadas del mundo a coordenadas de pantalla
        screen_x1 = x1 + bg_x
        screen_y1 = y1 + bg_y
        screen_x2 = x2 + bg_x
        screen_y2 = y2 + bg_y

        # Dibujar un rectángulo semitransparente para la zona de colisión
        if screen_x2 > 0 and screen_x1 < VIEW_WIDTH and screen_y2 > 0 and screen_y1 < VIEW_HEIGHT:
            collision_surface = pygame.Surface((screen_x2 - screen_x1, screen_y2 - screen_y1))
            collision_surface.set_alpha(0)  # Muy transparente para ver el mapa

            pantalla.blit(collision_surface, (screen_x1, screen_y1))


def draw_dialog_screen():
    # Dibujar el juego en segundo plano (sin actualizar)
    draw_game_screen()

    # Dibujar un panel de diálogo en la parte inferior de la pantalla
    panel_height = 150
    panel_rect = pygame.Rect(20, VIEW_HEIGHT - panel_height - 20, VIEW_WIDTH - 40, panel_height)

    # Dibujar un fondo semitransparente para el diálogo
    dialog_surface = pygame.Surface((panel_rect.width, panel_rect.height))
    dialog_surface.set_alpha(200)  # Transparencia (0-255)
    dialog_surface.fill((0, 0, 50))  # Color azul oscuro
    pantalla.blit(dialog_surface, panel_rect)

    # Añadir borde al panel
    pygame.draw.rect(pantalla, (255, 255, 255), panel_rect, 2)

    # Dibujar el texto del diálogo actual
    dialog_text = font_medium.render(npc_dialogs[current_dialog], True, (255, 255, 255))
    pantalla.blit(dialog_text, (panel_rect.x + 20, panel_rect.y + 20))

    # Instrucciones
    if current_dialog < len(npc_dialogs) - 1:
        instruction = font_small.render("Presiona ESPACIO para continuar", True, (200, 200, 200))
    else:
        instruction = font_small.render("Presiona ESC para salir", True, (200, 200, 200))

    pantalla.blit(instruction, (panel_rect.x + 20, panel_rect.y + panel_rect.height - 30))


def clear_screen_transition():
    pantalla.fill((0, 0, 0))
    pygame.display.update()
    # Pequeña pausa para evitar parpadeos o problemas de renderizado
    # No detenemos la música aquí
    pygame.time.wait(50)


# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Asegurarse de detener la música antes de salir
            pygame.mixer.music.stop()
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            # Loading screen controls
            if game_state == LOADING and event.key == K_SPACE and loading_complete:
                clear_screen_transition()
                game_state = MENU

            # Menu screen controls
            elif game_state == MENU:
                if event.key == K_1:
                    # Limpiar la pantalla antes de cambiar al juego
                    clear_screen_transition()
                    # Restablecer posición del personaje y del fondo
                    player_rect = player_image.get_rect(center=(VIEW_WIDTH // 2, VIEW_HEIGHT // 2))
                    bg_x = -(500 - VIEW_WIDTH // 2)
                    bg_y = -(500 - VIEW_HEIGHT // 2)
                    # Cambiar al estado de juego
                    game_state = GAME
                elif event.key == K_2:
                    game_state = CREDITS
                elif event.key == K_3 or event.key == K_ESCAPE:
                    # Asegurarse de detener la música antes de salir
                    pygame.mixer.music.stop()
                    pygame.quit()
                    sys.exit()

            # Credits screen controls
            elif game_state == CREDITS and (event.key == K_SPACE or event.key == K_ESCAPE):
                clear_screen_transition()
                game_state = MENU

            # Game controls - ESC to return to menu
            elif game_state == GAME and event.key == K_ESCAPE:
                clear_screen_transition()
                game_state = MENU

            # Dialog controls
            elif game_state == DIALOG:
                if event.key == K_SPACE:
                    # Avanzar al siguiente diálogo
                    if current_dialog < len(npc_dialogs) - 1:
                        current_dialog += 1
                    else:
                        # Al finalizar el diálogo, volver al juego
                        game_state = MENU  # Siguiendo la lógica del último diálogo que dice "ahora te sacaré al menú"
                elif event.key == K_ESCAPE:
                    # Salir del diálogo
                    game_state = GAME

    # Handle different game states
    if game_state == LOADING:
        update_loading_screen()
        draw_loading_screen()

    elif game_state == MENU:
        # Asegurarse de que la pantalla se limpia completamente antes de dibujar el menú
        pantalla.fill((0, 0, 0))
        draw_menu_screen()

    elif game_state == GAME:
        handle_game_input()
        check_npc_interaction()  # Verificar si el jugador interactúa con el NPC
        draw_game_screen()

    elif game_state == CREDITS:
        draw_credits_screen()

    elif game_state == DIALOG:
        draw_dialog_screen()

    pygame.display.update()
    clock.tick(fps)
