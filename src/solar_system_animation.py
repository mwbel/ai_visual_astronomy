import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

def animate_solar_system(show_earth_orbit=True, show_moon_orbit=True, save_animation=False, filename="solar_system_animation.mp4"):
    # Constants and parameters (simplified for educational purposes)
    sun_radius = 0.1
    earth_radius = 0.03
    moon_radius = 0.01

    earth_orbit_radius = 1.0
    moon_orbit_radius = 0.15

    earth_speed_factor = 1.0  # Earth's orbital speed around the Sun
    moon_speed_factor = 10.0  # Moon's orbital speed around Earth (faster)

    # Colors
    sun_color = 'yellow'
    earth_color = 'blue'
    moon_color = 'gray'

    # Setup the figure and axes
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_aspect('equal')
    ax.set_xlim([-1.5, 1.5])
    ax.set_ylim([-1.5, 1.5])
    ax.set_facecolor('black')
    ax.set_title("Solar System Animation")

    # Sun (fixed at origin)
    sun = plt.Circle((0, 0), sun_radius, color=sun_color, zorder=0)
    ax.add_patch(sun)

    # Earth
    earth_patch = plt.Circle((earth_orbit_radius, 0), earth_radius, color=earth_color, zorder=1)
    ax.add_patch(earth_patch)
    earth_orbit_line, = ax.plot([], [], 'w--', lw=0.5) # Earth's orbit path

    # Moon
    moon_patch = plt.Circle((earth_orbit_radius + moon_orbit_radius, 0), moon_radius, color=moon_color, zorder=2)
    ax.add_patch(moon_patch)
    moon_orbit_line, = ax.plot([], [], 'w:', lw=0.3) # Moon's orbit path around Earth

    # Animation update function
    def update(frame):
        # Earth's position around the Sun
        earth_angle = frame * (np.pi / 180) * earth_speed_factor
        earth_x = earth_orbit_radius * np.cos(earth_angle)
        earth_y = earth_orbit_radius * np.sin(earth_angle)
        earth_patch.set_center((earth_x, earth_y))

        # Moon's position around Earth
        moon_angle = frame * (np.pi / 180) * moon_speed_factor
        moon_x_relative = moon_orbit_radius * np.cos(moon_angle)
        moon_y_relative = moon_orbit_radius * np.sin(moon_angle)
        moon_patch.set_center((earth_x + moon_x_relative, earth_y + moon_y_relative))

        # Update orbit lines (for visualization, not actual paths)
        if show_earth_orbit:
            # Draw a full circle for Earth's orbit
            theta = np.linspace(0, 2*np.pi, 100)
            earth_orbit_x = earth_orbit_radius * np.cos(theta)
            earth_orbit_y = earth_orbit_radius * np.sin(theta)
            earth_orbit_line.set_data(earth_orbit_x, earth_orbit_y)
        else:
            earth_orbit_line.set_data([], [])

        if show_moon_orbit:
            # Draw a full circle for Moon's orbit around Earth
            theta = np.linspace(0, 2*np.pi, 100)
            moon_orbit_x = earth_x + moon_orbit_radius * np.cos(theta)
            moon_orbit_y = earth_y + moon_orbit_radius * np.sin(theta)
            moon_orbit_line.set_data(moon_orbit_x, moon_orbit_y)
        else:
            moon_orbit_line.set_data([], [])

        return earth_patch, moon_patch, earth_orbit_line, moon_orbit_line

    # Create animation
    ani = FuncAnimation(fig, update, frames=range(360), interval=50, blit=True)

    if save_animation:
        print(f"Saving animation to {filename}...")
        writer = FFMpegWriter(fps=20, metadata=dict(artist='Me'), bitrate=1800)
        ani.save(filename, writer=writer)
        print("Animation saved.")
    else:
        plt.show()

if __name__ == "__main__":
    print("Choose an animation mode:")
    print("1. Earth orbiting Sun only")
    print("2. Moon orbiting Earth only (relative to Earth's position)")
    print("3. Full Earth-Moon system orbiting Sun")
    print("4. Save full animation to MP4")
    print("5. Save full animation to GIF")

    choice = input("Enter your choice (1-5): ")

    if choice == '1':
        animate_solar_system(show_earth_orbit=True, show_moon_orbit=False)
    elif choice == '2':
        # For moon orbiting earth only, we need to adjust the view to follow earth
        # This requires a slightly different animation setup or a more complex update function
        # For simplicity, we'll show it as part of the full system but only highlight moon's orbit
        print("Displaying Moon orbiting Earth (relative to Earth's movement around Sun).")
        animate_solar_system(show_earth_orbit=False, show_moon_orbit=True)
    elif choice == '3':
        animate_solar_system(show_earth_orbit=True, show_moon_orbit=True)
    elif choice == '4':
        animate_solar_system(show_earth_orbit=True, show_moon_orbit=True, save_animation=True, filename="solar_system_animation.mp4")
    elif choice == '5':
        animate_solar_system(show_earth_orbit=True, show_moon_orbit=True, save_animation=True, filename="solar_system_animation.gif")
    else:
        print("Invalid choice. Exiting.")
