import pygame
from collections import deque
import numpy as np


import json
import os
from datetime import datetime

# Fichier de sauvegarde des scores
SCORES_FILE = "scores.txt"


pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

SIZE = 40
WINDOW_WIDTH = 480  # Agrandi pour des niveaux plus larges
WINDOW_HEIGHT = 580  # Agrandi pour des niveaux plus hauts
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Sokoban BFS")

# États du jeu
MENU = "menu"
PLAYING = "playing"
LEVEL_COMPLETE = "level_complete"
game_state = MENU

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)
RED = (200, 0, 0)
DARK_RED = (150, 0, 0)
BLUE = (0, 100, 200)
GOLD = (255, 215, 0)
ORANGE = (255, 165, 0)

# Variables pour le nom du joueur
player_name = ""
input_active = False

# États du jeu
MENU = "menu"
ALGORITHM_CHOICE = "algorithm_choice"  # NOUVEAU
NAME_INPUT = "name_input"
PLAYING = "playing"
LEVEL_COMPLETE = "level_complete"
GAME_OVER = "game_over"
game_state = MENU

# Variables pour le nom du joueur et algorithme
player_name = ""
input_active = False
selected_algorithm = "BFS"  # NOUVEAU - par défaut BFS












# Niveaux progressifs
levels = [
    # Niveau 1 - Très facile
    [
        "########",
        "#      #",
        "# $  . #",
        "#   P  #",
        "#      #",
        "########",
    ],
    
    # Niveau 2 - Facile
    [
        "##########",
        "##      ##",
        "## $    ##",
        "##     P##",
        "##      ##",
        "####  ####",
        "##### ####",
        "##      ##",
        "### .  ###",
        "##########",
    ],
    
    # Niveau 3 - Moyen
    [
        "############",
        "#     #    #",
        "# $   #  . #",
        "## #  #  # #",
        "#     P    #",
        "#   $    . #",
        "############",
    ],
    

]

current_level = 0

# Fonction pour générer des sons synthétiques
def generate_push_sound():
    """Génère un son de poussée de caisse"""
    duration = 0.3
    sample_rate = 22050
    frames = int(duration * sample_rate)
    
    # Son de type "thud" avec fréquences basses
    arr = np.zeros((frames, 2))
    
    # Enveloppe décroissante
    envelope = np.linspace(1.0, 0.0, frames)
    
    # Mélange de fréquences pour un son de choc
    for freq in [80, 120, 160]:
        wave = np.sin(2 * np.pi * freq * np.linspace(0, duration, frames))
        arr[:, 0] += wave * envelope * 0.3
        arr[:, 1] += wave * envelope * 0.3
    
    # Ajouter du bruit pour l'effet "thud"
    noise = np.random.normal(0, 0.1, (frames, 2))
    arr += noise * envelope.reshape(-1, 1) * 0.2
    
    # Normaliser et convertir
    arr = np.clip(arr, -1, 1)
    sound_array = (arr * 32767).astype(np.int16)
    
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

def generate_victory_music():
    """Génère une mélodie de victoire"""
    duration = 3.0
    sample_rate = 22050
    frames = int(duration * sample_rate)
    
    # Mélodie simple et joyeuse (Do-Mi-Sol-Do)
    notes = [261.63, 329.63, 392.00, 523.25, 392.00, 329.63, 261.63]  # C-E-G-C-G-E-C
    note_duration = duration / len(notes)
    note_frames = int(note_duration * sample_rate)
    
    arr = np.zeros((frames, 2))
    
    for i, freq in enumerate(notes):
        start = i * note_frames
        end = min(start + note_frames, frames)
        note_length = end - start
        
        if note_length > 0:
            # Enveloppe douce pour chaque note
            t = np.linspace(0, note_duration, note_length)
            envelope = np.exp(-t * 2) * (1 - np.exp(-t * 10))
            
            # Son de cloche/piano synthétique
            wave = (np.sin(2 * np.pi * freq * t) * 0.5 +
                   np.sin(2 * np.pi * freq * 2 * t) * 0.2 +
                   np.sin(2 * np.pi * freq * 3 * t) * 0.1) * envelope
            
            arr[start:end, 0] += wave
            arr[start:end, 1] += wave
    
    # Normaliser
    arr = np.clip(arr, -1, 1)
    sound_array = (arr * 16383).astype(np.int16)  # Volume plus doux
    
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

def generate_level_complete_sound():
    """Génère un son de fin de niveau plus court"""
    duration = 1.5
    sample_rate = 22050
    frames = int(duration * sample_rate)
    
    # Mélodie courte et positive
    notes = [392.00, 523.25, 659.25]  # G-C-E
    note_duration = duration / len(notes)
    note_frames = int(note_duration * sample_rate)
    
    arr = np.zeros((frames, 2))
    
    for i, freq in enumerate(notes):
        start = i * note_frames
        end = min(start + note_frames, frames)
        note_length = end - start
        
        if note_length > 0:
            t = np.linspace(0, note_duration, note_length)
            envelope = np.exp(-t * 1.5) * (1 - np.exp(-t * 8))
            
            wave = (np.sin(2 * np.pi * freq * t) * 0.6 +
                   np.sin(2 * np.pi * freq * 2 * t) * 0.3) * envelope
            
            arr[start:end, 0] += wave
            arr[start:end, 1] += wave
    
    arr = np.clip(arr, -1, 1)
    sound_array = (arr * 20000).astype(np.int16)
    
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

# Générer les sons
push_sound = generate_push_sound()
victory_music = generate_victory_music()
level_complete_sound = generate_level_complete_sound()


def save_score(name, level_reached, completed_all=False):
    """Sauvegarde le score du joueur"""
    global selected_algorithm  # AJOUTER cette ligne
    
    score_data = {
        'name': name,
        'level_reached': level_reached,
        'completed_all': completed_all,
        'algorithm': selected_algorithm,  # NOUVEAU
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Lire les scores existants
    scores = load_scores()
    scores.append(score_data)
    
    # Sauvegarder dans le fichier
    try:
        with open(SCORES_FILE, 'w', encoding='utf-8') as f:
            for score in scores:
                status = "VICTOIRE TOTALE" if score.get('completed_all', False) else f"NIVEAU {score.get('level_reached', 1)}"
                algo = score.get('algorithm', 'BFS')  # Par défaut BFS pour les anciens scores
                f.write(f"{score['name']} - {status} - {algo} - {score['date']}\n")
        print(f"Score sauvegardé pour {name}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")

def load_scores():
    """Charge les scores depuis le fichier"""
    scores = []
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if ' - ' in line:
                        parts = line.strip().split(' - ')
                        if len(parts) >= 3:
                            name = parts[0]
                            status = parts[1]
                            date = parts[2]
                            
                            completed_all = "VICTOIRE TOTALE" in status
                            if completed_all:
                                level_reached = len(levels)
                            else:
                                try:
                                    level_reached = int(status.split()[1])
                                except:
                                    level_reached = 1
                            
                            scores.append({
                                'name': name,
                                'level_reached': level_reached,
                                'completed_all': completed_all,
                                'date': date
                            })
        except Exception as e:
            print(f"Erreur lors du chargement: {e}")
    return scores

def draw_name_input():
    """Dessine l'écran de saisie du nom"""
    screen.fill(DARK_GRAY)
    
    # Titre
    title_font = pygame.font.Font(None, 48)
    title_text = title_font.render("ENTREZ VOTRE NOM", True, WHITE)
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
    screen.blit(title_text, title_rect)
    
    # Zone de saisie
    input_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, 280, 300, 50)
    color = WHITE if input_active else GRAY
    pygame.draw.rect(screen, color, input_rect, 3)
    
    # Texte saisi
    font = pygame.font.Font(None, 36)
    text_surface = font.render(player_name, True, WHITE)
    screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))
    
    # Instructions
    instr_font = pygame.font.Font(None, 24)
    instr_text = instr_font.render("Appuyez sur ENTRÉE pour commencer", True, GRAY)
    instr_rect = instr_text.get_rect(center=(WINDOW_WIDTH // 2, 380))
    screen.blit(instr_text, instr_rect)

def draw_game_over():
    """Dessine l'écran de game over"""
    screen.fill(DARK_GRAY)
    
    # Titre
    title_font = pygame.font.Font(None, 48)
    title_text = title_font.render("PARTIE TERMINÉE", True, RED)
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 150))
    screen.blit(title_text, title_rect)
    
    # Score atteint
    score_font = pygame.font.Font(None, 32)
    score_text = score_font.render(f"Niveau atteint: {current_level + 1}/{len(levels)}", True, WHITE)
    score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 220))
    screen.blit(score_text, score_rect)
    
    # Nom du joueur
    name_text = score_font.render(f"Joueur: {player_name}", True, GOLD)
    name_rect = name_text.get_rect(center=(WINDOW_WIDTH // 2, 260))
    screen.blit(name_text, name_rect)
    
    # Message sauvegarde
    save_font = pygame.font.Font(None, 24)
    save_text = save_font.render("Score sauvegardé!", True, GREEN)
    save_rect = save_text.get_rect(center=(WINDOW_WIDTH // 2, 300))
    screen.blit(save_text, save_rect)
    
    # Bouton retour menu
    restart_button = Button(WINDOW_WIDTH // 2 - 100, 350, 200, 50, "NOUVELLE PARTIE", GREEN, WHITE, 28)
    restart_button.draw(screen)


class Button:
    def __init__(self, x, y, width, height, text, color, text_color, font_size=36):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.Font(None, font_size)
        self.hover_color = (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30))
        self.pressed_color = (max(0, color[0] - 30), max(0, color[1] - 30), max(0, color[2] - 30))
        self.is_pressed = False
        self.is_hovered = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed:
                self.is_pressed = False
                if self.rect.collidepoint(event.pos):
                    return True
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        return False
    
    def draw(self, screen):
        # Choisir la couleur selon l'état
        if self.is_pressed:
            color = self.pressed_color
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.color
        
        # Dessiner le bouton avec bordure
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 3)
        
        # Dessiner le texte centré
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class Game:
    def __init__(self):
        self.level_data = levels[current_level]
        self.reset()
        self.victory_played = False
        self.game_states = []  # Historique des états du jeu
    
    def load_level(self, level_index):
        if 0 <= level_index < len(levels):
            self.level_data = levels[level_index]
            self.reset()
    
    def reset(self):
        self.boxes = set()
        self.goals = set()
        self.victory_played = False
        self.game_states = []  # Réinitialiser l'historique
        for y, row in enumerate(self.level_data):
            for x, cell in enumerate(row):
                if cell == 'P':
                    self.player = (x, y)
                elif cell == '$':
                    self.boxes.add((x, y))
                elif cell == '.':
                    self.goals.add((x, y))
        # Sauvegarder l'état initial
        self.save_state()
    
    def save_state(self):
        """Sauvegarde l'état actuel du jeu"""
        state = {
            'player': self.player,
            'boxes': self.boxes.copy()
        }
        self.game_states.append(state)
    
    def undo_move(self):
        """In do"""
        if len(self.game_states) > 1:  # Garder au moins l'état initial
            self.game_states.pop()  # Supprimer l'état actuel
            previous_state = self.game_states[-1]  # Récupérer l'état précédent
            self.player = previous_state['player']
            self.boxes = previous_state['boxes'].copy()
            return True
        return False
    
    def move(self, dx, dy):
        px, py = self.player
        nx, ny = px + dx, py + dy
        
        # Vérifier mur
        if ny < 0 or ny >= len(self.level_data) or nx < 0 or nx >= len(self.level_data[ny]) or self.level_data[ny][nx] == '#':
            return False
        
        box_pushed = False
        
        # Vérifier boîte
        if (nx, ny) in self.boxes:
            bx, by = nx + dx, ny + dy
            if (by < 0 or by >= len(self.level_data) or 
                bx < 0 or bx >= len(self.level_data[by]) or 
                self.level_data[by][bx] == '#' or (bx, by) in self.boxes):
                return False
            self.boxes.remove((nx, ny))
            self.boxes.add((bx, by))
            box_pushed = True
        
        self.player = (nx, ny)
        
        # Sauvegarder le nouvel état après un mouvement réussi
        self.save_state()
        
        # Jouer le son de poussée si une boîte a été déplacée
        if box_pushed:
            push_sound.play()
        
        return True
    
    def is_solved(self):
        solved = self.boxes == self.goals
        # Jouer la musique appropriée une seule fois
        if solved and not self.victory_played:
            if current_level == len(levels) - 1:  # Dernier niveau
                victory_music.play()
            else:
                level_complete_sound.play()
            self.victory_played = True
        return solved
    
    def get_state(self):
        return (self.player, tuple(sorted(self.boxes)))

def bfs_solve(game):
    start_state = game.get_state()
    queue = deque([(start_state, [])])
    visited = {start_state}
    
    while queue:
        state, path = queue.popleft()
        
        # Restaurer l'état
        game.player, boxes = state
        game.boxes = set(boxes)
        
        if game.boxes == game.goals:  # Vérification directe pour éviter de jouer le son
            return path
        
        # Essayer tous les mouvements
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            old_player, old_boxes = game.player, game.boxes.copy()
            
            if game.move_silent(dx, dy):  # Version silencieuse pour l'IA
                new_state = game.get_state()
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_state, path + [(dx, dy)]))
            
            # Restaurer
            game.player, game.boxes = old_player, old_boxes
    
    return []


def dfs_solve(game, max_depth=30, max_states=10000):
    """Résout le puzzle avec Depth-First Search optimisé"""
    start_state = game.get_state()
    visited = set()
    states_explored = 0
    

import time  # Ajouter cet import en haut du fichier

def dfs_solve(game, max_depth=25, timeout_seconds=5):
    """Résout le puzzle avec DFS et timeout de sécurité"""
    start_time = time.time()
    start_state = game.get_state()
    visited = set()
    states_explored = 0
    best_solution = None
    
    def dfs_recursive(state, path, depth):
        nonlocal states_explored, best_solution
        states_explored += 1
        
        # Vérifier le timeout
        if time.time() - start_time > timeout_seconds:
            return "TIMEOUT"
        
        # Limite de profondeur
        if depth > max_depth:
            return None
            
        # Restaurer l'état
        game.player, boxes = state
        game.boxes = set(boxes)
        
        # Solution trouvée
        if game.boxes == game.goals:
            print(f"DFS: Solution trouvée en {len(path)} mouvements")
            return path
        
        # Éviter les cycles
        if state in visited:
            return None
        
        visited.add(state)
        
        # Essayer tous les mouvements
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            old_player, old_boxes = game.player, game.boxes.copy()
            
            if game.move_silent(dx, dy):
                new_state = game.get_state()
                if new_state not in visited:
                    result = dfs_recursive(new_state, path + [(dx, dy)], depth + 1)
                    if result == "TIMEOUT":
                        return "TIMEOUT"
                    elif result is not None:
                        return result
            
            game.player, game.boxes = old_player, old_boxes
        
        visited.remove(state)
        return None
    
    print(f"DFS: Recherche avec timeout de {timeout_seconds}s...")
    result = dfs_recursive(start_state, [], 0)
    
    if result == "TIMEOUT":
        print(f"DFS: Timeout après {timeout_seconds}s - Fallback vers BFS")
        return bfs_solve(game)
    elif result is None:
        print(f"DFS: Aucune solution trouvée - Fallback vers BFS")
        return bfs_solve(game)
    
    return result


# Ajouter une version silencieuse du mouvement pour l'IA
def move_silent(self, dx, dy):
    px, py = self.player
    nx, ny = px + dx, py + dy
    
    if (ny < 0 or ny >= len(self.level_data) or 
        nx < 0 or nx >= len(self.level_data[ny]) or 
        self.level_data[ny][nx] == '#'):
        return False
    
    if (nx, ny) in self.boxes:
        bx, by = nx + dx, ny + dy
        if (by < 0 or by >= len(self.level_data) or 
            bx < 0 or bx >= len(self.level_data[by]) or 
            self.level_data[by][bx] == '#' or (bx, by) in self.boxes):
            return False
        self.boxes.remove((nx, ny))
        self.boxes.add((bx, by))
    
    self.player = (nx, ny)
    return True

# Ajouter la méthode silencieuse à la classe
Game.move_silent = move_silent

def get_level_offset():
    """Calcule l'offset pour centrer le niveau"""
    level_width = len(game.level_data[0]) * SIZE
    level_height = len(game.level_data) * SIZE
    offset_x = (WINDOW_WIDTH - level_width) // 2
    offset_y = (WINDOW_HEIGHT - level_height - 80) // 2  # -80 pour laisser place aux boutons
    return offset_x, offset_y

def draw_menu():
    screen.fill(DARK_GRAY)

    # Bouton d'entrée , entrée le nom du joueur
    enter_button = Button(WINDOW_WIDTH // 2 - 100, 320, 200, 60, "COMMENCER", GREEN, WHITE, 36)
    
    # Titre SOKOBAN
    title_font = pygame.font.Font(None, 72)
    title_text = title_font.render("SOKOBAN", True, WHITE)
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 150))
    screen.blit(title_text, title_rect)
    
    # Sous-titre
    subtitle_font = pygame.font.Font(None, 24)
    subtitle_text = subtitle_font.render("Résolution automatique par BFS", True, GRAY)
    subtitle_rect = subtitle_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
    screen.blit(subtitle_text, subtitle_rect)
    
    # Afficher le niveau actuel
    level_font = pygame.font.Font(None, 36)
    level_text = level_font.render(f"Niveau {current_level + 1}/{len(levels)}", True, GOLD)
    level_rect = level_text.get_rect(center=(WINDOW_WIDTH // 2, 250))
    screen.blit(level_text, level_rect)
    
    # Dessiner le bouton d'entrée
    enter_button.draw(screen)

def draw_level_complete():
    screen.fill(DARK_GRAY)
    
    # Titre de félicitations
    if current_level == len(levels) - 1:
        title_text = "FÉLICITATIONS!"
        subtitle_text = "Vous avez terminé tous les niveaux!"
    else:
        title_text = "NIVEAU TERMINÉ!"
        subtitle_text = f"Niveau {current_level + 1} complété!"
    
    title_font = pygame.font.Font(None, 48)
    title_surface = title_font.render(title_text, True, GOLD)
    title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 200))
    screen.blit(title_surface, title_rect)
    
    subtitle_font = pygame.font.Font(None, 32)
    subtitle_surface = subtitle_font.render(subtitle_text, True, WHITE)
    subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, 250))
    screen.blit(subtitle_surface, subtitle_rect)
    
    # Dessiner les boutons selon le niveau actuel
    if current_level < len(levels) - 1:  # Pas le dernier niveau
        next_level_button.draw(screen)
        # Repositionner le bouton menu
        menu_button_pos = Button(WINDOW_WIDTH // 2 - 80, 390, 160, 40, "MENU PRINCIPAL", RED, WHITE, 24)
        menu_button_pos.draw(screen)
    else:  # Dernier niveau - seulement le bouton menu centré
        menu_button_centered = Button(WINDOW_WIDTH // 2 - 80, 320, 160, 40, "MENU PRINCIPAL", RED, WHITE, 24)
        menu_button_centered.draw(screen)



def draw_algorithm_choice():
    """Dessine l'écran de choix d'algorithme"""
    screen.fill(DARK_GRAY)
    
    # Titre
    title_font = pygame.font.Font(None, 48)
    title_text = title_font.render("CHOISIR L'ALGORITHME", True, WHITE)
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 150))
    screen.blit(title_text, title_rect)
    
    # Description des algorithmes
    desc_font = pygame.font.Font(None, 24)
    
    # BFS
    bfs_color = GOLD if selected_algorithm == "BFS" else WHITE
    bfs_text = desc_font.render("BFS (Breadth-First Search)", True, bfs_color)
    bfs_rect = bfs_text.get_rect(center=(WINDOW_WIDTH // 2, 220))
    screen.blit(bfs_text, bfs_rect)
    
    bfs_desc = desc_font.render("• Solution optimale garantie", True, GRAY)
    bfs_desc_rect = bfs_desc.get_rect(center=(WINDOW_WIDTH // 2, 245))
    screen.blit(bfs_desc, bfs_desc_rect)
    
    bfs_desc2 = desc_font.render("• Explore niveau par niveau", True, GRAY)
    bfs_desc2_rect = bfs_desc2.get_rect(center=(WINDOW_WIDTH // 2, 265))
    screen.blit(bfs_desc2, bfs_desc2_rect)
    
    # DFS
    dfs_color = GOLD if selected_algorithm == "DFS" else WHITE
    dfs_text = desc_font.render("DFS (Depth-First Search)", True, dfs_color)
    dfs_rect = dfs_text.get_rect(center=(WINDOW_WIDTH // 2, 320))
    screen.blit(dfs_text, dfs_rect)
    
    dfs_desc = desc_font.render("• Plus rapide à trouver une solution", True, GRAY)
    dfs_desc_rect = dfs_desc.get_rect(center=(WINDOW_WIDTH // 2, 345))
    screen.blit(dfs_desc, dfs_desc_rect)
    
    dfs_desc2 = desc_font.render("• Solution pas forcément optimale", True, GRAY)
    dfs_desc2_rect = dfs_desc2.get_rect(center=(WINDOW_WIDTH // 2, 365))
    screen.blit(dfs_desc2, dfs_desc2_rect)
    
    # Instructions
    instr_font = pygame.font.Font(None, 28)
    instr_text = instr_font.render("↑↓ pour changer, ENTRÉE pour confirmer", True, WHITE)
    instr_rect = instr_text.get_rect(center=(WINDOW_WIDTH // 2, 450))
    screen.blit(instr_text, instr_rect)
    
    # Indicateur de sélection
    if selected_algorithm == "BFS":
        pygame.draw.rect(screen, GOLD, (WINDOW_WIDTH // 2 - 200, 210, 400, 70), 3)
    else:
        pygame.draw.rect(screen, GOLD, (WINDOW_WIDTH // 2 - 200, 310, 400, 70), 3)














def draw_game():
    screen.fill((50, 50, 50))
    
    offset_x, offset_y = get_level_offset()

    # Afficher informations en haut
    info_font = pygame.font.Font(None, 24)
    level_text = info_font.render(f"Niveau {current_level + 1}/{len(levels)}", True, WHITE)
    screen.blit(level_text, (10, 10))

    # NOUVEAU - Afficher l'algorithme utilisé
    algo_text = info_font.render(f"Algorithme: {selected_algorithm}", True, GOLD)
    screen.blit(algo_text, (200, 10))
    
    # Dessiner niveau
    for y, row in enumerate(game.level_data):
        for x, cell in enumerate(row):
            rect = pygame.Rect(x * SIZE + offset_x, y * SIZE + offset_y, SIZE, SIZE)
            if cell == '#':
                pygame.draw.rect(screen, (100, 100, 100), rect)
    
    # Dessiner objectifs
    for x, y in game.goals:
        pygame.draw.circle(screen, (0, 255, 0), 
                         (x * SIZE + SIZE//2 + offset_x, y * SIZE + SIZE//2 + offset_y), SIZE//4)
    
    # Dessiner boîtes
    for x, y in game.boxes:
        color = (255, 255, 0) if (x, y) in game.goals else (139, 69, 19)
        pygame.draw.rect(screen, color, 
                        (x * SIZE + 5 + offset_x, y * SIZE + 5 + offset_y, SIZE - 10, SIZE - 10))
    
    # Dessiner joueur
    px, py = game.player
    pygame.draw.circle(screen, (255, 0, 0), 
                      (px * SIZE + SIZE//2 + offset_x, py * SIZE + SIZE//2 + offset_y), SIZE//3)
    
    # Afficher informations en haut
    info_font = pygame.font.Font(None, 24)
    level_text = info_font.render(f"Niveau {current_level + 1}/{len(levels)}", True, WHITE)
    screen.blit(level_text, (10, 10))
    
    if move_index < len(solution):
        progress_text = info_font.render(f"ESPACE: {move_index}/{len(solution)}", True, WHITE)
        screen.blit(progress_text, (10, 35))
    else:
        complete_text = info_font.render("Solution terminée! R pour recommencer", True, WHITE)
        screen.blit(complete_text, (10, 35))
    
    # Afficher les contrôles
    controls_text = info_font.render("BACKSPACE: Annuler mouvement", True, WHITE)
    screen.blit(controls_text, (10, 60))
    
    # Dessiner les boutons
    exit_button.draw(screen)
    undo_button.draw(screen)

# Créer les boutons
enter_button = Button(WINDOW_WIDTH // 2 - 100, 320, 200, 60, "ENTRER", GREEN, WHITE, 36)
exit_button = Button(WINDOW_WIDTH // 2 - 130, 520, 120, 40, "MENU", RED, WHITE, 24)
undo_button = Button(WINDOW_WIDTH // 2 + 10, 520, 120, 40, "ANNULER", ORANGE, WHITE, 24)
next_level_button = Button(WINDOW_WIDTH // 2 - 120, 320, 240, 50, "NIVEAU SUIVANT", BLUE, WHITE, 28)
menu_button = Button(WINDOW_WIDTH // 2 - 80, 390, 160, 40, "MENU PRINCIPAL", RED, WHITE, 24)

# Initialiser le jeu
game = Game()
solution = []
move_index = 0
clock = pygame.time.Clock()

print("Bienvenue dans Sokoban!")
print(f"3 niveaux disponibles - Niveau actuel: {current_level + 1}")
print("Cliquez sur ENTRER pour commencer")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        if game_state == MENU:
            if enter_button.handle_event(event):
                game_state = ALGORITHM_CHOICE  # MODIFIÉ - aller au choix d'algorithme
        
        elif game_state == ALGORITHM_CHOICE:  # NOUVEAU
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    selected_algorithm = "DFS" if selected_algorithm == "BFS" else "BFS"
                elif event.key == pygame.K_RETURN:
                    game_state = NAME_INPUT
                    input_active = True
                elif event.key == pygame.K_ESCAPE:
                    game_state = MENU
        
        elif game_state == NAME_INPUT:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and player_name.strip():
                    game_state = PLAYING
                    game.load_level(current_level)
                    
                    # MODIFIÉ - Choisir l'algorithme selon la sélection
                    print(f"Résolution du niveau {current_level + 1} avec {selected_algorithm}...")
                    if selected_algorithm == "BFS":
                        solution = bfs_solve(game)
                    else:  # DFS
                        solution = dfs_solve(game)
                    
                    game.reset()
                    move_index = 0
                    if solution:
                        print(f"Solution trouvée en {len(solution)} mouvements avec {selected_algorithm}!")
                    else:
                        print(f"Aucune solution trouvée avec {selected_algorithm} (limite de profondeur atteinte)")
                    print(f"Joueur: {player_name}")
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.key == pygame.K_ESCAPE:
                    game_state = ALGORITHM_CHOICE  # MODIFIÉ - retour au choix d'algorithme
                    player_name = ""
                    input_active = False
                else:
                    if len(player_name) < 20 and event.unicode.isprintable():
                        player_name += event.unicode
        
        elif game_state == PLAYING:
            if exit_button.handle_event(event):
                save_score(player_name, current_level + 1, False)
                game_state = GAME_OVER
            
            if undo_button.handle_event(event):
                if game.undo_move():
                    if move_index > 0:
                        move_index -= 1
                    print("Annulation")
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and move_index < len(solution):
                    dx, dy = solution[move_index]
                    game.move(dx, dy)
                    move_index += 1
                    
                    if game.is_solved():
                        game_state = LEVEL_COMPLETE
                        
                elif event.key == pygame.K_r:
                    game.reset()
                    move_index = 0
                elif event.key == pygame.K_BACKSPACE:
                    if game.undo_move():
                        if move_index > 0:
                            move_index -= 1
                        print("Annulation")
                elif event.key == pygame.K_ESCAPE:
                    save_score(player_name, current_level + 1, False)
                    game_state = GAME_OVER
        
        elif game_state == LEVEL_COMPLETE:
            if current_level < len(levels) - 1:
                if next_level_button.handle_event(event):
                    current_level += 1
                    print(f"Passage au niveau {current_level + 1}")
                    game_state = PLAYING
                    game.load_level(current_level)
                    
                    # MODIFIÉ - Utiliser l'algorithme sélectionné
                    if selected_algorithm == "BFS":
                        solution = bfs_solve(game)
                    else:
                        solution = dfs_solve(game)
                    
                    game.reset()
                    move_index = 0
                    print(f"Solution trouvée en {len(solution)} mouvements avec {selected_algorithm}!")
                
                menu_click_area = pygame.Rect(WINDOW_WIDTH // 2 - 80, 390, 160, 40)
                if event.type == pygame.MOUSEBUTTONDOWN and menu_click_area.collidepoint(event.pos):
                    save_score(player_name, current_level + 1, False)
                    game_state = GAME_OVER
            else:
                save_score(player_name, len(levels), True)
                menu_click_area = pygame.Rect(WINDOW_WIDTH // 2 - 80, 320, 160, 40)
                if event.type == pygame.MOUSEBUTTONDOWN and menu_click_area.collidepoint(event.pos):
                    game_state = GAME_OVER
        
        elif game_state == GAME_OVER:
            restart_click_area = pygame.Rect(WINDOW_WIDTH // 2 - 100, 350, 200, 50)
            if event.type == pygame.MOUSEBUTTONDOWN and restart_click_area.collidepoint(event.pos):
                current_level = 0
                player_name = ""
                selected_algorithm = "BFS"  # NOUVEAU - réinitialiser
                game_state = MENU
                move_index = 0
                solution = []
    
    # Dessiner selon l'état du jeu
    if game_state == MENU:
        draw_menu()
    elif game_state == ALGORITHM_CHOICE:  # NOUVEAU
        draw_algorithm_choice()
    elif game_state == NAME_INPUT:
        draw_name_input()
    elif game_state == PLAYING:
        draw_game()
    elif game_state == LEVEL_COMPLETE:
        draw_level_complete()
    elif game_state == GAME_OVER:
        draw_game_over()
    
    pygame.display.flip()
    clock.tick(60)