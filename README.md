# Froststep

**Froststep** is a top-down survival game built with **Pygame**.
Collect resources, keep the beacon alive, and survive the cold as long as you can.

> Built for the **Pygame Community Winter Jam 2026**
>
> Submitted to **itch.io**

---

## 🎮 Gameplay

You play as a wanderer in a frozen world. Your goal is to keep the beacon lit by gathering fuel and depositing it at the beacon.

### 🔥 Core Loop
- Gather **wood** and **membrane** by interacting with trees and picking up dropped items.
- Carry resources in a small inventory (3 slots).
- Deposit resources at the **beacon** to keep your warmth level up.
- Keep an eye on your **warmth meter** and **time left**.
- Avoid (or survive) enemies like spiders roaming the map.

---

## 🕹️ Controls

- **Move:** Arrow keys / WASD
- **Interact / Pick up / Deposit:** `E`
- **Drop selected inventory item:** `Q`
- **Switch inventory slot:** Mouse wheel
- **Toggle full screen:** `F11`

### Debug toggles (for development)
- `F1` – Toggle UI debug overlay
- `F2` – Toggle hitbox debug overlay
- `F3` – Toggle console debug output
- `1` / `2` – Switch background map texture

---

## 🚀 Running the Game

### Requirements
- Python 3.10+ (recommended)
- `pygame` library

### Install Dependencies
```bash
pip install pygame
```

### Run
```bash
python main.py
```

---

## 🗂️ Project Structure

- `main.py` – Game entry point and main loop
- `player.py` – Player movement and state
- `enemy.py` – Enemy AI (spiders)
- `objects.py` – Trees, pickups, and world objects
- `ui.py` – UI elements (inventory, warmth bar, popouts)
- `utilities.py` – Helper utilities (sprite loading, text rendering, timers)
- `Assets/` – Textures, sounds, icons, fonts, etc.

---

## 🎁 Notes for Jam

- This game was created for **Pygame Community Winter Jam 2026**.
- Feel free to fork, modify, and expand the mechanics (more enemy types, crafting, additional maps, etc.).

---

## 📝 License

This repository is provided as-is. Feel free to use or modify the code in your own projects.
