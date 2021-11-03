import random
import matplotlib.pyplot as plt
import math
import numpy as np

def main():
    B_list = [3900, 3934, 3950, 3971]  # OH: NTCG103UH103JT1, VTRX+: NTCG063UH103HTBX
    T_list = [50, 75, 85, 100]
    R_list = []

    for i in range(len(T_list)):
        T_list[i] = T_list[i] + 273.15

    for B, T in zip(B_list, T_list):
        R = 10e3 * math.exp(-B * ((1 / 298.15) - (1 / T)))
        R_list.append(R)

    T_list = [298.15] + T_list
    R_list = [10000] + R_list

    for i in range(len(T_list)):
        T_list[i] = T_list[i] - 273.15

    #old_fit(T_list, R_list)
    new_fit(T_list, R_list)

def live_plot(ax, x, y):
    ax.plot(x, y, "turquoise")
    plt.draw()
    plt.pause(0.01)

def plot():
    fig = plt.figure()
    ax = fig.add_subplot(111)    # The big subplot
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)

    # Turn off axis lines and ticks of the big subplot
    ax.spines['top'].set_color('none')
    ax.spines['bottom'].set_color('none')
    ax.spines['left'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.tick_params(labelcolor='w', top=False, bottom=False, left=False, right=False)

    # Set common labels
    ax.set_xlabel('common xlabel')
    ax.set_ylabel('common ylabel')

    ax1.set_title('ax1 title')
    ax2.set_title('ax2 title')

    x = range(1, 101)
    y1 = [random.randint(1, 100) for _ in range(len(x))]
    y2 = [random.randint(1, 100) for _ in range(len(x))]

    live_plot(ax1, x, y1)
    live_plot(ax2, x, y2)


    plt.draw()
    plt.pause(10)

def old_fit(T_list, R_list):
    power = 4
    poly_coeffs = np.polyfit(T_list, np.log10(R_list), power)
    y_new = np.poly1d(poly_coeffs)
    x_new = np.linspace(0, 150, 150)

    # Plotting
    plt.plot(T_list, np.log10(R_list), 'o')
    plt.plot(x_new, y_new(x_new))

    res = 80.5
    temp = y_new(res)
    plt.plot(res, temp, 'x')

    plt.draw()
    plt.title("Power: " + str(power))
    plt.savefig("temp_fit_" + str(power))
    plt.pause(4)

def new_fit(T_list, R_list):

    power = 4
    poly_coeffs = np.polyfit(np.log10(R_list), T_list, power)
    y_new = np.poly1d(poly_coeffs)
    x_new = np.linspace(1, 5, 100)

    print("R_list", R_list)
    print("log(R_list)", list(np.log10(R_list)))
    print("T_list", T_list)

    res = 2000
    temp = y_new(np.log10(res))
    print(np.log10(res), temp)

    # Plotting
    plt.plot(np.log10(R_list), T_list, 'o')
    plt.plot(x_new, y_new(x_new))
    plt.plot(np.log10(res), temp, 'x')

    plt.draw()
    plt.title("Power: " + str(power))
    plt.savefig("temp_fit_" + str(power))
    plt.pause(4)


if __name__ == "__main__":
    main()

