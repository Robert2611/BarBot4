
from enum import Enum, auto
import colorsys

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider

class LED_Type(Enum):
    WATERFALL = auto(),
    RAINBOW = auto(),
    DRAFT = auto()

selected_LED_Type = LED_Type.DRAFT

PIXEL_COUNT = 60
X = range(PIXEL_COUNT)

# The parametrized function to be plotted
def get_colors(frame, position):
    colors = []
    if selected_LED_Type == LED_Type.WATERFALL:
        platform_position = position
        period = 10
        frame %= period
        for i in X:
            dist = (abs(i - platform_position) + frame) % period
            if dist > (period - 1) / 2:
                dist = period - dist
            brightness = max(1 - dist / 3.0, 0.0)
            colors.append((0, 0, brightness * brightness))

    elif selected_LED_Type == LED_Type.RAINBOW:
        frame %= PIXEL_COUNT
        for i in X:
            pos = (i + frame) % PIXEL_COUNT
            colors.append(colorsys.hsv_to_rgb(float(pos) / (PIXEL_COUNT - 1), 1.0, 0.8))

    elif selected_LED_Type == LED_Type.DRAFT:
        period = 20
        draft_position = position
        frame %= period
        for i in X:
            dist = (abs(i - draft_position) + frame) % period
            if dist > (period - 1) / 2:
                dist = period - dist
            brightness = max(1 - dist / 3.0, 0.0)
            if abs(i - draft_position) <= 2:
                brightness = 0.999
            colors.append((0, brightness * brightness, 0))

    #print([g for r,g,b in colors])
    return colors

# Define initial parameters
init_pos = 0
init_time = 0

# Create the figure and the line that we will manipulate
fig, ax = plt.subplots()
ax.set_facecolor("black")
figure = ax.scatter(X, [0 for _ in X], lw=2)
ax.set_xlabel('Pixels')

# adjust the main plot to make room for the sliders
fig.subplots_adjust(left=0.25, bottom=0.25)

# Make a horizontal slider to control the time.
axfreq = fig.add_axes((0.25, 0.1, 0.65, 0.03))
frame_slider = Slider(
    ax=axfreq,
    label='frame',
    valmin=0,
    valmax=100,
    valstep=1,
    valinit=init_time,
)

# Make a vertically oriented slider to control the position
axamp = fig.add_axes((0.1, 0.25, 0.0225, 0.63))
pos_slider = Slider(
    ax=axamp,
    label="position",
    valmin=0,
    valmax=PIXEL_COUNT-1,
    valstep=1,
    valinit=init_pos,
    orientation="vertical"
)

# The function to be called anytime a slider's value changes
def update(_):
    figure.set_facecolors( get_colors(frame_slider.val, pos_slider.val))
    fig.canvas.draw_idle()


# register the update function with the slider
frame_slider.on_changed(update)
pos_slider.on_changed(update)

# Create a `matplotlib.widgets.Button` to reset the sliders to initial values.
resetax = fig.add_axes((0.8, 0.025, 0.1, 0.04))
button = Button(resetax, 'Reset', hovercolor='0.975')
def reset(_):
    frame_slider.reset()
    pos_slider.reset()
button.on_clicked(reset)

plt.show()
